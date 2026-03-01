#!/usr/bin/env python3
"""
Unit tests for validate_st_scripts.py
"""

import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_st_scripts.py")


def write_temp(content, suffix=".sh"):
    """Write content to a temp file, return path. Caller must unlink."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.flush()
    f.close()
    return f.name


def run_validator(start_content, cleanup_content, ps_start=None, ps_cleanup=None):
    """Run validate_start_cleanup.py with temp files. Returns (exit_code, stdout, stderr)."""
    start_path = write_temp(start_content, ".sh")
    cleanup_path = write_temp(cleanup_content, ".sh")
    ps_start_path = write_temp(ps_start, ".ps1") if ps_start else None
    ps_cleanup_path = write_temp(ps_cleanup, ".ps1") if ps_cleanup else None

    try:
        cmd = [sys.executable, SCRIPT_PATH, start_path, cleanup_path]
        if ps_start_path and ps_cleanup_path:
            cmd.extend(["--powershell", ps_start_path, ps_cleanup_path])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(start_path)
        os.unlink(cleanup_path)
        if ps_start_path:
            os.unlink(ps_start_path)
        if ps_cleanup_path:
            os.unlink(ps_cleanup_path)


# --- Complete valid scripts ---

VALID_START = """#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/.run"
mkdir -p "$LOG_DIR"

echo "=== MyProject Service Startup ==="

# --- Proxy Detection and Configuration ---
HTTP_PROXY="${HTTP_PROXY:-${http_proxy:-}}"
HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy:-}}"
NO_PROXY="${NO_PROXY:-${no_proxy:-}}"

if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then
    LOCALHOST_ENTRIES="localhost,127.0.0.1,::1,0.0.0.0"
    if [ -n "$NO_PROXY" ]; then
        NO_PROXY="${NO_PROXY},${LOCALHOST_ENTRIES}"
    else
        NO_PROXY="$LOCALHOST_ENTRIES"
    fi
    export HTTP_PROXY HTTPS_PROXY NO_PROXY
    export http_proxy="$HTTP_PROXY" https_proxy="$HTTPS_PROXY" no_proxy="$NO_PROXY"
    echo "Proxy detected: HTTP_PROXY=${HTTP_PROXY}"
fi

# --- Build ---
echo "Building project..."
npm run build
if [ $? -ne 0 ]; then
    record_startup_failure "Build"
    exit 1
fi

# --- Health Check Utilities ---
wait_for_port() {
    local host="$1" port="$2" name="$3" timeout="${4:-60}"
    local elapsed=0
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ "$elapsed" -ge "$timeout" ]; then
            echo "ERROR: $name did not become ready on $host:$port"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    echo "$name ready"
}

wait_for_http() {
    local url="$1" name="$2" timeout="${3:-60}"
    local elapsed=0
    while ! curl -sf "$url" > /dev/null 2>&1; do
        if [ "$elapsed" -ge "$timeout" ]; then
            echo "ERROR: $name health check failed at $url"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    echo "$name healthy"
}

check_port_free() {
    local port="$1" name="$2"
    if nc -z localhost "$port" 2>/dev/null; then
        echo "WARNING: Port $port (for $name) already in use"
        return 1
    fi
}

# --- Retry Logic ---
start_with_retry() {
    local name="$1" max_attempts="${2:-3}" attempt=1
    shift 2
    while [ "$attempt" -le "$max_attempts" ]; do
        echo "Starting $name (attempt $attempt/$max_attempts)..."
        if "$@"; then
            return 0
        fi
        attempt=$((attempt + 1))
    done
    echo "ERROR: $name failed after $max_attempts attempts"
    return 1
}

record_startup_failure() {
    local component="$1"
    echo "=== STARTUP FAILED: $component ==="
    echo "Please start $component manually and re-run start.sh"
    if [ -f "task-progress.md" ]; then
        printf "\\n### Startup Failure\\n- Component: %s\\n" "$component" >> task-progress.md
    fi
}

# --- Step 1: Database ---
check_port_free 5432 "PostgreSQL"
docker compose up -d postgres
wait_for_port localhost 5432 "PostgreSQL" 30

# --- Step 2: Backend ---
check_port_free 8000 "Backend"
source .venv/bin/activate
uvicorn src.main:app --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
write_pid "$LOG_DIR/backend.pid" $!
wait_for_http "http://localhost:8000/health" "Backend" 30

# --- Step 3: Frontend ---
check_port_free 5173 "Frontend"
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
write_pid "$LOG_DIR/frontend.pid" $!
wait_for_http "http://localhost:5173" "Frontend" 60

echo "=== Services Ready ==="
"""

VALID_CLEANUP = """#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/.run"

echo "=== MyProject Service Cleanup ==="

stop_from_pid() {
    local pid_file="$1" name="$2"
    if [ ! -f "$pid_file" ]; then
        echo "$name: no PID file found"
        return 0
    fi
    local pid
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Stopping $name (PID $pid)..."
        kill "$pid"
        local wait=0
        while kill -0 "$pid" 2>/dev/null && [ "$wait" -lt 10 ]; do
            sleep 1; wait=$((wait + 1))
        done
        if kill -0 "$pid" 2>/dev/null; then
            echo "Force-killing $name (PID $pid)..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    else
        echo "$name (PID $pid) not running — stale PID."
    fi
    rm -f "$pid_file"
}

# --- Step 1: Stop frontend ---
stop_from_pid "$LOG_DIR/frontend.pid" "Frontend"

# --- Step 2: Stop backend ---
stop_from_pid "$LOG_DIR/backend.pid" "Backend"

# --- Step 3: Stop database ---
docker compose down

# --- Step 4: Clean PID files ---
rm -f "$LOG_DIR"/*.pid
rm -f "$LOG_DIR"/*.log

echo "=== Cleanup Complete ==="
"""


# --- Tests ---

def test_valid_scripts_pass():
    """Complete start and cleanup scripts should pass validation."""
    code, stdout, _ = run_validator(VALID_START, VALID_CLEANUP)
    assert code == 0, f"Expected exit 0 for valid scripts: {stdout}"
    assert "VALID" in stdout


def test_empty_start_fails():
    """An empty start script should fail."""
    code, stdout, _ = run_validator("", VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for empty start script: {stdout}"
    assert "empty" in stdout.lower()


def test_empty_cleanup_fails():
    """An empty cleanup script should fail."""
    code, stdout, _ = run_validator(VALID_START, "")
    assert code != 0, f"Expected non-zero for empty cleanup: {stdout}"
    assert "empty" in stdout.lower()


def test_missing_proxy_detection_fails():
    """Start script without proxy detection should fail."""
    start = VALID_START.replace("HTTP_PROXY", "XTTP_PROXY")
    start = start.replace("HTTPS_PROXY", "XTTPS_PROXY")
    start = start.replace("http_proxy", "xttp_proxy")
    start = start.replace("https_proxy", "xttps_proxy")
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for missing proxy: {stdout}"
    assert "Proxy detection" in stdout


def test_missing_health_check_fails():
    """Start script without health checks should fail."""
    start = VALID_START.replace("wait_for_port", "check_service")
    start = start.replace("wait_for_http", "check_endpoint")
    start = start.replace("health_check", "service_check")
    start = start.replace("Health Check", "Service Check")
    start = start.replace("health check", "service check")
    start = start.replace("healthy", "ok")
    start = start.replace("curl", "fetch_tool")
    start = start.replace("nc -z", "network_check")
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for missing health check: {stdout}"
    assert "Health check" in stdout


def test_missing_pid_management_fails():
    """Start script without PID management should fail."""
    start = VALID_START.replace(".pid", ".process")
    start = start.replace("$!", "$LAST")
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for missing PID management: {stdout}"
    assert "PID" in stdout


def test_missing_retry_logic_fails():
    """Start script without retry logic should fail."""
    start = VALID_START.replace("start_with_retry", "start_once")
    start = start.replace("max_attempts", "max_runs")
    start = start.replace("retry", "redo")
    start = start.replace("Retry", "Redo")
    start = start.replace("attempt", "run_num")
    start = start.replace("retries", "redos")
    start = start.replace("try again", "redo it")
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for missing retry: {stdout}"
    assert "Retry" in stdout


def test_missing_graceful_failure_fails():
    """Start script without graceful failure handling should fail."""
    start = VALID_START.replace("record_startup_failure", "log_error")
    start = start.replace("STARTUP FAILED", "ERROR OCCURRED")
    start = start.replace("Please start $component manually", "Check $component logs")
    start = start.replace("start manually", "check logs")
    start = start.replace("Start manually", "Check logs")
    start = start.replace("manual start", "check system")
    start = start.replace("failed after", "errored after")
    start = start.replace("Failed after", "Errored after")
    start = start.replace("task-progress.md", "error-log.txt")
    start = start.replace("Startup Failure", "Error Event")
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for missing graceful failure: {stdout}"
    assert "Graceful failure" in stdout


def test_missing_build_step_fails():
    """Start script without build/compile step should fail."""
    start = VALID_START.replace("npm run build", "npm run lint")
    start = start.replace("npm run dev", "npm run serve_static")
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for missing build step: {stdout}"
    assert "Build" in stdout


def test_no_build_needed_comment_passes():
    """Start script with 'No build needed' comment should pass the build check."""
    start = VALID_START.replace("npm run build", "# No build needed — Python is interpreted")
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code == 0, f"Expected exit 0 for 'no build needed' comment: {stdout}"


def test_naive_sleep_without_health_check_fails():
    """Start script using only sleep (no health check) should fail."""
    start = """#!/usr/bin/env bash
set -euo pipefail
HTTP_PROXY="${HTTP_PROXY:-}"
NO_PROXY="localhost,127.0.0.1"
npm run build
echo "Starting server..."
npm start &
echo $! > .run/server.pid
sleep 5
echo "Server should be ready now"
start_with_retry() { attempt=1; max_attempts=3; "$@"; }
record_startup_failure() { echo "STARTUP FAILED: $1"; echo "Please start $1 manually"; }
"""
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for naive sleep: {stdout}"
    assert "naive sleep" in stdout.lower() or "health check" in stdout.lower()


def test_cleanup_missing_process_termination_fails():
    """Cleanup script without kill/Stop-Process should fail."""
    cleanup = VALID_CLEANUP.replace("kill", "end_proc")
    cleanup = cleanup.replace("docker compose down", "docker compose status")
    code, stdout, _ = run_validator(VALID_START, cleanup)
    assert code != 0, f"Expected non-zero for missing process termination: {stdout}"
    assert "Process termination" in stdout


def test_cleanup_missing_pid_cleanup_fails():
    """Cleanup script without PID file cleanup should fail."""
    cleanup = VALID_CLEANUP.replace("rm -f", "list")
    cleanup = cleanup.replace("Remove-Item", "Get-Item")
    cleanup = cleanup.replace(".pid", ".process")
    cleanup = cleanup.replace("PID", "PROC")
    cleanup = cleanup.replace("pid", "proc")
    code, stdout, _ = run_validator(VALID_START, cleanup)
    assert code != 0, f"Expected non-zero for missing PID cleanup: {stdout}"
    assert "PID file cleanup" in stdout


def test_cleanup_identical_to_start_fails():
    """Cleanup script identical to start should fail."""
    code, stdout, _ = run_validator(VALID_START, VALID_START)
    assert code != 0, f"Expected non-zero for identical scripts: {stdout}"
    assert "identical" in stdout.lower()


def test_minimal_cli_project_passes():
    """Minimal scripts for CLI/library projects should pass."""
    minimal_start = """#!/usr/bin/env bash
echo "No services to start — CLI-only project"
exit 0
"""
    minimal_cleanup = """#!/usr/bin/env bash
echo "No services to start — CLI-only project"
exit 0
"""
    code, stdout, _ = run_validator(minimal_start, minimal_cleanup)
    assert code == 0, f"Expected exit 0 for minimal scripts: {stdout}"


def test_nonexistent_start_file():
    """Validating a nonexistent start file should fail."""
    cleanup_path = write_temp(VALID_CLEANUP, ".sh")
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, "/nonexistent/start.sh", cleanup_path],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "not found" in result.stdout.lower()
    finally:
        os.unlink(cleanup_path)


def test_nonexistent_cleanup_file():
    """Validating a nonexistent cleanup file should fail."""
    start_path = write_temp(VALID_START, ".sh")
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, start_path, "/nonexistent/cleanup.sh"],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "not found" in result.stdout.lower()
    finally:
        os.unlink(start_path)


def test_powershell_valid_scripts_pass():
    """Valid PowerShell scripts should pass with --powershell flag."""
    ps_start = """
$ErrorActionPreference = "Stop"
$HttpProxy = $env:HTTP_PROXY
$NoProxy = "localhost,127.0.0.1"

# Build
npm run build

# Health check
function Wait-ForPort { param($Host, $Port, $Name, $Timeout=60)
    $elapsed = 0
    while (-not (Test-NetConnection -ComputerName $Host -Port $Port -InformationLevel Quiet)) {
        if ($elapsed -ge $Timeout) { throw "$Name not ready" }
        Start-Sleep 2; $elapsed += 2
    }
}

# Start with retry
$maxAttempts = 3; $attempt = 1
$proc = Start-Process -PassThru -NoNewWindow node -ArgumentList "server.js"
$proc.Id | Out-File ".run/server.pid"
Wait-ForPort -Host localhost -Port 3000 -Name "Server"

function Record-StartupFailure($component) {
    Write-Host "=== STARTUP FAILED: $component ==="
    Write-Host "Please start $component manually"
}
"""
    ps_cleanup = """
$ErrorActionPreference = "Stop"

# Stop server
$pidFile = ".run/server.pid"
if (Test-Path $pidFile) {
    $pid = Get-Content $pidFile
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Remove-Item $pidFile
}

# Clean up
Remove-Item ".run/*.pid" -ErrorAction SilentlyContinue
"""
    code, stdout, _ = run_validator(VALID_START, VALID_CLEANUP, ps_start, ps_cleanup)
    assert code == 0, f"Expected exit 0 for valid PowerShell scripts: {stdout}"


def test_error_count_in_output():
    """Output should show count of issues found."""
    start = "#!/usr/bin/env bash\necho hello\n"
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0
    assert "FAILED" in stdout
    assert "issue" in stdout.lower()


def test_no_proxy_localhost_missing_fails():
    """Start script with proxy but without localhost in NO_PROXY should fail."""
    start = VALID_START.replace("LOCALHOST_ENTRIES", "BYPASS_ENTRIES")
    start = start.replace("localhost", "remotehost")
    start = start.replace("127.0.0.1", "10.0.0.1")
    code, stdout, _ = run_validator(start, VALID_CLEANUP)
    assert code != 0, f"Expected non-zero for missing localhost: {stdout}"
    assert "NO_PROXY localhost" in stdout
