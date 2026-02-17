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


if __name__ == "__main__":
    tests = [
        test_valid_feature_list,
        test_missing_required_field,
        test_invalid_status,
        test_duplicate_ids,
        test_invalid_dependency_reference,
        test_empty_verification_steps,
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
