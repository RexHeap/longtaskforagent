#!/usr/bin/env python3
"""
Validate LLM-generated test/mutation scripts for structural completeness.

Checks that test.sh/test.ps1 and mutate.sh/mutate.ps1 contain all required
operational patterns: environment loading, tool checks, coverage support,
mutation modes, exit code handling, and error handling.

Does NOT check functional correctness — only that required patterns are present.

Usage:
    python validate_test_mutation.py <test-script> <mutate-script>
    python validate_test_mutation.py <test-script> <mutate-script> --powershell <test.ps1> <mutate.ps1>

Exit codes:
    0 — all required patterns present
    1 — one or more required patterns missing
"""

import argparse
import re
import sys


# --- Test script checks ---
# Each is (label, list of alternative regex patterns).
# Passes if at least ONE pattern from each group is found (case-insensitive).
TEST_CHECKS = [
    ("Environment loading (.env)",
     [r"\.env", r"source .env", r"set -a", r"dotenv",
      r"Get-Content.*\.env", r"DOTENV"]),
    ("Environment activation",
     [r"activate", r"conda activate", r"nvm use", r"sdkman",
      r"source .venv", r"\.venv", r"fnm use", r"volta",
      r"Activate\.ps1", r"VIRTUAL_ENV"]),
    ("Tool availability check",
     [r"command -v", r"\bwhich\b", r"Get-Command", r"check_tool",
      r"Test-Tool", r"tool.*not found", r"not found.*exit 2",
      r"exit 2"]),
    ("Test execution command",
     [r"\bpytest\b", r"mvn test", r"mvnw.*test", r"gradlew.*test",
      r"npx jest", r"npx vitest", r"\bctest\b", r"npm test",
      r"npm run test", r"go test"]),
    ("Coverage mode support",
     [r"--cov", r"--coverage", r"jacoco", r"\bgcov\b", r"\blcov\b",
      r"\bc8\b", r"istanbul", r"nyc", r"coverage"]),
    ("Exit code handling",
     [r"exit 0", r"exit 1", r"exit 2", r"\$LASTEXITCODE", r"\$\?",
      r"EXIT_CODE", r"exit_code"]),
    ("Error handling",
     [r"set -e", r"pipefail", r"ErrorActionPreference",
      r"\btrap\b", r"\btry\b", r"\bcatch\b", r"set -u"]),
]

# --- Mutation script checks ---
MUTATE_CHECKS = [
    ("Environment loading (.env)",
     [r"\.env", r"source .env", r"set -a", r"dotenv",
      r"Get-Content.*\.env", r"DOTENV"]),
    ("Environment activation",
     [r"activate", r"conda activate", r"nvm use", r"sdkman",
      r"source .venv", r"\.venv", r"fnm use", r"volta",
      r"Activate\.ps1", r"VIRTUAL_ENV"]),
    ("Tool availability check",
     [r"command -v", r"\bwhich\b", r"Get-Command", r"check_tool",
      r"Test-Tool", r"tool.*not found", r"not found.*exit 2",
      r"exit 2"]),
    ("Mutation tool command",
     [r"\bmutmut\b", r"\bpitest\b", r"\bstryker\b", r"\bmull\b",
      r"mull-runner", r"mutation"]),
    ("Incremental mode support",
     [r"--paths-to-mutate", r"--mutate", r"targetClasses",
      r"--filters", r"incremental", r"CHANGED_FILES",
      r"changed_files"]),
    ("Full mode support",
     [r"\bfull\b", r"--full", r"mutmut run\b", r"stryker run\b",
      r"pitest:mutationCoverage\b", r"mull-runner"]),
    ("Exit code handling",
     [r"exit 0", r"exit 1", r"exit 2", r"\$LASTEXITCODE", r"\$\?",
      r"EXIT_CODE", r"exit_code"]),
    ("Error handling",
     [r"set -e", r"pipefail", r"ErrorActionPreference",
      r"\btrap\b", r"\btry\b", r"\bcatch\b", r"set -u"]),
]

# --- Minimal script detection ---
MINIMAL_PATTERN = r"no.?tests?.?configured|no.?mutation.?configured|no.?tests?.?needed|cli.?only|library.?only"


def validate_test_script(path: str) -> list[str]:
    """Validate a test script for required patterns. Returns list of errors."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"Test script not found: {path}"]
    except Exception as e:
        return [f"Cannot read test script: {e}"]

    if not content.strip():
        return [f"Test script is empty: {path}"]

    # Check for minimal/CLI-only script — skip all checks
    if re.search(MINIMAL_PATTERN, content, re.IGNORECASE):
        return []

    for label, patterns in TEST_CHECKS:
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        if not found:
            errors.append(f"Test script missing: {label}")

    return errors


def validate_mutate_script(path: str, test_content: str = None) -> list[str]:
    """Validate a mutation script for required patterns. Returns list of errors."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"Mutation script not found: {path}"]
    except Exception as e:
        return [f"Cannot read mutation script: {e}"]

    if not content.strip():
        return [f"Mutation script is empty: {path}"]

    # Check for minimal/CLI-only script — skip all checks
    if re.search(MINIMAL_PATTERN, content, re.IGNORECASE):
        return []

    for label, patterns in MUTATE_CHECKS:
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        if not found:
            errors.append(f"Mutation script missing: {label}")

    # Sanity check: mutation script should not be identical to test script
    if test_content and content.strip() == test_content.strip():
        errors.append("Mutation script is identical to test script")

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
        description="Validate LLM-generated test/mutation scripts"
    )
    parser.add_argument("test_script", help="Path to test.sh or test.ps1")
    parser.add_argument("mutate_script", help="Path to mutate.sh or mutate.ps1")
    parser.add_argument(
        "--powershell", nargs=2, metavar=("TEST_PS1", "MUTATE_PS1"),
        help="Additionally validate PowerShell variants"
    )
    args = parser.parse_args()

    all_errors = []

    # Validate bash/main scripts
    test_errors = validate_test_script(args.test_script)
    all_errors.extend(test_errors)

    test_content = read_file_content(args.test_script)
    mutate_errors = validate_mutate_script(args.mutate_script, test_content)
    all_errors.extend(mutate_errors)

    # Validate PowerShell variants if provided
    if args.powershell:
        ps_test, ps_mutate = args.powershell
        ps_test_errors = validate_test_script(ps_test)
        all_errors.extend([f"(PowerShell) {e}" for e in ps_test_errors])

        ps_test_content = read_file_content(ps_test)
        ps_mutate_errors = validate_mutate_script(ps_mutate, ps_test_content)
        all_errors.extend([f"(PowerShell) {e}" for e in ps_mutate_errors])

    # Report
    total_checks = len(TEST_CHECKS) + len(MUTATE_CHECKS)
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
