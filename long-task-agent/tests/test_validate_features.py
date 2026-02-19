#!/usr/bin/env python3
"""
Unit tests for validate_features.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_features.py")


def run_validator(feature_data):
    """Run validate_features.py with given data, return (exit_code, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(feature_data, f, indent=2)
        f.flush()
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path],
            capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(tmp_path)


def test_valid_feature_list():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1,
                "category": "core",
                "title": "Test feature",
                "description": "A test feature",
                "priority": "high",
                "status": "failing",
                "verification_steps": ["Step 1"],
                "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0, got {code}: {stdout}"
    assert "VALID" in stdout


def test_missing_required_field():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1,
                "category": "core",
                "title": "Test feature",
                # Missing: description, priority, status, verification_steps
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit, got {code}: {stdout}"


def test_invalid_status():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1,
                "category": "core",
                "title": "Test feature",
                "description": "A test feature",
                "priority": "high",
                "status": "in-progress",  # Invalid!
                "verification_steps": ["Step 1"],
                "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for invalid status: {stdout}"


def test_duplicate_ids():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            },
            {
                "id": 1, "category": "core", "title": "B",
                "description": "B", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for duplicate IDs: {stdout}"


def test_invalid_dependency_reference():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [99]  # ID 99 doesn't exist
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for invalid dependency: {stdout}"


def test_empty_verification_steps():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": [], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for empty verification_steps: {stdout}"


def test_valid_tech_stack():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {
            "language": "python",
            "test_framework": "pytest",
            "coverage_tool": "pytest-cov",
            "mutation_tool": "mutmut"
        },
        "quality_gates": {
            "line_coverage_min": 90,
            "branch_coverage_min": 80,
            "mutation_score_min": 80
        },
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid tech_stack: {stdout}"
    assert "VALID" in stdout


def test_invalid_language():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {
            "language": "ruby",
            "test_framework": "rspec",
            "coverage_tool": "simplecov",
            "mutation_tool": "mutant"
        },
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for unsupported language: {stdout}"


def test_todo_language_is_valid():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {"language": "TODO"},
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for TODO language: {stdout}"


def test_invalid_quality_gate_value():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "quality_gates": {
            "line_coverage_min": 150,
            "branch_coverage_min": 80,
            "mutation_score_min": 80
        },
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for quality gate > 100: {stdout}"


def test_negative_quality_gate_value():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "quality_gates": {
            "line_coverage_min": -10,
            "branch_coverage_min": 80,
            "mutation_score_min": 80
        },
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for negative quality gate: {stdout}"


def test_quality_gate_string_value():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "quality_gates": {
            "line_coverage_min": "high",
            "branch_coverage_min": 80,
            "mutation_score_min": 80
        },
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for string quality gate: {stdout}"


def test_all_supported_languages():
    for lang in ["python", "java", "typescript", "c", "cpp", "c++"]:
        data = {
            "project": "test-project",
            "created": "2025-01-01",
            "tech_stack": {"language": lang},
            "features": [
                {
                    "id": 1, "category": "core", "title": "A",
                    "description": "A", "priority": "high", "status": "failing",
                    "verification_steps": ["Step 1"], "dependencies": []
                }
            ]
        }
        code, stdout, _ = run_validator(data)
        assert code == 0, f"Expected exit 0 for language '{lang}': {stdout}"


def test_valid_required_configs():
    """Valid required_configs should pass validation."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "required_configs": [
            {
                "name": "API Key",
                "type": "env",
                "key": "API_KEY",
                "description": "API key for external service",
                "required_by": [1],
                "check_hint": "Get from dashboard"
            },
            {
                "name": "DB Config",
                "type": "file",
                "path": "config/db.yml",
                "description": "Database configuration",
                "required_by": [1, 2],
                "check_hint": "Copy from db.yml.example"
            }
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            },
            {
                "id": 2, "category": "core", "title": "B",
                "description": "B", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid required_configs: {stdout}"


def test_required_configs_invalid_type():
    """Invalid config type should fail validation."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "required_configs": [
            {
                "name": "Bad Config",
                "type": "database",
                "description": "Invalid",
                "required_by": [1]
            }
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for invalid config type: {stdout}"


def test_required_configs_missing_key_for_env():
    """env type config missing 'key' should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "required_configs": [
            {
                "name": "API Key",
                "type": "env",
                "description": "API key",
                "required_by": [1]
            }
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for env missing key: {stdout}"


def test_required_configs_missing_path_for_file():
    """file type config missing 'path' should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "required_configs": [
            {
                "name": "DB Config",
                "type": "file",
                "description": "Database config",
                "required_by": [1]
            }
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for file missing path: {stdout}"


def test_required_configs_invalid_required_by_reference():
    """required_by referencing non-existent feature ID should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "required_configs": [
            {
                "name": "API Key",
                "type": "env",
                "key": "API_KEY",
                "description": "API key",
                "required_by": [99]
            }
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for invalid required_by ref: {stdout}"


def test_required_configs_duplicate_name():
    """Duplicate config names should fail validation."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "required_configs": [
            {
                "name": "API Key",
                "type": "env",
                "key": "KEY_A",
                "description": "First",
                "required_by": [1]
            },
            {
                "name": "API Key",
                "type": "env",
                "key": "KEY_B",
                "description": "Second",
                "required_by": [1]
            }
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for duplicate config names: {stdout}"


def test_required_configs_not_array():
    """required_configs that is not an array should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "required_configs": "not an array",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for non-array required_configs: {stdout}"


def test_empty_required_configs_is_valid():
    """Empty required_configs array should pass validation."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "required_configs": [],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for empty required_configs: {stdout}"


def test_no_required_configs_key_is_valid():
    """Omitting required_configs entirely should pass (backward compat)."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 when required_configs is omitted: {stdout}"


# --- UI field validation tests ---

def test_ui_feature_with_devtools_step_valid():
    """UI feature with [devtools] verification step should pass."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "frontend", "title": "Login Page",
                "description": "Login form", "priority": "high", "status": "failing",
                "verification_steps": [
                    "[devtools] navigate to /login, verify form fields, fill credentials, submit",
                    "Unit test: login logic"
                ],
                "dependencies": [],
                "ui": True,
                "ui_entry": "/login"
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid UI feature: {stdout}"


def test_ui_feature_without_devtools_step_fails():
    """UI feature without any [devtools] verification step should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "frontend", "title": "Login Page",
                "description": "Login form", "priority": "high", "status": "failing",
                "verification_steps": ["Run unit tests", "Check API response"],
                "dependencies": [],
                "ui": True
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for UI feature without [devtools] step: {stdout}"
    assert "[devtools]" in stdout


def test_non_ui_feature_no_devtools_step_ok():
    """Non-UI feature without [devtools] step should pass (no requirement)."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "API endpoint",
                "description": "Backend", "priority": "high", "status": "failing",
                "verification_steps": ["Run unit tests"],
                "dependencies": [],
                "ui": False
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for non-UI feature: {stdout}"


def test_ui_field_not_boolean_fails():
    """ui field that is not boolean should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "frontend", "title": "Page",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"],
                "dependencies": [],
                "ui": "yes"
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for non-boolean ui field: {stdout}"


def test_ui_entry_not_string_fails():
    """ui_entry field that is not a string should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "frontend", "title": "Page",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["[devtools] check page"],
                "dependencies": [],
                "ui": True,
                "ui_entry": 123
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for non-string ui_entry: {stdout}"


def test_feature_without_ui_field_is_valid():
    """Feature without ui field should pass (backward compat)."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 when ui field absent: {stdout}"


def test_devtools_step_case_insensitive():
    """[devtools] prefix should be case-insensitive."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "frontend", "title": "Page",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["[DevTools] Navigate to /page and verify"],
                "dependencies": [],
                "ui": True
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for case-insensitive [DevTools]: {stdout}"


if __name__ == "__main__":
    tests = [
        test_valid_feature_list,
        test_missing_required_field,
        test_invalid_status,
        test_duplicate_ids,
        test_invalid_dependency_reference,
        test_empty_verification_steps,
        test_valid_tech_stack,
        test_invalid_language,
        test_todo_language_is_valid,
        test_invalid_quality_gate_value,
        test_negative_quality_gate_value,
        test_quality_gate_string_value,
        test_all_supported_languages,
        test_valid_required_configs,
        test_required_configs_invalid_type,
        test_required_configs_missing_key_for_env,
        test_required_configs_missing_path_for_file,
        test_required_configs_invalid_required_by_reference,
        test_required_configs_duplicate_name,
        test_required_configs_not_array,
        test_empty_required_configs_is_valid,
        test_no_required_configs_key_is_valid,
        test_ui_feature_with_devtools_step_valid,
        test_ui_feature_without_devtools_step_fails,
        test_non_ui_feature_no_devtools_step_ok,
        test_ui_field_not_boolean_fails,
        test_ui_entry_not_string_fails,
        test_feature_without_ui_field_is_valid,
        test_devtools_step_case_insensitive,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
