#!/usr/bin/env python3
"""
Validate LLM-generated ST runtime scripts for structural completeness.

Checks that st-start.sh/st-start.ps1 and st-clear.sh/st-clear.ps1 contain all required
operational patterns: proxy detection, build steps, health checks, PID management,
retry logic, and graceful failure handling.

Does NOT check functional correctness — only that required patterns are present.

Usage:
    python validate_st_scripts.py <st-start-script> <st-clear-script>
    python validate_st_scripts.py <st-start-script> <st-clear-script> --powershell <st-start.ps1> <st-clear.ps1>

Exit codes:
    0 — all required patterns present
    1 — one or more required patterns missing
"""

import argparse
import re
import sys


# --- Start script checks ---
# Each is (label, list of alternative regex patterns).
# Passes if at least ONE pattern from each group is found (case-insensitive).
START_CHECKS = [
    ("Proxy detection",
     [r"HTTP_PROXY", r"HTTPS_PROXY", r"http_proxy", r"https_proxy"]),
    ("NO_PROXY localhost entries",
     [r"localhost", r"127\.0\.0\.1"]),
    ("Build/compile step or explicit skip",
     [r"npm run build", r"npx tsc", r"tsc\b", r"mvnw.*package", r"gradlew.*build",
      r"cmake\s*--build", r"\bmake\b", r"go build", r"cargo build",
      r"pip install\s+-e", r"npm run dev",
      r"no.?build.?needed", r"no.?compile", r"interpreted",
      r"docker compose.*--build", r"docker.*build"]),
    ("Health check mechanism",
     [r"wait_for_port", r"wait_for_http", r"health.?check",
      r"curl\s+(-s\s+)?.*localhost", r"nc\s+-z", r"Test-NetConnection",
      r"Invoke-WebRequest.*localhost", r"wget.*localhost"]),
    ("PID file management",
     [r"\.pid", r"\$!", r"Start-Process.*-PassThru", r"\$Process\.Id"]),
    ("Retry / error handling",
     [r"retry", r"attempt", r"max_attempts", r"start_with_retry",
      r"try.*again", r"retries"]),
    ("Graceful failure handling",
     [r"record_startup_failure", r"STARTUP FAILED", r"start.*manually",
      r"manual.*start", r"failed.*after.*attempt",
      r"task-progress\.md"]),
]

# Anti-pattern: naive sleep without health check
NAIVE_SLEEP_PATTERN = r"sleep\s+\d+"
HEALTH_CHECK_PATTERN = r"wait_for_port|wait_for_http|health.?check|curl.*localhost|nc\s+-z|Test-NetConnection|Invoke-WebRequest.*localhost"

# --- Cleanup script checks ---
CLEANUP_CHECKS = [
    ("Process termination",
     [r"\bkill\b", r"Stop-Process", r"docker compose down", r"docker-compose down",
      r"taskkill", r"SIGTERM", r"SIGKILL"]),
    ("PID file cleanup",
     [r"rm.*\.pid", r"Remove-Item.*\.pid", r"del.*\.pid", r"clean.*pid"]),
]

# --- Minimal script detection ---
MINIMAL_PATTERN = r"no.?services?.?to.?start|no.?runtime.?services|cli.?only|library.?only|no.?server"


def validate_start_script(path: str) -> list[str]:
    """Validate a start script for required patterns. Returns list of errors."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"Start script not found: {path}"]
    except Exception as e:
        return [f"Cannot read start script: {e}"]

    if not content.strip():
        return [f"Start script is empty: {path}"]

    # Check for minimal/CLI-only script — skip all checks
    if re.search(MINIMAL_PATTERN, content, re.IGNORECASE):
        return []

    for label, patterns in START_CHECKS:
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        if not found:
            errors.append(f"Start script missing: {label}")

    # Anti-pattern check: sleep without health check
    has_sleep = re.search(NAIVE_SLEEP_PATTERN, content)
    has_health = re.search(HEALTH_CHECK_PATTERN, content, re.IGNORECASE)
    if has_sleep and not has_health:
        errors.append("Start script uses naive sleep without health check — use wait_for_port/wait_for_http instead")

    return errors


def validate_cleanup_script(path: str, start_content: str = None) -> list[str]:
    """Validate a cleanup script for required patterns. Returns list of errors."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"Cleanup script not found: {path}"]
    except Exception as e:
        return [f"Cannot read cleanup script: {e}"]

    if not content.strip():
        return [f"Cleanup script is empty: {path}"]

    # Check for minimal/CLI-only script — skip all checks
    if re.search(MINIMAL_PATTERN, content, re.IGNORECASE):
        return []

    for label, patterns in CLEANUP_CHECKS:
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        if not found:
            errors.append(f"Cleanup script missing: {label}")

    # Sanity check: cleanup should not be identical to start
    if start_content and content.strip() == start_content.strip():
        errors.append("Cleanup script is identical to start script")

    return errors


def read_file_content(path: str) -> str | None:
    """Read file content, return None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Validate LLM-generated start/cleanup scripts"
    )
    parser.add_argument("start_script", help="Path to start.sh or start.ps1")
    parser.add_argument("cleanup_script", help="Path to cleanup.sh or cleanup.ps1")
    parser.add_argument(
        "--powershell", nargs=2, metavar=("START_PS1", "CLEANUP_PS1"),
        help="Additionally validate PowerShell variants"
    )
    args = parser.parse_args()

    all_errors = []

    # Validate bash/main scripts
    start_errors = validate_start_script(args.start_script)
    all_errors.extend(start_errors)

    start_content = read_file_content(args.start_script)
    cleanup_errors = validate_cleanup_script(args.cleanup_script, start_content)
    all_errors.extend(cleanup_errors)

    # Validate PowerShell variants if provided
    if args.powershell:
        ps_start, ps_cleanup = args.powershell
        ps_start_errors = validate_start_script(ps_start)
        all_errors.extend([f"(PowerShell) {e}" for e in ps_start_errors])

        ps_start_content = read_file_content(ps_start)
        ps_cleanup_errors = validate_cleanup_script(ps_cleanup, ps_start_content)
        all_errors.extend([f"(PowerShell) {e}" for e in ps_cleanup_errors])

    # Report
    total_checks = len(START_CHECKS) + len(CLEANUP_CHECKS) + 1  # +1 for naive sleep
    if args.powershell:
        total_checks *= 2

    if all_errors:
        print(f"VALIDATION FAILED — {len(all_errors)} issue(s):\n")
        for e in all_errors:
            print(f"  - {e}")
        print(f"\nTotal checks: {total_checks}")
        print(f"Issues: {len(all_errors)}")
        sys.exit(1)
    else:
        print(f"VALID — all {total_checks} checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
