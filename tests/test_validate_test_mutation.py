#!/usr/bin/env python3
"""
Unit tests for validate_test_mutation.py
"""

import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_test_mutation.py")


def write_temp(content, suffix=".sh"):
    """Write content to a temp file, return path. Caller must unlink."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.flush()
    f.close()
    return f.name


def run_validator(test_content, mutate_content, ps_test=None, ps_mutate=None):
    """Run validate_test_mutation.py with temp files. Returns (exit_code, stdout, stderr)."""
    test_path = write_temp(test_content, ".sh")
    mutate_path = write_temp(mutate_content, ".sh")
    ps_test_path = write_temp(ps_test, ".ps1") if ps_test else None
    ps_mutate_path = write_temp(ps_mutate, ".ps1") if ps_mutate else None

    try:
        cmd = [sys.executable, SCRIPT_PATH, test_path, mutate_path]
        if ps_test_path and ps_mutate_path:
            cmd.extend(["--powershell", ps_test_path, ps_mutate_path])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(test_path)
        os.unlink(mutate_path)
        if ps_test_path:
            os.unlink(ps_test_path)
        if ps_mutate_path:
            os.unlink(ps_mutate_path)


# --- Complete valid scripts ---

VALID_TEST = """#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== MyProject Test Runner ==="

# --- Phase 1: Environment ---
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "Loaded .env"
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated .venv"
fi

# --- Phase 2: Tool Check ---
check_tool() {
    local tool="$1"
    if ! command -v "$tool" &>/dev/null; then
        echo "ERROR: $tool not found."
        exit 2
    fi
}
check_tool pytest

# --- Phase 3: Execute ---
MODE="${1:-test}"
case "$MODE" in
  --coverage)
    echo "Running tests with coverage..."
    pytest --cov=src --cov-branch --cov-report=term-missing
    EXIT_CODE=$?
    ;;
  *)
    echo "Running full test suite..."
    pytest
    EXIT_CODE=$?
    ;;
esac

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "=== Tests Passed ==="
else
    echo "=== Tests Failed (exit code: $EXIT_CODE) ==="
fi
exit "$EXIT_CODE"
"""

VALID_MUTATE = """#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== MyProject Mutation Testing ==="

# --- Phase 1: Environment ---
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "Loaded .env"
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated .venv"
fi

# --- Phase 2: Tool Check ---
check_tool() {
    local tool="$1"
    if ! command -v "$tool" &>/dev/null; then
        echo "ERROR: $tool not found."
        exit 2
    fi
}
check_tool mutmut

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
    mutmut run --paths-to-mutate="$CHANGED_FILES"
    EXIT_CODE=$?
    ;;
  --full)
    echo "Running full mutation testing..."
    mutmut run
    EXIT_CODE=$?
    ;;
  *)
    echo "Usage: ./mutate.sh [--incremental <files>|--full]"
    exit 2
    ;;
esac

# --- Results ---
echo ""
echo "--- Mutation Results ---"
mutmut results 2>/dev/null || true

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "=== Mutation Testing Passed ==="
else
    echo "=== Mutation Testing Failed (exit code: $EXIT_CODE) ==="
fi
exit "$EXIT_CODE"
"""


# --- Tests ---

def test_valid_scripts_pass():
    """Complete test and mutation scripts should pass validation."""
    code, stdout, _ = run_validator(VALID_TEST, VALID_MUTATE)
    assert code == 0, f"Expected exit 0 for valid scripts: {stdout}"
    assert "VALID" in stdout


def test_empty_test_script_fails():
    """An empty test script should fail."""
    code, stdout, _ = run_validator("", VALID_MUTATE)
    assert code != 0, f"Expected non-zero for empty test script: {stdout}"
    assert "empty" in stdout.lower()


def test_empty_mutate_script_fails():
    """An empty mutation script should fail."""
    code, stdout, _ = run_validator(VALID_TEST, "")
    assert code != 0, f"Expected non-zero for empty mutation script: {stdout}"
    assert "empty" in stdout.lower()


def test_missing_env_loading_fails():
    """Test script without .env loading should fail."""
    test = VALID_TEST.replace(".env", ".config_file")
    test = test.replace("dotenv", "configloader")
    test = test.replace("DOTENV", "CONFIGLOADER")
    test = test.replace("set -a", "set -x")
    code, stdout, _ = run_validator(test, VALID_MUTATE)
    assert code != 0, f"Expected non-zero for missing env loading: {stdout}"
    assert "Environment loading" in stdout


def test_missing_env_activation_fails():
    """Test script without environment activation should fail."""
    test = VALID_TEST.replace("activate", "prepare_env")
    test = test.replace("Activate", "Prepare_env")
    test = test.replace("Activated", "Prepared")
    test = test.replace(".venv", ".virtual")
    test = test.replace("VIRTUAL_ENV", "MY_ENV")
    test = test.replace("conda", "package_mgr")
    test = test.replace("nvm", "node_mgr")
    code, stdout, _ = run_validator(test, VALID_MUTATE)
    assert code != 0, f"Expected non-zero for missing env activation: {stdout}"
    assert "Environment activation" in stdout


def test_missing_tool_check_fails():
    """Test script without tool availability check should fail."""
    test = VALID_TEST.replace("command -v", "find_tool")
    test = test.replace("check_tool", "verify_dep")
    test = test.replace("exit 2", "exit 99")
    test = test.replace("$tool not found", "$tool unavailable")
    test = test.replace("not found", "unavailable")
    code, stdout, _ = run_validator(test, VALID_MUTATE)
    assert code != 0, f"Expected non-zero for missing tool check: {stdout}"
    assert "Tool availability" in stdout


def test_missing_test_command_fails():
    """Test script without test execution command should fail."""
    test = VALID_TEST.replace("pytest", "run_checks")
    code, stdout, _ = run_validator(test, VALID_MUTATE)
    assert code != 0, f"Expected non-zero for missing test command: {stdout}"
    assert "Test execution" in stdout


def test_missing_coverage_mode_fails():
    """Test script without coverage support should fail."""
    test = VALID_TEST.replace("--cov", "--metrics")
    test = test.replace("coverage", "analysis")
    code, stdout, _ = run_validator(test, VALID_MUTATE)
    assert code != 0, f"Expected non-zero for missing coverage: {stdout}"
    assert "Coverage mode" in stdout


def test_missing_exit_code_handling_fails():
    """Test script without exit code handling should fail."""
    test = VALID_TEST.replace("exit 0", "done 0")
    test = test.replace("exit 1", "done 1")
    test = test.replace("exit 2", "done 2")
    test = test.replace("EXIT_CODE", "RESULT_VALUE")
    test = test.replace("exit_code", "result_value")
    test = test.replace("$?", "$RESULT")
    test = test.replace("$LASTEXITCODE", "$RESULTCODE")
    code, stdout, _ = run_validator(test, VALID_MUTATE)
    assert code != 0, f"Expected non-zero for missing exit codes: {stdout}"
    assert "Exit code" in stdout


def test_missing_error_handling_fails():
    """Test script without error handling should fail."""
    test = VALID_TEST.replace("set -euo pipefail", "# no error handling")
    test = test.replace("set -e", "# no e")
    test = test.replace("set -u", "# no u")
    test = test.replace("pipefail", "nocheck")
    test = test.replace("trap", "handler")
    test = test.replace("try", "attempt_block")
    test = test.replace("catch", "handle_block")
    test = test.replace("ErrorActionPreference", "ErrorMode")
    code, stdout, _ = run_validator(test, VALID_MUTATE)
    assert code != 0, f"Expected non-zero for missing error handling: {stdout}"
    assert "Error handling" in stdout


def test_mutate_missing_tool_command_fails():
    """Mutation script without mutation tool should fail."""
    mutate = VALID_MUTATE.replace("mutmut", "test_tool")
    mutate = mutate.replace("mutation", "testing_analysis")
    mutate = mutate.replace("Mutation", "Testing_analysis")
    code, stdout, _ = run_validator(VALID_TEST, mutate)
    assert code != 0, f"Expected non-zero for missing mutation tool: {stdout}"
    assert "Mutation tool" in stdout


def test_mutate_missing_incremental_fails():
    """Mutation script without incremental mode should fail."""
    mutate = VALID_MUTATE.replace("--paths-to-mutate", "--scope")
    mutate = mutate.replace("incremental", "partial_run")
    mutate = mutate.replace("CHANGED_FILES", "TARGET_SCOPE")
    mutate = mutate.replace("changed_files", "target_scope")
    mutate = mutate.replace("--mutate", "--scope")
    mutate = mutate.replace("targetClasses", "scopeClasses")
    mutate = mutate.replace("--filters", "--scope")
    code, stdout, _ = run_validator(VALID_TEST, mutate)
    assert code != 0, f"Expected non-zero for missing incremental: {stdout}"
    assert "Incremental mode" in stdout


def test_mutate_missing_full_mode_fails():
    """Mutation script without full mode should fail."""
    mutate = VALID_MUTATE.replace("--full", "--everything")
    mutate = mutate.replace("full", "everything")
    mutate = mutate.replace("Full", "Everything")
    mutate = mutate.replace("mutmut run", "mutmut check")
    code, stdout, _ = run_validator(VALID_TEST, mutate)
    assert code != 0, f"Expected non-zero for missing full mode: {stdout}"
    assert "Full mode" in stdout


def test_identical_scripts_fails():
    """Mutation script identical to test script should fail."""
    code, stdout, _ = run_validator(VALID_TEST, VALID_TEST)
    assert code != 0, f"Expected non-zero for identical scripts: {stdout}"
    assert "identical" in stdout.lower()


def test_minimal_cli_project_passes():
    """Minimal scripts for CLI/library projects should pass."""
    minimal_test = """#!/usr/bin/env bash
echo "No tests configured — see feature-list.json tech_stack"
exit 0
"""
    minimal_mutate = """#!/usr/bin/env bash
echo "No mutation configured — see feature-list.json tech_stack"
exit 0
"""
    code, stdout, _ = run_validator(minimal_test, minimal_mutate)
    assert code == 0, f"Expected exit 0 for minimal scripts: {stdout}"


def test_nonexistent_test_file():
    """Validating a nonexistent test file should fail."""
    mutate_path = write_temp(VALID_MUTATE, ".sh")
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, "/nonexistent/test.sh", mutate_path],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "not found" in result.stdout.lower()
    finally:
        os.unlink(mutate_path)


def test_nonexistent_mutate_file():
    """Validating a nonexistent mutation file should fail."""
    test_path = write_temp(VALID_TEST, ".sh")
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, test_path, "/nonexistent/mutate.sh"],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "not found" in result.stdout.lower()
    finally:
        os.unlink(test_path)


def test_powershell_valid_scripts_pass():
    """Valid PowerShell scripts should pass with --powershell flag."""
    ps_test = """
$ErrorActionPreference = "Stop"

# Load .env
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
}

# Activate venv
$venvActivate = ".venv\\Scripts\\Activate.ps1"
if (Test-Path $venvActivate) { & $venvActivate }

# Tool check
if (-not (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: pytest not found"
    exit 2
}

$Mode = if ($args.Count -gt 0) { $args[0] } else { "test" }
switch ($Mode) {
    "--coverage" {
        pytest --cov=src --cov-branch --cov-report=term-missing
    }
    default {
        pytest
    }
}

if ($LASTEXITCODE -eq 0) { Write-Host "=== Tests Passed ===" }
else { exit $LASTEXITCODE }
"""
    ps_mutate = """
$ErrorActionPreference = "Stop"

# Load .env
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
}

# Activate venv
$venvActivate = ".venv\\Scripts\\Activate.ps1"
if (Test-Path $venvActivate) { & $venvActivate }

# Tool check
if (-not (Get-Command mutmut -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: mutmut not found"
    exit 2
}

$Mode = if ($args.Count -gt 0) { $args[0] } else { "--full" }
switch ($Mode) {
    "--incremental" {
        $ChangedFiles = $args[1..($args.Count - 1)] -join ","
        mutmut run --paths-to-mutate="$ChangedFiles"
    }
    "--full" {
        mutmut run
    }
}

if ($LASTEXITCODE -eq 0) { Write-Host "=== Mutation Testing Passed ===" }
else { exit $LASTEXITCODE }
"""
    code, stdout, _ = run_validator(VALID_TEST, VALID_MUTATE, ps_test, ps_mutate)
    assert code == 0, f"Expected exit 0 for valid PowerShell scripts: {stdout}"


def test_error_count_in_output():
    """Output should show count of issues found."""
    test = "#!/usr/bin/env bash\necho hello\n"
    code, stdout, _ = run_validator(test, VALID_MUTATE)
    assert code != 0
    assert "FAILED" in stdout
    assert "issue" in stdout.lower()
