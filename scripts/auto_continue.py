"""
Auto-Continue for Long-Task Agent (Windows + Linux)
====================================================
Background process that enables cross-session continuation.
Launched automatically by the session-start hook.

Flow:
  1. Detect Claude Code idle state (no "esc to interrupt")
  2. Check feature-list.json — all passing? → exit
  3. Check iteration count — max reached? → exit
  4. Send "/clear" → wait for completion → send "继续"

Designed to work alongside the Stop hook (hooks/stop) which handles
in-session continuation. This script handles cross-session continuation
when context is exhausted.

Dependencies:
  [Windows] pip install pyautogui pyperclip pywinauto
  [Linux]   sudo apt install xdotool xclip wmctrl  (GUI mode, optional)
            (tmux mode needs no extra dependencies)
"""

import time
import re
import json
import sys
import os
import atexit
import subprocess
import shutil
import argparse
import logging
import platform
import tempfile
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Tuple
from abc import ABC, abstractmethod

PLATFORM = platform.system()


# ─── Singleton PID Guard ──────────────────────────────────────────────────────
def _pid_file_path() -> str:
    return os.path.join(tempfile.gettempdir(), "claude-auto-continue.pid")


def _is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running (cross-platform)."""
    if PLATFORM == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def acquire_singleton() -> bool:
    """Acquire singleton lock. Returns True if this is the only instance."""
    pid_file = _pid_file_path()
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old_pid = int(f.read().strip())
            if _is_process_running(old_pid):
                return False  # Another instance is running
        except (ValueError, IOError):
            pass  # Stale/corrupt PID file, proceed
        try:
            os.unlink(pid_file)
        except OSError:
            pass

    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    def _cleanup():
        try:
            if os.path.exists(pid_file):
                with open(pid_file, "r") as f:
                    if f.read().strip() == str(os.getpid()):
                        os.unlink(pid_file)
        except Exception:
            pass

    atexit.register(_cleanup)
    return True


# ─── State ────────────────────────────────────────────────────────────────────
class State(Enum):
    RUNNING = auto()
    IDLE = auto()
    UNKNOWN = auto()


@dataclass
class DetectionResult:
    state: State
    detail: str = ""
    matched: str = ""


@dataclass
class Config:
    poll_interval: float = 2.0
    continue_text: str = "继续"
    max_retries: int = 3
    idle_confirm_count: int = 2
    cooldown_after_send: float = 10.0
    clear_timeout: float = 15.0
    vscode_title: str = "Visual Studio Code"
    dry_run: bool = False
    log_level: str = "INFO"
    feature_list_path: str = ""
    max_iterations: int = 0          # 0 = unlimited


# ─── Logging ──────────────────────────────────────────────────────────────────
def setup_log(level="INFO"):
    lg = logging.getLogger("auto-continue")
    lg.setLevel(getattr(logging, level, logging.INFO))
    if not lg.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)-5s %(message)s", "%H:%M:%S"))
        lg.addHandler(h)
    return lg


# ═══════════════════════════════════════════════════════════════════════════════
#  State Detection
# ═══════════════════════════════════════════════════════════════════════════════
class Detector:
    RUNNING_PATTERNS = [
        re.compile(r"esc\s+to\s+interrupt", re.IGNORECASE),
        re.compile(r"(?:pause|stop)\s+(?:generation|execution)", re.IGNORECASE),
    ]

    IDLE_PATTERNS = [
        re.compile(r"\bsubmit\b", re.IGNORECASE),
        re.compile(r"What would you like", re.IGNORECASE),
        re.compile(r"Type (?:a |your )?message", re.IGNORECASE),
        re.compile(r"Enter your (?:message|response)", re.IGNORECASE),
        re.compile(r"How can I help", re.IGNORECASE),
    ]

    @classmethod
    def detect(cls, text: str) -> DetectionResult:
        tail = text[-2000:] if len(text) > 2000 else text

        for p in cls.RUNNING_PATTERNS:
            m = p.search(tail)
            if m:
                return DetectionResult(State.RUNNING, p.pattern[:50], m.group())

        for p in cls.IDLE_PATTERNS:
            m = p.search(tail)
            if m:
                return DetectionResult(State.IDLE, p.pattern[:50], m.group())

        if not any(p.search(tail) for p in cls.RUNNING_PATTERNS):
            return DetectionResult(State.IDLE, "no running indicator found")

        return DetectionResult(State.UNKNOWN)


# ═══════════════════════════════════════════════════════════════════════════════
#  Platform Backends (from v3)
# ═══════════════════════════════════════════════════════════════════════════════
class Backend(ABC):
    @abstractmethod
    def find_windows(self, pattern: str) -> List[dict]: ...
    @abstractmethod
    def read_text(self, win_id) -> str: ...
    @abstractmethod
    def send_text(self, win_id, text: str) -> bool: ...


class WinBackend(Backend):
    def __init__(self):
        import ctypes
        self.user32 = ctypes.windll.user32
        self.log = logging.getLogger("auto-continue")
        self._uia = None
        try:
            from pywinauto import Desktop
            self._uia = Desktop(backend="uia")
        except Exception:
            pass

    def find_windows(self, pattern):
        import ctypes
        from ctypes import wintypes
        res = []
        cb_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, _):
            if self.user32.IsWindowVisible(hwnd):
                n = self.user32.GetWindowTextLengthW(hwnd)
                if n:
                    buf = ctypes.create_unicode_buffer(n + 1)
                    self.user32.GetWindowTextW(hwnd, buf, n + 1)
                    t = buf.value
                    if pattern in t or "Code" in t:
                        res.append({"id": hwnd, "title": t})
            return True
        self.user32.EnumWindows(cb_type(cb), 0)
        return res

    def _bring(self, wid):
        if self.user32.IsIconic(wid):
            self.user32.ShowWindow(wid, 9)
        self.user32.SetForegroundWindow(wid)
        time.sleep(0.3)

    def read_text(self, wid) -> str:
        if self._uia:
            try:
                parts = []
                for w in self._uia.windows(title_re=r".*Code.*")[:1]:
                    for e in w.descendants():
                        try:
                            t = e.window_text()
                            if t and t.strip():
                                parts.append(t.strip())
                        except Exception:
                            continue
                if parts:
                    return "\n".join(parts)
            except Exception:
                pass
        return self._clipboard_read(wid)

    def _clipboard_read(self, wid) -> str:
        try:
            import pyautogui, pyperclip
            old = pyperclip.paste() or ""
            self._bring(wid)
            pyautogui.hotkey('ctrl', 'shift', 'end'); time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'shift', 'c'); time.sleep(0.3)
            txt = pyperclip.paste() or ""
            pyautogui.press('escape')
            try: pyperclip.copy(old)
            except: pass
            return txt
        except Exception:
            return ""

    def send_text(self, wid, text) -> bool:
        try:
            import pyautogui, pyperclip
            self._bring(wid)
            old = ""
            try: old = pyperclip.paste()
            except: pass
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v'); time.sleep(0.2)
            pyautogui.press('enter')
            try:
                if old: pyperclip.copy(old)
            except: pass
            return True
        except Exception as e:
            self.log.warning(f"Send failed: {e}")
            return False


class LinuxBackend(Backend):
    def __init__(self):
        self.log = logging.getLogger("auto-continue")
        self._tmux = os.environ.get("TMUX")
        self._screen = os.environ.get("STY")
        self._display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        self._xdotool = shutil.which("xdotool")
        self._wmctrl = shutil.which("wmctrl")
        self._xclip = shutil.which("xclip")

        if self._tmux:
            self.log.info("[Linux] tmux mode")
        elif self._screen:
            self.log.info("[Linux] screen mode")
        elif self._display:
            self.log.info(f"[Linux] GUI mode DISPLAY={self._display}")
        else:
            self.log.info("[Linux] bare terminal mode")

    def _run(self, cmd, timeout=5) -> Optional[str]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip() if r.returncode == 0 else None
        except Exception:
            return None

    def find_windows(self, pattern) -> List[dict]:
        if self._tmux:
            return [{"id": "__tmux__", "title": "tmux"}]
        if self._screen:
            return [{"id": "__screen__", "title": "screen"}]

        if self._display and self._wmctrl:
            out = self._run(["wmctrl", "-l"])
            if out:
                res = []
                for line in out.splitlines():
                    parts = line.split(None, 3)
                    if len(parts) >= 4 and (pattern in parts[3] or "Code" in parts[3]):
                        res.append({"id": parts[0], "title": parts[3]})
                if res:
                    return res

        if self._display and self._xdotool:
            out = self._run(["xdotool", "search", "--name", pattern])
            if out:
                res = []
                for wid in out.splitlines()[:3]:
                    t = self._run(["xdotool", "getwindowname", wid]) or ""
                    res.append({"id": wid, "title": t})
                if res:
                    return res

        return [{"id": "__self__", "title": "current"}]

    def read_text(self, wid) -> str:
        if wid == "__tmux__" or self._tmux:
            out = self._run(["tmux", "capture-pane", "-p", "-S", "-100"])
            return out or ""

        if wid == "__screen__" or self._screen:
            tmp = "/tmp/_cc_screen.txt"
            self._run(["screen", "-X", "hardcopy", tmp])
            try:
                with open(tmp, "r", errors="replace") as f:
                    return f.read()
            except Exception:
                return ""

        if self._display and self._xdotool and self._xclip:
            try:
                if self._wmctrl:
                    self._run(["wmctrl", "-i", "-a", str(wid)])
                else:
                    self._run(["xdotool", "windowactivate", str(wid)])
                time.sleep(0.2)
                self._run(["xdotool", "key", "--window", str(wid), "ctrl+shift+End"])
                time.sleep(0.1)
                self._run(["xdotool", "key", "--window", str(wid), "ctrl+shift+c"])
                time.sleep(0.3)
                txt = self._run(["xclip", "-selection", "clipboard", "-o"]) or ""
                self._run(["xdotool", "key", "--window", str(wid), "Escape"])
                return txt
            except Exception:
                return ""

        return ""

    def send_text(self, wid, text) -> bool:
        if wid == "__tmux__" or self._tmux:
            return self._run(["tmux", "send-keys", text, "Enter"]) is not None

        if wid == "__screen__" or self._screen:
            return self._run(["screen", "-X", "stuff", f"{text}\n"]) is not None

        if self._display and self._xdotool:
            try:
                if self._wmctrl:
                    self._run(["wmctrl", "-i", "-a", str(wid)])
                else:
                    self._run(["xdotool", "windowactivate", str(wid)])
                time.sleep(0.2)
                if self._xclip:
                    p = subprocess.Popen(["xclip", "-selection", "clipboard"],
                                         stdin=subprocess.PIPE)
                    p.communicate(text.encode("utf-8"))
                    self._run(["xdotool", "key", "--window", str(wid), "ctrl+v"])
                else:
                    self._run(["xdotool", "type", "--clearmodifiers", "--window",
                               str(wid), text])
                time.sleep(0.2)
                self._run(["xdotool", "key", "--window", str(wid), "Return"])
                return True
            except Exception:
                return False

        self.log.warning("Cannot auto-send, please input manually")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  Feature Completion Detection
# ═══════════════════════════════════════════════════════════════════════════════
def check_features(feature_list_path: str) -> Tuple[bool, str]:
    """
    Check if all active (non-deprecated) features are passing.
    Returns (all_passing, summary_string).
    """
    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return False, "feature-list.json not found"
    except json.JSONDecodeError as e:
        return False, f"feature-list.json parse error: {e}"

    features = data.get("features", [])
    active = [f for f in features if not f.get("deprecated", False)]
    if not active:
        return False, "no active features"

    passing = sum(1 for f in active if f.get("status") == "passing")
    total = len(active)
    all_passing = (passing == total)
    return all_passing, f"{passing}/{total} active features passing"


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Controller
# ═══════════════════════════════════════════════════════════════════════════════
class Watcher:
    def __init__(self, cfg: Config = None):
        self.cfg = cfg or Config()
        self.log = setup_log(self.cfg.log_level)
        self.backend: Backend = WinBackend() if PLATFORM == "Windows" else LinuxBackend()
        self.idle_count = 0
        self.total = 0
        self._on = False

        # Resolve feature_list_path to absolute at startup
        if self.cfg.feature_list_path:
            self.cfg.feature_list_path = os.path.abspath(self.cfg.feature_list_path)

    def _detect(self, wid) -> DetectionResult:
        txt = self.backend.read_text(wid)
        if not txt:
            return DetectionResult(State.UNKNOWN, "no text")
        return Detector.detect(txt)

    def _send_with_retry(self, wid, text: str) -> bool:
        for i in range(self.cfg.max_retries):
            if self.backend.send_text(wid, text):
                return True
            self.log.warning(f"Retry {i+1}/{self.cfg.max_retries} for '{text}'")
            time.sleep(1)
        return False

    def _wait_for_clear_completion(self, wid, timeout: float = 15.0) -> bool:
        """Wait for /clear to complete by detecting idle state return."""
        start = time.time()
        time.sleep(1.0)  # Initial delay for /clear to begin
        while time.time() - start < timeout:
            txt = self.backend.read_text(wid)
            if txt:
                result = Detector.detect(txt)
                if result.state == State.IDLE:
                    return True
            time.sleep(1.0)
        self.log.warning("Clear completion timeout — proceeding anyway")
        return False

    def _on_idle(self, wid):
        self.idle_count += 1
        self.log.info(f"Idle ({self.idle_count}/{self.cfg.idle_confirm_count})")
        if self.idle_count < self.cfg.idle_confirm_count:
            return

        # Gate 1: Feature completion check
        if self.cfg.feature_list_path:
            all_passing, summary = check_features(self.cfg.feature_list_path)
            self.log.info(f"Features: {summary}")
            if all_passing:
                self.log.info("All active features passing. Stopping auto-continue.")
                self.stop()
                return

        # Gate 2: Max iterations
        if self.cfg.max_iterations > 0 and self.total >= self.cfg.max_iterations:
            self.log.info(f"Max iterations ({self.cfg.max_iterations}) reached. Stopping.")
            self.stop()
            return

        if self.cfg.dry_run:
            self.log.info(f"[DRY RUN] Would send: /clear then '{self.cfg.continue_text}'")
            self.total += 1
        else:
            # Step 1: Send /clear
            self.log.info("Sending /clear ...")
            ok_clear = self._send_with_retry(wid, "/clear")
            if not ok_clear:
                self.log.warning("Failed to send /clear — skipping this cycle")
                self.idle_count = 0
                return

            # Step 2: Wait for clear completion (SessionStart hook runs)
            self.log.info(f"Waiting for /clear completion (up to {self.cfg.clear_timeout}s) ...")
            self._wait_for_clear_completion(wid, timeout=self.cfg.clear_timeout)

            # Step 3: Settle delay
            time.sleep(2.0)

            # Step 4: Send continue text
            self.log.info(f"Sending '{self.cfg.continue_text}' ...")
            ok_continue = self._send_with_retry(wid, self.cfg.continue_text)
            self.total += 1
            status = "OK" if ok_continue else "FAILED"
            self.log.info(f"Cycle #{self.total} {status}")

        self.idle_count = 0
        self.log.info(f"Cooldown {self.cfg.cooldown_after_send}s")
        time.sleep(self.cfg.cooldown_after_send)

    def run(self):
        self._on = True
        self.log.info("=" * 55)
        self.log.info("  Long-Task Auto-Continue (integrated)")
        self.log.info(f"  platform={PLATFORM}  interval={self.cfg.poll_interval}s  confirm={self.cfg.idle_confirm_count}")
        self.log.info(f"  text='{self.cfg.continue_text}'  dry_run={self.cfg.dry_run}")
        if self.cfg.feature_list_path:
            self.log.info(f"  feature_list={self.cfg.feature_list_path}")
        if self.cfg.max_iterations > 0:
            self.log.info(f"  max_iterations={self.cfg.max_iterations}")
        self.log.info("  Ctrl+C to stop")
        self.log.info("=" * 55)

        try:
            while self._on:
                wins = self.backend.find_windows(self.cfg.vscode_title)
                if not wins:
                    self.idle_count = 0
                    time.sleep(self.cfg.poll_interval)
                    continue

                w = wins[0]
                r = self._detect(w["id"])
                self.log.debug(f"[{r.state.name}] {r.detail}  matched={r.matched}")

                if r.state == State.RUNNING:
                    self.idle_count = 0
                    self.log.debug("Running...")
                elif r.state == State.IDLE:
                    self._on_idle(w["id"])
                else:
                    self.idle_count = 0

                time.sleep(self.cfg.poll_interval)
        except KeyboardInterrupt:
            self.log.info("\nInterrupted")
        finally:
            self._on = False
            self.log.info(f"Total cycles: {self.total}")

    def stop(self):
        self._on = False


# ─── API ──────────────────────────────────────────────────────────────────────
def start_watching(**kw):
    Watcher(Config(**kw)).run()


def check_once(**kw) -> DetectionResult:
    cfg = Config(**kw)
    w = Watcher(cfg)
    wins = w.backend.find_windows(cfg.vscode_title)
    if not wins:
        return DetectionResult(State.UNKNOWN, "no window found")
    return w._detect(wins[0]["id"])


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="Long-Task Auto-Continue (integrated with hooks)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Normally launched automatically by the session-start hook.
Can also be run manually:

  %(prog)s --feature-list ./feature-list.json --max-iterations 50
  %(prog)s --dry-run --log-level DEBUG
  %(prog)s --check-once
        """
    )
    p.add_argument("--feature-list", default="",
                   help="Path to feature-list.json for completion detection")
    p.add_argument("--max-iterations", type=int, default=0,
                   help="Max continue cycles (0=unlimited)")
    p.add_argument("--clear-timeout", type=float, default=15.0,
                   help="Seconds to wait for /clear completion")
    p.add_argument("--interval", type=float, default=2.0,
                   help="Poll interval in seconds")
    p.add_argument("--text", default="继续",
                   help="Continue text to send")
    p.add_argument("--confirm", type=int, default=2,
                   help="Consecutive idle polls before sending")
    p.add_argument("--cooldown", type=float, default=10.0,
                   help="Cooldown after send in seconds")
    p.add_argument("--retries", type=int, default=3,
                   help="Max retries per send")
    p.add_argument("--dry-run", action="store_true",
                   help="Detect only, do not send")
    p.add_argument("--check-once", action="store_true",
                   help="Check state once and exit")
    p.add_argument("--log-level", default="INFO",
                   choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    a = p.parse_args()

    if a.check_once:
        log = setup_log(a.log_level)
        # Also check features if path given
        if a.feature_list:
            all_ok, summary = check_features(a.feature_list)
            print(f"Features: {summary}")
            if all_ok:
                print("All features passing — auto-continue would exit.")
                sys.exit(0)

        r = check_once(log_level=a.log_level)
        state_str = {State.RUNNING: "RUNNING", State.IDLE: "IDLE", State.UNKNOWN: "UNKNOWN"}
        print(f"State: {state_str.get(r.state, '?')}")
        print(f"Detail: {r.detail}")
        if r.matched:
            print(f"Matched: {r.matched}")
        sys.exit(0 if r.state == State.IDLE else 1)

    # Singleton guard
    if not acquire_singleton():
        print("Another auto-continue instance is already running. Exiting.", file=sys.stderr)
        sys.exit(0)

    Watcher(Config(
        poll_interval=a.interval, continue_text=a.text,
        max_retries=a.retries, idle_confirm_count=a.confirm,
        cooldown_after_send=a.cooldown, clear_timeout=a.clear_timeout,
        dry_run=a.dry_run, log_level=a.log_level,
        feature_list_path=a.feature_list, max_iterations=a.max_iterations,
    )).run()


if __name__ == "__main__":
    main()
