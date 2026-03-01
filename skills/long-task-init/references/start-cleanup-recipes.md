# ST-Start / ST-Clear Script Recipes

Templates and best practices for generating `st-start.sh` / `st-start.ps1` (ST runtime service startup) and `st-clear.sh` / `st-clear.ps1` (ST runtime service teardown) scripts. Choose recipes matching the project's tech stack and architecture from the design document.

**Relationship to init scripts**: `init.sh` installs runtimes, creates environments, and installs dependencies for **development environment**. `st-start.sh` builds the project, starts services, and verifies readiness for **ST testing runtime**. `st-clear.sh` stops services and releases resources after **ST testing completes**. All three are LLM-generated, project-specific, and recipe-driven.

**Key distinction**:
- `init.sh` = Development environment setup (Session level)
- `st-start.sh` / `st-clear.sh` = ST testing runtime (Feature ST / System ST level)

## General Rules — Start Scripts

1. **Idempotent** — re-running when services are already running should detect this and skip (check PID file or health endpoint); never start duplicate instances
2. **Cross-platform** — generate both `st-start.sh` (bash) and `st-start.ps1` (PowerShell)
3. **Fail-fast** — use `set -euo pipefail` (bash) / `$ErrorActionPreference = "Stop"` (PowerShell)
4. **Self-healing** — retry failed starts up to 3 times with exponential backoff; detect and report port conflicts
5. **Proxy-aware** — detect and forward HTTP_PROXY, HTTPS_PROXY, NO_PROXY; always add localhost/127.0.0.1 to NO_PROXY
6. **Health-check-driven** — never assume a service is ready; poll its health endpoint or port; timeout after configurable seconds
7. **Ordered startup** — always: build/compile → databases/caches → backend/API → frontend dev server
8. **Graceful failure** — if startup fails after all retries, write failure record to `task-progress.md`, print exact manual commands, exit non-zero

## General Rules — Cleanup Scripts

1. **Reverse-order shutdown** — frontend first → backend → databases/caches (opposite of startup)
2. **Graceful before forced** — SIGTERM with 10-second wait; SIGKILL if process still alive
3. **PID file cleanup** — always remove stale PID files even if process is already gone
4. **Port release verification** — verify ports are free after shutdown; report any still-occupied ports
5. **Temp file cleanup** — remove lock files, temp dirs, build caches created by start script
6. **Idempotent** — safe to run when services are already stopped; never error on "nothing to stop"
7. **Cross-platform** — generate both `st-clear.sh` (bash) and `st-clear.ps1` (PowerShell)
8. **Browser process cleanup** — if project has UI features (`"ui": true`), kill Chrome/Chromium process after services stop; use cross-platform detection (`taskkill` on Windows, `pkill` on Linux/macOS)

---

## Output Format — PID Visibility (IMPORTANT)

Scripts must output structured information to stdout for Claude Code to parse and record in `task-progress.md`.

### st-start.sh Output Format

After all services are started, print a summary table:

```bash
echo ""
echo "=== ST Runtime Services Started ==="
echo "| Service   | PID  | Port | Status  |"
echo "|-----------|------|------|---------|"
# For each service:
echo "| postgres  | $PG_PID  | 5432 | running |"
echo "| backend   | $BACKEND_PID  | 8000 | running |"
echo "| frontend  | $FRONTEND_PID  | 5173 | running |"
echo ""
echo "Summary: 3 services started."
echo "PIDs: $PG_PID, $BACKEND_PID, $FRONTEND_PID"
```

### st-start.ps1 Output Format

```powershell
Write-Host ""
Write-Host "=== ST Runtime Services Started ==="
Write-Host "| Service   | PID  | Port | Status  |"
Write-Host "|-----------|------|------|---------|"
# For each service:
Write-Host "| postgres  | $PgPid  | 5432 | running |"
Write-Host "| backend   | $BackendPid  | 8000 | running |"
Write-Host "| frontend  | $FrontendPid  | 5173 | running |"
Write-Host ""
Write-Host "Summary: 3 services started."
Write-Host "PIDs: $PgPid, $BackendPid, $FrontendPid"
```

### st-clear.sh Output Format

After all services are stopped, print a cleanup confirmation:

```bash
echo ""
echo "=== ST Runtime Services Cleared ==="
echo "| Service   | PID  | Action     | Result  |"
echo "|-----------|------|------------|---------|"
# For each service:
echo "| frontend  | $FRONTEND_PID  | SIGTERM    | stopped |"
echo "| backend   | $BACKEND_PID  | SIGTERM    | stopped |"
echo "| postgres  | $PG_PID  | SIGTERM    | stopped |"
echo "| chrome    | -    | force-kill | cleaned |"
echo ""
echo "Summary: All services stopped."
echo "Ports released: 5173, 8000, 5432"
```

### st-clear.ps1 Output Format

```powershell
Write-Host ""
Write-Host "=== ST Runtime Services Cleared ==="
Write-Host "| Service   | PID  | Action     | Result  |"
Write-Host "|-----------|------|------------|---------|"
# For each service:
Write-Host "| frontend  | $FrontendPid  | SIGTERM    | stopped |"
Write-Host "| backend   | $BackendPid  | SIGTERM    | stopped |"
Write-Host "| postgres  | $PgPid  | SIGTERM    | stopped |"
Write-Host "| chrome    | -    | force-kill | cleaned |"
Write-Host ""
Write-Host "Summary: All services stopped."
Write-Host "Ports released: 5173, 8000, 5432"
```

**Why this matters**: Claude Code reads stdout to extract PID information and records it in `task-progress.md` for tracking and debugging purposes.

---

## Standard Startup Order (6 Phases)

Every `st-start.sh` follows this phase sequence. Skip inapplicable phases but preserve order:

```
Phase 1: Environment     — load .env, detect/configure proxy, check prerequisites
Phase 2: Build/Compile   — compile source code (language-specific); fail-fast if build fails
Phase 3: Infrastructure  — start databases, caches, message queues
Phase 4: Backend         — start API/backend servers (from compiled artifacts)
Phase 5: Frontend        — start dev server or serve built assets
Phase 6: Health & Report — poll all services, print readiness summary
```

---

## Script Skeletons

### st-start.sh (bash)

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/.run"
mkdir -p "$LOG_DIR"

echo "=== [Project Name] Service Startup ==="

# --- Phase 1: Environment ---
# [load .env]
# [proxy detection — see Proxy Recipe]
# [already-running check — see Already Running Recipe]

# --- Phase 2: Build/Compile ---
# [build step — see Build Recipes]

# --- Phase 3: Infrastructure ---
# [start DB; write PID to $LOG_DIR/db.pid]

# --- Phase 4: Backend ---
# [start backend; write PID to $LOG_DIR/backend.pid]

# --- Phase 5: Frontend ---
# [start frontend; write PID to $LOG_DIR/frontend.pid]

# --- Phase 6: Health Check & Report ---
# [poll health endpoints with timeout]

echo ""
echo "=== Services Ready ==="
echo "Backend:  http://localhost:<port>"
echo "Frontend: http://localhost:<port>"
```

### st-start.ps1 (PowerShell)

```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$LogDir = Join-Path $PSScriptRoot ".run"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "=== [Project Name] Service Startup ==="

# --- Phase 1: Environment ---
# [load .env]
# [proxy detection — see Proxy Recipe]
# [already-running check]

# --- Phase 2: Build/Compile ---
# [build step — see Build Recipes]

# --- Phase 3: Infrastructure ---
# [start DB; write PID]

# --- Phase 4: Backend ---
# [start backend; write PID]

# --- Phase 5: Frontend ---
# [start frontend; write PID]

# --- Phase 6: Health Check & Report ---
# [poll health endpoints]

Write-Host ""
Write-Host "=== Services Ready ==="
```

### st-clear.sh (bash)

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/.run"

echo "=== [Project Name] Service Cleanup ==="

# --- Step 1: Stop frontend ---
# [read $LOG_DIR/frontend.pid; graceful stop]

# --- Step 2: Stop backend ---
# [read $LOG_DIR/backend.pid; graceful stop]

# --- Step 3: Stop infrastructure ---
# [stop databases, caches]

# --- Step 4: Kill Chrome browser (for UI features) ---
if command -v taskkill >/dev/null 2>&1; then
    # Windows (Git Bash / MSYS2)
    taskkill /F /IM chrome.exe /T 2>/dev/null || true
    taskkill /F /IM chromium.exe /T 2>/dev/null || true
else
    # Linux / macOS
    pkill -f "(chrome|chromium)" 2>/dev/null || true
fi

# --- Step 5: Clean temp files ---
# [remove $LOG_DIR/*.pid, lock files, temp dirs]

# --- Step 6: Verify ---
# [check ports are free]

echo ""
echo "=== Cleanup Complete ==="
```

### st-clear.ps1 (PowerShell)

```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$LogDir = Join-Path $PSScriptRoot ".run"

Write-Host "=== [Project Name] Service Cleanup ==="

# --- Step 1: Stop frontend ---
# [Stop-Process from PID file]

# --- Step 2: Stop backend ---
# [Stop-Process from PID file]

# --- Step 3: Stop infrastructure ---
# [stop databases, caches]

# --- Step 4: Kill Chrome browser (for UI features) ---
foreach ($name in @("chrome", "chromium")) {
    $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Host "Stopping $name browser..."
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

# --- Step 5: Clean temp files ---
# [Remove-Item *.pid, lock files]

# --- Step 6: Verify ---

Write-Host "=== Cleanup Complete ==="
```

---

## Reusable Recipe Blocks

### .env Loading

```bash
# --- Load .env ---
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "Loaded .env"
fi
```

```powershell
# --- Load .env ---
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
    Write-Host "Loaded .env"
}
```

### Proxy Detection and Configuration

```bash
# --- Proxy Detection and Configuration ---
HTTP_PROXY="${HTTP_PROXY:-${http_proxy:-}}"
HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy:-}}"
NO_PROXY="${NO_PROXY:-${no_proxy:-}}"

if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then
    # Always add localhost variants to NO_PROXY to prevent local
    # service-to-service calls from going through proxy
    LOCALHOST_ENTRIES="localhost,127.0.0.1,::1,0.0.0.0"
    if [ -n "$NO_PROXY" ]; then
        NO_PROXY="${NO_PROXY},${LOCALHOST_ENTRIES}"
    else
        NO_PROXY="$LOCALHOST_ENTRIES"
    fi
    export HTTP_PROXY HTTPS_PROXY NO_PROXY
    export http_proxy="$HTTP_PROXY"
    export https_proxy="$HTTPS_PROXY"
    export no_proxy="$NO_PROXY"
    echo "Proxy detected: HTTP_PROXY=${HTTP_PROXY}"
    echo "NO_PROXY includes: ${LOCALHOST_ENTRIES}"
fi
```

```powershell
# --- Proxy Detection and Configuration ---
$HttpProxy = if ($env:HTTP_PROXY) { $env:HTTP_PROXY } elseif ($env:http_proxy) { $env:http_proxy } else { $null }
$HttpsProxy = if ($env:HTTPS_PROXY) { $env:HTTPS_PROXY } elseif ($env:https_proxy) { $env:https_proxy } else { $null }
$NoProxy = if ($env:NO_PROXY) { $env:NO_PROXY } elseif ($env:no_proxy) { $env:no_proxy } else { $null }

if ($HttpProxy -or $HttpsProxy) {
    $LocalhostEntries = "localhost,127.0.0.1,::1,0.0.0.0"
    $NoProxy = if ($NoProxy) { "$NoProxy,$LocalhostEntries" } else { $LocalhostEntries }
    $env:HTTP_PROXY = $HttpProxy; $env:http_proxy = $HttpProxy
    $env:HTTPS_PROXY = $HttpsProxy; $env:https_proxy = $HttpsProxy
    $env:NO_PROXY = $NoProxy; $env:no_proxy = $NoProxy
    Write-Host "Proxy detected: HTTP_PROXY=$HttpProxy"
    Write-Host "NO_PROXY includes: $LocalhostEntries"
}
```

### Already-Running Detection

```bash
# --- Already Running Check ---
is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        # Stale PID file — clean up
        rm -f "$pid_file"
    fi
    return 1
}

# Check if all services are already up
ALL_RUNNING=true
for pid_file in "$LOG_DIR"/*.pid; do
    [ -f "$pid_file" ] || continue
    if ! is_running "$pid_file"; then
        ALL_RUNNING=false
        break
    fi
done

if [ "$ALL_RUNNING" = true ] && [ -n "$(ls "$LOG_DIR"/*.pid 2>/dev/null)" ]; then
    echo "All services already running. Use st-clear.sh first to restart."
    exit 0
fi
```

```powershell
# --- Already Running Check ---
function Test-ServiceRunning($PidFile) {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile
        try {
            Get-Process -Id $pid -ErrorAction Stop | Out-Null
            return $true
        } catch {
            Remove-Item $PidFile -Force
        }
    }
    return $false
}
```

### Health Check — Port Polling

```bash
wait_for_port() {
    local host="$1" port="$2" name="$3" timeout="${4:-60}"
    local elapsed=0
    echo "Waiting for $name on $host:$port (timeout: ${timeout}s)..."
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ "$elapsed" -ge "$timeout" ]; then
            echo "ERROR: $name did not become ready on $host:$port within ${timeout}s"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    echo "  $name ready after ${elapsed}s"
}
```

```powershell
function Wait-ForPort {
    param(
        [string]$HostName, [int]$Port, [string]$Name, [int]$Timeout = 60
    )
    $elapsed = 0
    Write-Host "Waiting for $Name on ${HostName}:${Port} (timeout: ${Timeout}s)..."
    while ($elapsed -lt $Timeout) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect($HostName, $Port)
            $tcp.Close()
            Write-Host "  $Name ready after ${elapsed}s"
            return
        } catch {
            Start-Sleep 2
            $elapsed += 2
        }
    }
    throw "$Name did not become ready on ${HostName}:${Port} within ${Timeout}s"
}
```

### Health Check — HTTP Endpoint

```bash
wait_for_http() {
    local url="$1" name="$2" timeout="${3:-60}"
    local elapsed=0
    echo "Waiting for $name at $url (timeout: ${timeout}s)..."
    while ! curl -sf "$url" > /dev/null 2>&1; do
        if [ "$elapsed" -ge "$timeout" ]; then
            echo "ERROR: $name health check failed at $url after ${timeout}s"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    echo "  $name healthy after ${elapsed}s"
}
```

```powershell
function Wait-ForHttp {
    param(
        [string]$Url, [string]$Name, [int]$Timeout = 60
    )
    $elapsed = 0
    Write-Host "Waiting for $Name at $Url (timeout: ${Timeout}s)..."
    while ($elapsed -lt $Timeout) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
            Write-Host "  $Name healthy after ${elapsed}s"
            return
        } catch {
            Start-Sleep 2
            $elapsed += 2
        }
    }
    throw "$Name health check failed at $Url after ${Timeout}s"
}
```

### Port Conflict Detection

```bash
check_port_free() {
    local port="$1" name="$2"
    if nc -z localhost "$port" 2>/dev/null; then
        echo "WARNING: Port $port (for $name) is already in use."
        local occupier
        occupier=$(lsof -ti tcp:"$port" 2>/dev/null || true)
        if [ -n "$occupier" ]; then
            echo "  Occupied by PID: $occupier"
            echo "  To free: kill $occupier  (or run st-clear.sh first)"
        fi
        return 1
    fi
    return 0
}
```

```powershell
function Test-PortFree {
    param([int]$Port, [string]$Name)
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "WARNING: Port $Port (for $Name) is already in use."
        Write-Host "  Occupied by PID: $($conn.OwningProcess)"
        return $false
    }
    return $true
}
```

### Retry with Backoff

```bash
start_with_retry() {
    local name="$1" max_attempts="${2:-3}" attempt=1
    shift 2
    while [ "$attempt" -le "$max_attempts" ]; do
        echo "Starting $name (attempt $attempt/$max_attempts)..."
        if "$@"; then
            echo "  $name started successfully."
            return 0
        fi
        echo "  WARNING: $name failed on attempt $attempt."
        if [ "$attempt" -lt "$max_attempts" ]; then
            local wait_time=$((attempt * 3))
            echo "  Retrying in ${wait_time}s..."
            sleep "$wait_time"
        fi
        attempt=$((attempt + 1))
    done
    echo "ERROR: $name failed after $max_attempts attempts."
    return 1
}
```

```powershell
function Start-WithRetry {
    param(
        [string]$Name, [scriptblock]$Action, [int]$MaxAttempts = 3
    )
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        Write-Host "Starting $Name (attempt $attempt/$MaxAttempts)..."
        try {
            & $Action
            Write-Host "  $Name started successfully."
            return
        } catch {
            Write-Host "  WARNING: $Name failed on attempt $attempt."
            if ($attempt -lt $MaxAttempts) {
                $wait = $attempt * 3
                Write-Host "  Retrying in ${wait}s..."
                Start-Sleep $wait
            }
        }
    }
    throw "$Name failed after $MaxAttempts attempts."
}
```

### PID File Management

```bash
write_pid() {
    local pid_file="$1" pid="$2"
    echo "$pid" > "$pid_file"
    echo "  PID $pid written to $pid_file"
}

stop_from_pid() {
    local pid_file="$1" name="$2"
    if [ ! -f "$pid_file" ]; then
        echo "$name: no PID file found — may not be running."
        return 0
    fi
    local pid
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Stopping $name (PID $pid)..."
        kill "$pid"
        local wait=0
        while kill -0 "$pid" 2>/dev/null && [ "$wait" -lt 10 ]; do
            sleep 1
            wait=$((wait + 1))
        done
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Force-killing $name (PID $pid)..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        echo "  $name stopped."
    else
        echo "$name (PID $pid) was not running — stale PID file."
    fi
    rm -f "$pid_file"
}
```

```powershell
function Write-Pid($PidFile, $Pid) {
    $Pid | Out-File -FilePath $PidFile -Encoding ascii
    Write-Host "  PID $Pid written to $PidFile"
}

function Stop-FromPid($PidFile, $Name) {
    if (-not (Test-Path $PidFile)) {
        Write-Host "$Name`: no PID file found."
        return
    }
    $pid = Get-Content $PidFile
    try {
        $proc = Get-Process -Id $pid -ErrorAction Stop
        Write-Host "Stopping $Name (PID $pid)..."
        Stop-Process -Id $pid
        $proc.WaitForExit(10000)
        if (-not $proc.HasExited) {
            Write-Host "  Force-killing $Name..."
            Stop-Process -Id $pid -Force
        }
        Write-Host "  $Name stopped."
    } catch {
        Write-Host "$Name (PID $pid) was not running — stale PID file."
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}
```

### Graceful Failure Recording

```bash
record_startup_failure() {
    local component="$1"
    local timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo ""
    echo "=== STARTUP FAILED: $component ==="
    echo "Please start $component manually and re-run st-start.sh"
    echo ""
    # Append to task-progress.md if it exists
    if [ -f "task-progress.md" ]; then
        printf "\n### Startup Failure — %s\n- **Component**: %s\n- **Time**: %s\n- **Action required**: Manual startup\n" \
            "$timestamp" "$component" "$timestamp" >> task-progress.md
    fi
}
```

```powershell
function Record-StartupFailure($Component) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host ""
    Write-Host "=== STARTUP FAILED: $Component ==="
    Write-Host "Please start $Component manually and re-run st-start.ps1"
    Write-Host ""
    $progressFile = Join-Path $PSScriptRoot "task-progress.md"
    if (Test-Path $progressFile) {
        Add-Content $progressFile "`n### Startup Failure - $timestamp`n- **Component**: $Component`n- **Action required**: Manual startup"
    }
}
```

---

## Build / Compile Recipes

Build must complete **before** any services start. Build failure = hard stop (no services started).

### Python (interpreted — no compile needed)

```bash
# --- Phase 2: Build ---
# No build needed — Python is interpreted
# Ensure editable install if using src layout
if [ -f "pyproject.toml" ]; then
    pip install -e . 2>/dev/null || true
fi
```

### TypeScript / Node.js

```bash
# --- Phase 2: Build ---
echo "Building TypeScript project..."
if [ -f "package.json" ]; then
    if grep -q '"build"' package.json; then
        npm run build || { record_startup_failure "TypeScript build"; exit 1; }
    elif command -v npx &>/dev/null; then
        npx tsc || { record_startup_failure "TypeScript build"; exit 1; }
    fi
fi
echo "Build complete."
```

```powershell
# --- Phase 2: Build ---
Write-Host "Building TypeScript project..."
if (Test-Path "package.json") {
    $pkg = Get-Content package.json | ConvertFrom-Json
    if ($pkg.scripts.PSObject.Properties.Name -contains "build") {
        npm run build
        if ($LASTEXITCODE -ne 0) { Record-StartupFailure "TypeScript build"; exit 1 }
    }
}
Write-Host "Build complete."
```

### Java / Maven

```bash
# --- Phase 2: Build ---
echo "Building Java project..."
if [ -f "mvnw" ]; then
    ./mvnw package -DskipTests -q || { record_startup_failure "Maven build"; exit 1; }
elif [ -f "gradlew" ]; then
    ./gradlew build -x test -q || { record_startup_failure "Gradle build"; exit 1; }
elif command -v mvn &>/dev/null; then
    mvn package -DskipTests -q || { record_startup_failure "Maven build"; exit 1; }
fi
echo "Build complete."
```

### C / C++ (CMake)

```bash
# --- Phase 2: Build ---
echo "Building C/C++ project..."
BUILD_DIR="${SCRIPT_DIR}/build"
mkdir -p "$BUILD_DIR"
cmake -S . -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Debug 2>/dev/null || true
cmake --build "$BUILD_DIR" --parallel || { record_startup_failure "C/C++ build"; exit 1; }
echo "Build complete."
```

### Go

```bash
# --- Phase 2: Build ---
echo "Building Go project..."
BIN_DIR="${SCRIPT_DIR}/bin"
mkdir -p "$BIN_DIR"
go build -o "$BIN_DIR/" ./... || { record_startup_failure "Go build"; exit 1; }
echo "Build complete."
```

### Rust

```bash
# --- Phase 2: Build ---
echo "Building Rust project..."
cargo build || { record_startup_failure "Rust build"; exit 1; }
echo "Build complete."
```

### Frontend Dev Server (auto-compiles)

When using a dev server (Vite, webpack-dev-server, Next.js dev), explicit build is typically not needed — the dev server compiles on the fly. In this case, annotate the build phase:

```bash
# --- Phase 2: Build ---
# No explicit build needed — dev server (Vite/Next.js) compiles on the fly
# For production builds: npm run build
```

### Incremental Build Awareness

Use build tool caching — do NOT force full rebuild every time:

```bash
# Good — let the tool decide what to rebuild:
npm run build                           # TypeScript — tsc incremental is default
./mvnw package -DskipTests              # Maven — incremental compilation
cmake --build build/                    # CMake — only rebuilds changed files
cargo build                             # Rust — incremental compilation

# Bad — forced full rebuild (slow, unnecessary):
rm -rf dist/ && npm run build           # Do NOT delete build output
./mvnw clean package -DskipTests        # Do NOT clean unless necessary
rm -rf build/ && cmake -S . -B build/   # Do NOT recreate build directory
cargo clean && cargo build              # Do NOT clean unless necessary
```

---

## Per-Tech-Stack Startup Recipes

### Frontend — Vite Dev Server

```bash
# --- Phase 5: Frontend (Vite) ---
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
check_port_free "$FRONTEND_PORT" "Vite dev server"
npm run dev -- --port "$FRONTEND_PORT" > "$LOG_DIR/frontend.log" 2>&1 &
write_pid "$LOG_DIR/frontend.pid" $!
wait_for_http "http://localhost:$FRONTEND_PORT" "Vite dev server" 60
```

### Frontend — Next.js Dev Server

```bash
# --- Phase 5: Frontend (Next.js) ---
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
check_port_free "$FRONTEND_PORT" "Next.js"
npm run dev -- -p "$FRONTEND_PORT" > "$LOG_DIR/frontend.log" 2>&1 &
write_pid "$LOG_DIR/frontend.pid" $!
wait_for_http "http://localhost:$FRONTEND_PORT" "Next.js" 90
```

### Frontend — webpack-dev-server

```bash
# --- Phase 5: Frontend (webpack) ---
FRONTEND_PORT="${FRONTEND_PORT:-8080}"
check_port_free "$FRONTEND_PORT" "webpack-dev-server"
npx webpack serve --port "$FRONTEND_PORT" > "$LOG_DIR/frontend.log" 2>&1 &
write_pid "$LOG_DIR/frontend.pid" $!
wait_for_http "http://localhost:$FRONTEND_PORT" "webpack-dev-server" 60
```

### Frontend — Angular CLI

```bash
# --- Phase 5: Frontend (Angular) ---
FRONTEND_PORT="${FRONTEND_PORT:-4200}"
check_port_free "$FRONTEND_PORT" "Angular"
npx ng serve --port "$FRONTEND_PORT" > "$LOG_DIR/frontend.log" 2>&1 &
write_pid "$LOG_DIR/frontend.pid" $!
wait_for_http "http://localhost:$FRONTEND_PORT" "Angular dev server" 90
```

### Backend — FastAPI / Uvicorn

```bash
# --- Phase 4: Backend (FastAPI) ---
BACKEND_PORT="${BACKEND_PORT:-8000}"
check_port_free "$BACKEND_PORT" "FastAPI"
source .venv/bin/activate 2>/dev/null || true
uvicorn src.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload > "$LOG_DIR/backend.log" 2>&1 &
write_pid "$LOG_DIR/backend.pid" $!
wait_for_http "http://localhost:$BACKEND_PORT/health" "FastAPI" 30
```

### Backend — Flask

```bash
# --- Phase 4: Backend (Flask) ---
BACKEND_PORT="${BACKEND_PORT:-5000}"
check_port_free "$BACKEND_PORT" "Flask"
source .venv/bin/activate 2>/dev/null || true
FLASK_APP="${FLASK_APP:-app}" flask run --host 0.0.0.0 --port "$BACKEND_PORT" > "$LOG_DIR/backend.log" 2>&1 &
write_pid "$LOG_DIR/backend.pid" $!
wait_for_port localhost "$BACKEND_PORT" "Flask" 30
```

### Backend — Django

```bash
# --- Phase 4: Backend (Django) ---
BACKEND_PORT="${BACKEND_PORT:-8000}"
check_port_free "$BACKEND_PORT" "Django"
source .venv/bin/activate 2>/dev/null || true
python manage.py runserver "0.0.0.0:$BACKEND_PORT" > "$LOG_DIR/backend.log" 2>&1 &
write_pid "$LOG_DIR/backend.pid" $!
wait_for_port localhost "$BACKEND_PORT" "Django" 30
```

### Backend — Express / Node.js

```bash
# --- Phase 4: Backend (Express) ---
BACKEND_PORT="${BACKEND_PORT:-3001}"
check_port_free "$BACKEND_PORT" "Express"
PORT="$BACKEND_PORT" node dist/server.js > "$LOG_DIR/backend.log" 2>&1 &
write_pid "$LOG_DIR/backend.pid" $!
wait_for_http "http://localhost:$BACKEND_PORT/health" "Express" 30
```

### Backend — Spring Boot

```bash
# --- Phase 4: Backend (Spring Boot) ---
BACKEND_PORT="${BACKEND_PORT:-8080}"
check_port_free "$BACKEND_PORT" "Spring Boot"
JAR_FILE=$(find target -name '*.jar' -not -name '*-sources.jar' -not -name '*-javadoc.jar' | head -1)
if [ -z "$JAR_FILE" ]; then
    record_startup_failure "Spring Boot (no JAR found — build may have failed)"
    exit 1
fi
java -jar "$JAR_FILE" --server.port="$BACKEND_PORT" > "$LOG_DIR/backend.log" 2>&1 &
write_pid "$LOG_DIR/backend.pid" $!
wait_for_http "http://localhost:$BACKEND_PORT/actuator/health" "Spring Boot" 90
```

### Backend — Go Binary

```bash
# --- Phase 4: Backend (Go) ---
BACKEND_PORT="${BACKEND_PORT:-8080}"
check_port_free "$BACKEND_PORT" "Go server"
BIN_FILE=$(find bin/ -type f -executable | head -1)
if [ -z "$BIN_FILE" ]; then
    record_startup_failure "Go server (no binary found — build may have failed)"
    exit 1
fi
PORT="$BACKEND_PORT" "$BIN_FILE" > "$LOG_DIR/backend.log" 2>&1 &
write_pid "$LOG_DIR/backend.pid" $!
wait_for_port localhost "$BACKEND_PORT" "Go server" 30
```

### Database — PostgreSQL (local)

```bash
# --- Phase 3: Infrastructure (PostgreSQL) ---
DB_PORT="${DB_PORT:-5432}"
check_port_free "$DB_PORT" "PostgreSQL"
if command -v pg_ctl &>/dev/null && [ -n "${PGDATA:-}" ]; then
    pg_ctl start -D "$PGDATA" -l "$LOG_DIR/postgres.log" -w
    wait_for_port localhost "$DB_PORT" "PostgreSQL" 30
elif command -v docker &>/dev/null; then
    docker compose up -d postgres 2>/dev/null || \
    docker run -d --name project-postgres \
        -p "$DB_PORT:5432" \
        -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}" \
        postgres:16 > /dev/null
    wait_for_port localhost "$DB_PORT" "PostgreSQL" 30
fi
```

### Database — MySQL

```bash
# --- Phase 3: Infrastructure (MySQL) ---
DB_PORT="${DB_PORT:-3306}"
check_port_free "$DB_PORT" "MySQL"
if command -v docker &>/dev/null; then
    docker compose up -d mysql 2>/dev/null || \
    docker run -d --name project-mysql \
        -p "$DB_PORT:3306" \
        -e MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-root}" \
        mysql:8 > /dev/null
    wait_for_port localhost "$DB_PORT" "MySQL" 60
fi
```

### Database — MongoDB

```bash
# --- Phase 3: Infrastructure (MongoDB) ---
MONGO_PORT="${MONGO_PORT:-27017}"
check_port_free "$MONGO_PORT" "MongoDB"
if command -v docker &>/dev/null; then
    docker compose up -d mongo 2>/dev/null || \
    docker run -d --name project-mongo \
        -p "$MONGO_PORT:27017" \
        mongo:7 > /dev/null
    wait_for_port localhost "$MONGO_PORT" "MongoDB" 30
fi
```

### Database — SQLite

```bash
# --- Phase 3: Infrastructure (SQLite) ---
# No startup needed — SQLite is an embedded database (file-based)
echo "SQLite: no startup needed (embedded)"
```

### Cache — Redis

```bash
# --- Phase 3: Infrastructure (Redis) ---
REDIS_PORT="${REDIS_PORT:-6379}"
check_port_free "$REDIS_PORT" "Redis"
if command -v redis-server &>/dev/null; then
    redis-server --port "$REDIS_PORT" --daemonize yes --logfile "$LOG_DIR/redis.log"
    wait_for_port localhost "$REDIS_PORT" "Redis" 15
elif command -v docker &>/dev/null; then
    docker compose up -d redis 2>/dev/null || \
    docker run -d --name project-redis \
        -p "$REDIS_PORT:6379" \
        redis:7 > /dev/null
    wait_for_port localhost "$REDIS_PORT" "Redis" 15
fi
```

### Docker Compose (all services)

When the project uses `docker-compose.yml` for all services:

```bash
# --- Phase 3-5: All Services (Docker Compose) ---
echo "Starting services via Docker Compose..."
docker compose up -d --build || { record_startup_failure "Docker Compose"; exit 1; }

# Health check each exposed service
# [Add wait_for_port/wait_for_http for each service port]
echo "Docker Compose services started."
```

Cleanup:
```bash
# --- Docker Compose Cleanup ---
docker compose down --remove-orphans
echo "Docker Compose services stopped."
```

---

## Cleanup Recipes

### Stop from PID file (generic)

Use the `stop_from_pid` function from the PID File Management recipe block above for each service.

### Docker Compose Cleanup

```bash
if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ] || [ -f "compose.yml" ]; then
    echo "Stopping Docker Compose services..."
    docker compose down --remove-orphans 2>/dev/null || true
fi
```

### Docker Container Cleanup (standalone containers)

```bash
for container_name in project-postgres project-mysql project-mongo project-redis; do
    if docker ps -q -f "name=$container_name" 2>/dev/null | grep -q .; then
        echo "Stopping Docker container: $container_name"
        docker stop "$container_name" 2>/dev/null || true
        docker rm "$container_name" 2>/dev/null || true
    fi
done
```

### Port Release Verification

```bash
verify_ports_free() {
    local ports=("$@")
    local occupied=()
    for port in "${ports[@]}"; do
        if nc -z localhost "$port" 2>/dev/null; then
            occupied+=("$port")
        fi
    done
    if [ ${#occupied[@]} -gt 0 ]; then
        echo "WARNING: Ports still occupied after cleanup: ${occupied[*]}"
        echo "  Use: lsof -ti tcp:<port> | xargs kill -9"
        return 1
    fi
    echo "All ports released."
    return 0
}

# Call after all stops:
verify_ports_free 5432 8000 5173
```

### Temp File Cleanup

```bash
# --- Clean temp files ---
rm -f "$LOG_DIR"/*.pid
rm -f "$LOG_DIR"/*.log
# Remove lock files if present
rm -f ./*.lock 2>/dev/null || true
# Remove temp test artifacts
rm -rf .pytest_cache __pycache__ .mypy_cache 2>/dev/null || true
echo "Temp files cleaned."
```

---

## Selection Guide

| Signal in Design Doc | Start Recipe | Cleanup Recipe |
|---|---|---|
| `npm run dev` / Vite | Vite dev server | stop_from_pid |
| `next dev` / Next.js | Next.js dev server | stop_from_pid |
| `ng serve` / Angular | Angular CLI | stop_from_pid |
| webpack-dev-server | webpack dev server | stop_from_pid |
| FastAPI / uvicorn | FastAPI + Uvicorn | stop_from_pid |
| Flask | Flask | stop_from_pid |
| Django runserver | Django | stop_from_pid |
| Express / Node.js server | Express | stop_from_pid |
| Spring Boot | Spring Boot JAR | stop_from_pid |
| Go net/http | Go binary | stop_from_pid |
| PostgreSQL in design | PostgreSQL (pg_ctl or docker) | pg_ctl stop or docker stop |
| MySQL in design | MySQL docker | docker stop |
| MongoDB in design | MongoDB docker | docker stop |
| Redis in design | Redis (native or docker) | redis-cli shutdown or docker stop |
| SQLite only | No startup (embedded) | No cleanup |
| `docker-compose.yml` | Docker Compose up | Docker Compose down |
| CLI tool / library | Minimal (see below) | Minimal |

## Combining Recipes

Projects needing multiple services chain recipes in order. Each service is idempotent and has its own health check:

```bash
# Example: Python (FastAPI) + PostgreSQL + Redis + Vite frontend
# Phase 2: Build
npm run build                                           # Build frontend
pip install -e . 2>/dev/null || true                    # Install backend

# Phase 3: Infrastructure
# [PostgreSQL recipe]
# [Redis recipe]

# Phase 4: Backend
# [FastAPI recipe]
# Apply database migrations after DB is ready:
python manage.py migrate 2>/dev/null || alembic upgrade head 2>/dev/null || true

# Phase 5: Frontend
# [Vite recipe]
```

## CLI / Library Projects (Minimal Scripts)

For projects with no runtime services:

```bash
#!/usr/bin/env bash
echo "No services to start — CLI/library project"
echo "Run tests directly: python -m pytest"
exit 0
```

```powershell
Write-Host "No services to start — CLI/library project"
Write-Host "Run tests directly: python -m pytest"
exit 0
```

---

## Windows / PowerShell Considerations

### Background Processes

PowerShell does not have bash's `&` operator. Use `Start-Process`:

```powershell
$proc = Start-Process -PassThru -NoNewWindow -FilePath "node" -ArgumentList "dist/server.js" `
    -RedirectStandardOutput "$LogDir/backend.log" -RedirectStandardError "$LogDir/backend.err"
Write-Pid "$LogDir/backend.pid" $proc.Id
```

### Port Checking (nc alternative)

```powershell
# Instead of nc -z:
function Test-Port($Host, $Port) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect($Host, $Port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}
```

### Process Termination

```powershell
# Instead of kill / kill -9:
Stop-Process -Id $pid -ErrorAction SilentlyContinue           # Graceful
Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue    # Forced (SIGKILL equivalent)

# Instead of taskkill for named processes:
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Docker on Windows

Docker Desktop for Windows works the same way:
```powershell
docker compose up -d --build
docker compose down --remove-orphans
```

---

## Proxy-Specific Notes

### Package Managers Behind Proxy

Most package managers respect `HTTP_PROXY` / `HTTPS_PROXY` env vars automatically, but some need explicit configuration:

```bash
# npm — respects env vars, but can also be set explicitly:
npm config set proxy "$HTTP_PROXY"
npm config set https-proxy "$HTTPS_PROXY"
npm config set noproxy "$NO_PROXY"

# pip — respects env vars; can also pass --proxy:
pip install --proxy "$HTTP_PROXY" -r requirements.txt

# Docker — requires daemon configuration for image pulls:
# /etc/docker/daemon.json or Docker Desktop settings
```

### Dev Servers Behind Proxy

Dev servers typically bind to localhost. The key issue is preventing requests *to* localhost from going through the proxy:

```bash
# This is why NO_PROXY must include localhost:
# Without it, curl http://localhost:3000 goes through the proxy → fails
NO_PROXY="localhost,127.0.0.1,::1,0.0.0.0"
```

### WebSocket Connections

Some frontend dev servers (Vite, webpack) use WebSocket for HMR (Hot Module Replacement). Proxy servers may block WebSocket upgrade requests:

```bash
# If HMR fails behind proxy, try configuring the dev server:
# Vite: vite.config.ts → server.hmr.host = 'localhost'
# webpack: devServer.client.webSocketURL = 'ws://localhost:<port>/ws'
```
