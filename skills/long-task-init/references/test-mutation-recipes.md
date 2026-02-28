# Test & Mutation Script Recipes

Templates and best practices for generating `test.sh` / `test.ps1` (test runner wrapper) and `mutate.sh` / `mutate.ps1` (mutation testing wrapper) scripts. Choose recipes matching the project's tech stack from the design document and `feature-list.json`.

**Relationship to other scripts**: `init.sh` installs runtimes and dependencies. `start.sh` builds and starts services. `test.sh` runs unit tests and coverage. `mutate.sh` runs mutation testing. All are LLM-generated, project-specific, and recipe-driven.

## General Rules — Test Scripts

1. **Idempotent** — safe to re-run; no side effects beyond test output
2. **Cross-platform** — generate both `test.sh` (bash) and `test.ps1` (PowerShell)
3. **Fail-fast** — use `set -euo pipefail` (bash) / `$ErrorActionPreference = "Stop"` (PowerShell)
4. **Load .env** — environment variables may contain test-relevant configs (DB URLs, API keys)
5. **Activate environment** — venv/conda/nvm/sdkman must be active before running tools
6. **Check tool availability** — verify test framework and coverage tool exist before executing; exit 2 if missing
7. **Exit codes** — `0` = all tests pass (and coverage above threshold if `--coverage`), `1` = test failures or coverage below threshold, `2` = tool not found / environment error
8. **Structured output** — print clear summary line at end with pass/fail counts and coverage percentages
9. **Graceful failure** — if tool is missing or env broken, print clear diagnostic message and manual fix instructions; never silently skip

## General Rules — Mutation Scripts

1. **Idempotent** — safe to re-run
2. **Cross-platform** — bash + PowerShell
3. **Fail-fast** — same error handling as test scripts
4. **Load .env** — same reason as test scripts
5. **Activate environment** — same as test scripts
6. **Check tool availability** — verify mutation tool exists; exit 2 if missing
7. **Two modes** — `--incremental <files>` (changed files only) and `--full` (entire codebase)
8. **Exit codes** — `0` = mutation score above threshold, `1` = score below threshold, `2` = tool not found / environment error
9. **Structured output** — print mutation score, killed/survived/total counts
10. **Graceful failure** — same as test scripts

---

## Script Interface

### test.sh / test.ps1

```
Usage: ./test.sh [OPTIONS]
  (no args)    Run full test suite
  --coverage   Run with coverage report

Exit codes:
  0  All tests pass (coverage above threshold if --coverage)
  1  Test failures or coverage below threshold
  2  Tool not found / environment error
```

### mutate.sh / mutate.ps1

```
Usage: ./mutate.sh MODE [FILES]
  --incremental <file1> [file2...]   Mutate only specified files
  --full                              Mutate entire codebase

Exit codes:
  0  Mutation score above threshold
  1  Mutation score below threshold
  2  Tool not found / environment error
```

---

## Script Skeletons

### test.sh (bash)

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== [Project Name] Test Runner ==="

# --- Phase 1: Environment ---
# [load .env — see .env Loading recipe]
# [activate environment — see Environment Activation recipe]

# --- Phase 2: Tool Check ---
# [check_tool — see Tool Availability Check recipe]

# --- Phase 3: Execute ---
MODE="${1:-test}"
case "$MODE" in
  --coverage)
    echo "Running tests with coverage..."
    # [coverage command — see Per-Tech-Stack Test Recipes]
    ;;
  *)
    echo "Running full test suite..."
    # [test command — see Per-Tech-Stack Test Recipes]
    ;;
esac

EXIT_CODE=$?
if [ "$EXIT_CODE" -eq 0 ]; then
    echo ""
    echo "=== Tests Passed ==="
else
    echo ""
    echo "=== Tests Failed (exit code: $EXIT_CODE) ==="
fi
exit "$EXIT_CODE"
```

### test.ps1 (PowerShell)

```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== [Project Name] Test Runner ==="

# --- Phase 1: Environment ---
# [load .env]
# [activate environment]

# --- Phase 2: Tool Check ---
# [check_tool]

# --- Phase 3: Execute ---
$Mode = if ($args.Count -gt 0) { $args[0] } else { "test" }

switch ($Mode) {
    "--coverage" {
        Write-Host "Running tests with coverage..."
        # [coverage command]
    }
    default {
        Write-Host "Running full test suite..."
        # [test command]
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Tests Passed ==="
} else {
    Write-Host "`n=== Tests Failed (exit code: $LASTEXITCODE) ==="
    exit $LASTEXITCODE
}
```

### mutate.sh (bash)

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== [Project Name] Mutation Testing ==="

# --- Phase 1: Environment ---
# [load .env]
# [activate environment]

# --- Phase 2: Tool Check ---
# [check mutation tool availability]

# --- Phase 3: Execute ---
MODE="${1:---full}"
shift || true

case "$MODE" in
  --incremental)
    if [ "$#" -eq 0 ]; then
        echo "ERROR: --incremental requires file arguments"
        exit 2
    fi
    CHANGED_FILES="$*"
    echo "Running incremental mutation on: $CHANGED_FILES"
    # [incremental mutation command — see Per-Tech-Stack Mutation Recipes]
    ;;
  --full)
    echo "Running full mutation testing..."
    # [full mutation command — see Per-Tech-Stack Mutation Recipes]
    ;;
  *)
    echo "Usage: ./mutate.sh [--incremental <files>|--full]"
    exit 2
    ;;
esac

EXIT_CODE=$?
# [Parse mutation results — see Structured Output Parsing recipe]
if [ "$EXIT_CODE" -eq 0 ]; then
    echo ""
    echo "=== Mutation Testing Passed ==="
else
    echo ""
    echo "=== Mutation Testing Failed (exit code: $EXIT_CODE) ==="
fi
exit "$EXIT_CODE"
```

### mutate.ps1 (PowerShell)

```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== [Project Name] Mutation Testing ==="

# --- Phase 1: Environment ---
# [load .env]
# [activate environment]

# --- Phase 2: Tool Check ---
# [check mutation tool]

# --- Phase 3: Execute ---
$Mode = if ($args.Count -gt 0) { $args[0] } else { "--full" }

switch ($Mode) {
    "--incremental" {
        $Files = $args[1..($args.Count - 1)]
        if ($Files.Count -eq 0) {
            Write-Host "ERROR: --incremental requires file arguments"
            exit 2
        }
        $ChangedFiles = $Files -join ","
        Write-Host "Running incremental mutation on: $ChangedFiles"
        # [incremental mutation command]
    }
    "--full" {
        Write-Host "Running full mutation testing..."
        # [full mutation command]
    }
    default {
        Write-Host "Usage: ./mutate.ps1 [--incremental <files>|--full]"
        exit 2
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Mutation Testing Passed ==="
} else {
    Write-Host "`n=== Mutation Testing Failed (exit code: $LASTEXITCODE) ==="
    exit $LASTEXITCODE
}
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

### Environment Activation

```bash
# --- Python: venv / conda ---
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated .venv"
elif [ -n "${CONDA_DEFAULT_ENV:-}" ]; then
    conda activate "$CONDA_DEFAULT_ENV"
    echo "Activated conda: $CONDA_DEFAULT_ENV"
elif [ -f "environment.yml" ] || [ -f "environment.yaml" ]; then
    ENV_NAME=$(head -1 environment.yml | sed 's/name: //')
    conda activate "$ENV_NAME" 2>/dev/null || true
fi
```

```bash
# --- Node.js: nvm ---
if [ -f ".nvmrc" ] && command -v nvm &>/dev/null; then
    nvm use
fi
```

```bash
# --- Java: sdkman ---
if [ -f ".sdkmanrc" ] && [ -n "${SDKMAN_DIR:-}" ]; then
    source "$SDKMAN_DIR/bin/sdkman-init.sh"
    sdk env install 2>/dev/null || true
fi
```

```powershell
# --- Python: venv / conda ---
$venvActivate = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Host "Activated .venv"
} elseif ($env:CONDA_DEFAULT_ENV) {
    conda activate $env:CONDA_DEFAULT_ENV
}
```

```powershell
# --- Node.js: nvm ---
if (Test-Path ".nvmrc") {
    nvm use (Get-Content .nvmrc).Trim() 2>$null
}
```

### Tool Availability Check

```bash
check_tool() {
    local tool="$1"
    local display="${2:-$1}"
    if ! command -v "$tool" &>/dev/null; then
        echo ""
        echo "ERROR: $display not found."
        echo "  Install it and re-run this script."
        echo "  If using a virtual environment, ensure it is activated."
        exit 2
    fi
}

# Usage examples:
# check_tool pytest "pytest (pip install pytest)"
# check_tool mutmut "mutmut (pip install mutmut)"
# check_tool npx "npx (install Node.js)"
```

```powershell
function Test-Tool {
    param([string]$Name, [string]$Display)
    if (-not $Display) { $Display = $Name }
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Host ""
        Write-Host "ERROR: $Display not found."
        Write-Host "  Install it and re-run this script."
        exit 2
    }
}

# Usage:
# Test-Tool "pytest" "pytest (pip install pytest)"
# Test-Tool "mutmut" "mutmut (pip install mutmut)"
```

### Structured Output Parsing

```bash
# --- Parse pytest coverage output ---
parse_pytest_coverage() {
    local output="$1"
    local total_line
    total_line=$(echo "$output" | grep "^TOTAL" || true)
    if [ -n "$total_line" ]; then
        echo "$total_line"
    fi
}
```

```bash
# --- Parse mutmut results ---
parse_mutmut_results() {
    mutmut results 2>/dev/null | tail -5
    echo ""
    echo "For details: mutmut results"
    echo "To inspect a mutant: mutmut show <id>"
}
```

```bash
# --- Parse stryker results ---
parse_stryker_results() {
    if [ -f "reports/mutation/mutation.json" ]; then
        echo "Report: reports/mutation/html/index.html"
    fi
}
```

### Graceful Failure Recording

```bash
record_test_failure() {
    local component="$1"
    local timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo ""
    echo "=== TEST ENVIRONMENT FAILED: $component ==="
    echo "Please fix the issue and re-run this script."
    echo ""
    if [ -f "task-progress.md" ]; then
        printf "\n### Test Environment Failure — %s\n- **Component**: %s\n- **Action required**: Manual fix\n" \
            "$timestamp" "$component" >> task-progress.md
    fi
}
```

```powershell
function Record-TestFailure($Component) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host ""
    Write-Host "=== TEST ENVIRONMENT FAILED: $Component ==="
    Write-Host "Please fix the issue and re-run this script."
    Write-Host ""
    $progressFile = Join-Path $PSScriptRoot "task-progress.md"
    if (Test-Path $progressFile) {
        Add-Content $progressFile "`n### Test Environment Failure - $timestamp`n- **Component**: $Component`n- **Action required**: Manual fix"
    }
}
```

### Retry Logic (for flaky test environments)

```bash
run_with_retry() {
    local name="$1" max_attempts="${2:-2}" attempt=1
    shift 2
    while [ "$attempt" -le "$max_attempts" ]; do
        echo "Running $name (attempt $attempt/$max_attempts)..."
        if "$@"; then
            return 0
        fi
        local exit_code=$?
        # Only retry on environment errors (exit 2), not test failures (exit 1)
        if [ "$exit_code" -ne 2 ]; then
            return "$exit_code"
        fi
        echo "  Environment issue detected, retrying..."
        attempt=$((attempt + 1))
    done
    echo "ERROR: $name failed after $max_attempts attempts."
    return 2
}
```

---

## Per-Tech-Stack Test Recipes

### Python (pytest / pytest-cov)

```bash
# --- Tool Check ---
check_tool pytest "pytest (pip install pytest)"

# --- Test Mode ---
case "$MODE" in
  --coverage)
    check_tool pytest "pytest-cov (pip install pytest-cov)"
    pytest --cov=src --cov-branch --cov-report=term-missing
    EXIT_CODE=$?
    ;;
  *)
    pytest
    EXIT_CODE=$?
    ;;
esac
```

```powershell
# --- Test Mode ---
switch ($Mode) {
    "--coverage" {
        Test-Tool "pytest" "pytest-cov (pip install pytest-cov)"
        pytest --cov=src --cov-branch --cov-report=term-missing
    }
    default {
        Test-Tool "pytest" "pytest (pip install pytest)"
        pytest
    }
}
```

### Java (JUnit / JaCoCo via Maven)

```bash
# --- Tool Check ---
if [ -f "mvnw" ]; then
    MVN="./mvnw"
elif command -v mvn &>/dev/null; then
    MVN="mvn"
else
    echo "ERROR: Maven not found (no mvnw wrapper and mvn not in PATH)"
    exit 2
fi

# --- Test Mode ---
case "$MODE" in
  --coverage)
    $MVN test jacoco:report
    EXIT_CODE=$?
    echo ""
    echo "Coverage report: target/site/jacoco/index.html"
    ;;
  *)
    $MVN test
    EXIT_CODE=$?
    ;;
esac
```

### JavaScript (Jest / c8)

```bash
# --- Tool Check ---
check_tool npx "npx (install Node.js)"

# --- Test Mode ---
case "$MODE" in
  --coverage)
    npx c8 --branches 80 --lines 90 --reporter=text npx jest
    EXIT_CODE=$?
    ;;
  *)
    npx jest
    EXIT_CODE=$?
    ;;
esac
```

### TypeScript (Vitest / c8)

```bash
# --- Tool Check ---
check_tool npx "npx (install Node.js)"

# --- Test Mode ---
case "$MODE" in
  --coverage)
    npx vitest run --coverage
    EXIT_CODE=$?
    ;;
  *)
    npx vitest run
    EXIT_CODE=$?
    ;;
esac
```

### C / C++ (CTest / gcov+lcov)

```bash
# --- Tool Check ---
check_tool cmake "cmake"
check_tool ctest "ctest (part of cmake)"

# --- Build for Testing ---
BUILD_DIR="${BUILD_DIR:-build}"
if [ ! -d "$BUILD_DIR" ]; then
    echo "Building project..."
    cmake -S . -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Debug
    cmake --build "$BUILD_DIR" --parallel
fi

# --- Test Mode ---
case "$MODE" in
  --coverage)
    check_tool gcov "gcov"
    check_tool lcov "lcov (apt install lcov)"
    # Rebuild with coverage flags
    cmake -S . -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_FLAGS="--coverage" -DCMAKE_CXX_FLAGS="--coverage"
    cmake --build "$BUILD_DIR" --parallel
    ctest --test-dir "$BUILD_DIR" --output-on-failure
    EXIT_CODE=$?
    # Generate coverage report
    lcov --capture --directory "$BUILD_DIR" --output-file coverage.info --quiet
    lcov --summary coverage.info
    ;;
  *)
    ctest --test-dir "$BUILD_DIR" --output-on-failure
    EXIT_CODE=$?
    ;;
esac
```

---

## Per-Tech-Stack Mutation Recipes

### Python (mutmut)

```bash
# --- Tool Check ---
check_tool mutmut "mutmut (pip install mutmut)"

# --- Mutation Mode ---
case "$MODE" in
  --incremental)
    mutmut run --paths-to-mutate="$CHANGED_FILES"
    EXIT_CODE=$?
    ;;
  --full)
    mutmut run
    EXIT_CODE=$?
    ;;
esac

# --- Results ---
echo ""
echo "--- Mutation Results ---"
mutmut results 2>/dev/null || true
echo ""
echo "To inspect a surviving mutant: mutmut show <id>"
```

```powershell
# --- Mutation Mode ---
switch ($Mode) {
    "--incremental" {
        Test-Tool "mutmut" "mutmut (pip install mutmut)"
        mutmut run --paths-to-mutate="$ChangedFiles"
    }
    "--full" {
        Test-Tool "mutmut" "mutmut (pip install mutmut)"
        mutmut run
    }
}

# --- Results ---
Write-Host "`n--- Mutation Results ---"
mutmut results 2>$null
Write-Host "`nTo inspect a surviving mutant: mutmut show <id>"
```

### Java (PIT / pitest via Maven)

```bash
# --- Tool Check ---
if [ -f "mvnw" ]; then
    MVN="./mvnw"
elif command -v mvn &>/dev/null; then
    MVN="mvn"
else
    echo "ERROR: Maven not found"
    exit 2
fi

# --- Mutation Mode ---
case "$MODE" in
  --incremental)
    $MVN pitest:mutationCoverage -DtargetClasses="$CHANGED_FILES"
    EXIT_CODE=$?
    ;;
  --full)
    $MVN pitest:mutationCoverage
    EXIT_CODE=$?
    ;;
esac

# --- Results ---
echo ""
echo "--- Mutation Results ---"
echo "Report: target/pit-reports/*/index.html"
```

### JavaScript / TypeScript (Stryker)

```bash
# --- Tool Check ---
check_tool npx "npx (install Node.js)"

# --- Mutation Mode ---
case "$MODE" in
  --incremental)
    npx stryker run --mutate="$CHANGED_FILES"
    EXIT_CODE=$?
    ;;
  --full)
    npx stryker run
    EXIT_CODE=$?
    ;;
esac

# --- Results ---
echo ""
echo "--- Mutation Results ---"
if [ -f "reports/mutation/html/index.html" ]; then
    echo "Report: reports/mutation/html/index.html"
fi
```

### C / C++ (Mull)

```bash
# --- Tool Check ---
check_tool mull-runner "mull-runner (install Mull)"

# --- Ensure test binary exists ---
TEST_BIN="${TEST_BIN:-build/test-binary}"
if [ ! -f "$TEST_BIN" ]; then
    echo "ERROR: Test binary not found at $TEST_BIN"
    echo "  Build with: cmake --build build/"
    exit 2
fi

# --- Mutation Mode ---
case "$MODE" in
  --incremental)
    mull-runner "$TEST_BIN" --filters="$CHANGED_FILES"
    EXIT_CODE=$?
    ;;
  --full)
    mull-runner "$TEST_BIN"
    EXIT_CODE=$?
    ;;
esac

# --- Results ---
echo ""
echo "--- Mutation Results ---"
if [ -f "mull-report.json" ]; then
    cat mull-report.json
fi
```

---

## Self-Repair Protocol

When `test.sh` or `mutate.sh` exits with code 2 (tool/environment error), the Worker should follow this protocol:

```
1. READ error output — identify the specific tool or environment issue
2. DIAGNOSE root cause:
   - Tool not installed → attempt: pip install / npm install / mvn dependency
   - Environment not activated → check init.sh ran successfully
   - Wrong path → check project structure matches design doc
   - Missing config → run Config Gate to collect missing values
3. ATTEMPT FIX — make one targeted change (install tool, fix path, activate env)
4. RE-RUN — execute the script again
5. IF STILL FAILS → escalate to user via AskUserQuestion:
   "test.sh/mutate.sh failed with: <error message>.
    I attempted to fix by: <what was tried>.
    Please resolve this manually and confirm when ready."
6. NEVER SKIP — testing is a hard gate; no bypass allowed
```

**Red flags:**
| Rationalization | Correct Action |
|---|---|
| "Tool not found, skip mutation testing" | Install tool or ask user |
| "Environment issue, run tests directly" | Fix environment, use script |
| "Script failed, try raw command instead" | Fix script first; raw command = same issue |

---

## CLI / Library Projects (Minimal Scripts)

For projects where UT or mutation testing is not applicable:

```bash
#!/usr/bin/env bash
echo "No tests configured — see feature-list.json tech_stack"
exit 0
```

```powershell
Write-Host "No tests configured — see feature-list.json tech_stack"
exit 0
```

---

## Selection Guide

| Tech Stack in feature-list.json | test.sh Recipe | mutate.sh Recipe |
|---|---|---|
| `pytest` + `pytest-cov` | Python test recipe | Python mutmut recipe |
| `junit` + `jacoco` | Java Maven recipe | Java pitest recipe |
| `jest` + `c8` | JavaScript jest recipe | JS/TS stryker recipe |
| `vitest` + `c8` | TypeScript vitest recipe | JS/TS stryker recipe |
| `ctest` / `gtest` + `gcov` | C/C++ ctest recipe | C/C++ mull recipe |

## Combining with start.sh

If the project has runtime services needed for integration tests:
- `test.sh` should NOT start services — that's `start.sh`'s job
- `test.sh` may check if required services are running (via health check) and warn if not
- Worker orchestration ensures `start.sh` runs before `test.sh`

## Windows / PowerShell Considerations

### Virtual Environment Activation

```powershell
# Python venv on Windows uses a different activation path:
$venvActivate = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
}
# NOT: source .venv/bin/activate (that's Unix-only)
```

### Exit Code Handling

```powershell
# PowerShell does not propagate exit codes automatically from native commands.
# Always check $LASTEXITCODE after running external tools:
pytest --cov=src --cov-branch
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed with exit code: $LASTEXITCODE"
    exit $LASTEXITCODE
}
```
