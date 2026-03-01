#!/usr/bin/env python3
"""
PreToolUse Hook: Port Guard  (long-task-agent plugin, plugin-level)

Kills any processes occupying relevant ports BEFORE Claude starts a service.
Always exits 0 — never blocks the command; only cleans up first so the
incoming server-start command finds clean ports.

Registered in hooks/hooks.json as a PreToolUse/Bash hook.
Fires automatically for every Bash tool call in every session where the
long-task-agent plugin is installed.

--- PORT DISCOVERY (three layers) ---
Layer 1: .claude/st-config.json          (explicit project declaration)
Layer 2: project files inference          (.env, package.json, application.yml)
Layer 3: psutil / stdlib runtime scan    (all current LISTEN sockets)

--- TRIGGER CONDITIONS ---
Triggers on: uvicorn, gunicorn, flask run, npm run dev/start/serve, node,
             ts-node, vite, next dev/start, java -jar, cargo run, go run,
Excludes:    pytest, jest, mvn test, gradle test, cargo test, go test,
             vitest, mocha, ctest, mutmut, pitest, stryker (unit-test commands)

--- GRACEFUL DEGRADATION ---
When .claude/st-config.json is absent (non-long-task projects), falls back to
Layer 2 (project file inference) and Layer 3 (runtime scan).
When no ports are declared anywhere, cleans all listening ports on trigger.

--- DEPENDENCIES ---
Optional: psutil (pip install psutil) — automatically falls back to stdlib
          (netstat on Windows, ss/lsof on Linux/macOS) if not available.
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Trigger classification
# ---------------------------------------------------------------------------

_SERVER_PATTERNS: list[str] = [
    r"\buvicorn\b",
    r"\bgunicorn\b",
    r"\bflask\b.*\brun\b",
    r"manage\.py\s+runserver",
    r"\bhypercorn\b",
    r"\bdaphne\b",
    r"\bnpm\b.*(run\s+)?(dev|start|serve|preview)\b",
    r"\bnode\b\s+\S+\.(?:js|mjs|cjs)\b",
    r"\bts-node\b",
    r"\bvite\b",
    r"\bnext\b\s+(dev|start)\b",
    r"\bnuxt\b\s+(dev|start)\b",
    r"\bjava\b.*-jar\b",
    r"\bmvn\b.*spring-boot:run",
    r"\bgradle\b.*(bootRun|appRun)\b",
    r"\bcargo\b\s+run\b",
    r"\bgo\b\s+run\b",
]

_EXCLUDE_PATTERNS: list[str] = [
    r"\bpytest\b",
    r"\bunittest\b",
    r"\bjest\b",
    r"\bvitest\b",
    r"\bmocha\b",
    r"\bmvn\b\s+(test|verify)\b",
    r"\bgradle\b\s+(test|check)\b",
    r"\bcargo\b\s+test\b",
    r"\bgo\b\s+test\b",
    r"\bctest\b",
    r"\bnpm\b\s+(run\s+)?test\b",
    r"\bmutmut\b",
    r"\bpitest\b",
    r"\bstryker\b",
    r"\bmull\b",
    # Kill/Terminate commands — don't interfere with user-initiated stops
    r"\bpkill\b",
    r"\btaskkill\b",
    r"\bkill\b",
    r"\bpkill\b",
    r"\bproc Kill\b",
]


def _needs_cleanup(cmd: str) -> bool:
    """Return True iff this command starts a long-running service."""
    for pat in _EXCLUDE_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            return False
    for pat in _SERVER_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Port discovery — Layer 1: st-config.json
# ---------------------------------------------------------------------------

def _config_ports() -> set[int]:
    cfg_path = os.path.join(".claude", "st-config.json")
    if not os.path.isfile(cfg_path):
        return set()
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError):
        return set()

    ports: set[int] = set()
    for p in cfg.get("ports", []):
        if isinstance(p, int) and 1024 <= p <= 65535:
            ports.add(p)
    r = cfg.get("port_range")
    if isinstance(r, list) and len(r) == 2:
        for p in range(int(r[0]), int(r[1]) + 1):
            if 1024 <= p <= 65535:
                ports.add(p)
    return ports


# ---------------------------------------------------------------------------
# Port discovery — Layer 2: project file inference
# ---------------------------------------------------------------------------

def _file_ports() -> set[int]:
    ports: set[int] = set()

    # .env / .env.* files
    for envfile in (".env", ".env.local", ".env.development", ".env.test"):
        if os.path.isfile(envfile):
            try:
                with open(envfile, encoding="utf-8") as f:
                    for line in f:
                        m = re.match(r"[A-Z_]*PORT\s*=\s*(\d+)", line.strip(), re.IGNORECASE)
                        if m:
                            p = int(m.group(1))
                            if 1024 <= p <= 65535:
                                ports.add(p)
            except OSError:
                pass

    # package.json
    if os.path.isfile("package.json"):
        try:
            with open("package.json", encoding="utf-8") as f:
                content = f.read()
            for m in re.finditer(r"(?:--|PORT[=:]\s*|port[=:]\s*|-p\s+)(\d{4,5})", content, re.IGNORECASE):
                p = int(m.group(1))
                if 1024 <= p <= 65535:
                    ports.add(p)
        except OSError:
            pass

    # Spring Boot application.yml / .properties
    for cfg_file in (
        "src/main/resources/application.yml",
        "src/main/resources/application.properties",
        "application.yml",
        "application.properties",
    ):
        if os.path.isfile(cfg_file):
            try:
                with open(cfg_file, encoding="utf-8") as f:
                    for line in f:
                        if re.search(r"(server\.port|port:)", line, re.IGNORECASE):
                            m = re.search(r"(\d{4,5})", line)
                            if m:
                                p = int(m.group(1))
                                if 1024 <= p <= 65535:
                                    ports.add(p)
            except OSError:
                pass

    return ports


# ---------------------------------------------------------------------------
# Port discovery — Layer 3: runtime listening sockets
# ---------------------------------------------------------------------------

def _runtime_ports_psutil() -> dict[int, int]:
    """port → pid mapping via psutil (cross-platform including Windows)."""
    import psutil  # type: ignore

    result: dict[int, int] = {}
    for conn in psutil.net_connections(kind="tcp"):
        if getattr(conn, "status", None) == "LISTEN" and conn.pid and conn.laddr:
            p = conn.laddr.port
            if 1024 <= p <= 65535:
                result[p] = conn.pid
    return result


def _runtime_ports_stdlib() -> dict[int, int]:
    """port → pid mapping via subprocess (fallback when psutil unavailable)."""
    result: dict[int, int] = {}
    try:
        if platform.system() == "Windows":
            out = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=8
            ).stdout
            for line in out.splitlines():
                if "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        addr, pid_str = parts[1], parts[-1]
                        port_str = addr.rsplit(":", 1)[-1]
                        try:
                            p, pid = int(port_str), int(pid_str)
                            if 1024 <= p <= 65535:
                                result[p] = pid
                        except ValueError:
                            pass
        else:
            # Linux / macOS: try ss first, fall back to lsof
            try:
                out = subprocess.run(
                    ["ss", "-tlnp"], capture_output=True, text=True, timeout=5
                ).stdout
                for line in out.splitlines():
                    m = re.search(r":(\d+)\s.*pid=(\d+)", line)
                    if m:
                        p, pid = int(m.group(1)), int(m.group(2))
                        if 1024 <= p <= 65535:
                            result[p] = pid
            except FileNotFoundError:
                out = subprocess.run(
                    ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
                    capture_output=True, text=True, timeout=8
                ).stdout
                for line in out.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 9:
                        addr_field = parts[8]
                        pid_str = parts[1]
                        port_str = addr_field.rsplit(":", 1)[-1]
                        try:
                            p, pid = int(port_str), int(pid_str)
                            if 1024 <= p <= 65535:
                                result[p] = pid
                        except ValueError:
                            pass
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return result


def _get_listening() -> dict[int, int]:
    try:
        import psutil  # noqa: F401
        return _runtime_ports_psutil()
    except ImportError:
        return _runtime_ports_stdlib()


# ---------------------------------------------------------------------------
# Process termination
# ---------------------------------------------------------------------------

def _kill_pid(pid: int) -> bool:
    # Try psutil first (cleanest, cross-platform)
    try:
        import psutil  # type: ignore

        proc = psutil.Process(pid)
        proc.kill()
        return True
    except Exception:
        pass
    # stdlib fallback
    try:
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True, timeout=5
            )
        else:
            os.kill(pid, 9)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
        command: str = data.get("tool_input", {}).get("command", "")
    except (json.JSONDecodeError, AttributeError, TypeError):
        sys.exit(0)

    if not _needs_cleanup(command):
        sys.exit(0)

    # Safety: If no st-config.json exists, skip port cleanup entirely
    # This prevents accidentally killing processes in unknown projects
    cfg_path = os.path.join(".claude", "st-config.json")
    if not os.path.isfile(cfg_path):
        sys.exit(0)

    # Gather target ports
    target_ports = _config_ports() | _file_ports()
    listening = _get_listening()

    # If no ports declared, clean ALL listening ports found (safe on first use)
    if not target_ports:
        target_ports = set(listening.keys())

    # Load exclude list
    exclude_pids: set[int] = set()
    try:
        with open(os.path.join(".claude", "st-config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        exclude_pids = set(cfg.get("exclude_pids", []))
    except (json.JSONDecodeError, OSError):
        pass

    # Kill
    cleaned: list[str] = []
    for port in sorted(target_ports):
        pid = listening.get(port)
        if pid and pid not in exclude_pids:
            if _kill_pid(pid):
                cleaned.append(f"port {port} (PID {pid})")

    if cleaned:
        print(f"[port-guard] Cleaned: {', '.join(cleaned)}", file=sys.stderr)
        time.sleep(0.3)  # Brief pause for OS to release ports

    # Also kill process_patterns from config
    try:
        with open(os.path.join(".claude", "st-config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        for pat in cfg.get("process_patterns", []):
            try:
                import psutil  # type: ignore

                for proc in psutil.process_iter(["name", "cmdline"]):
                    try:
                        cmdline = " ".join(proc.info.get("cmdline") or [])
                        if re.search(pat, cmdline, re.IGNORECASE):
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except ImportError:
                if platform.system() != "Windows":
                    subprocess.run(["pkill", "-9", "-f", pat], capture_output=True)
    except (json.JSONDecodeError, OSError):
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
