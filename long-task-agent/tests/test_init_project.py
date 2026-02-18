#!/usr/bin/env python3
"""
Unit tests for init_project.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "init_project.py")


def run_init(project_name, output_dir, extra_args=None):
    """Run init_project.py, return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, SCRIPT_PATH, project_name, "--path", output_dir]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_creates_all_artifacts():
    """init_project.py should create all expected files."""
    tmp = tempfile.mkdtemp()
    try:
        code, stdout, _ = run_init("test-project", tmp)
        assert code == 0, f"Expected exit 0, got {code}"

        expected_files = [
            "long-task-guide.md",
            "feature-list.json",
            "task-progress.md",
            "RELEASE_NOTES.md",
            "init.sh",
            "init.ps1",
            os.path.join("examples", "README.md"),
        ]
        for f in expected_files:
            path = os.path.join(tmp, f)
            assert os.path.exists(path), f"Missing: {f}"
    finally:
        shutil.rmtree(tmp)


def test_feature_list_is_valid_json():
    """feature-list.json should be valid JSON with correct structure."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        fl_path = os.path.join(tmp, "feature-list.json")
        with open(fl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "project" in data, "Missing 'project' key"
        assert data["project"] == "test-project"
        assert "features" in data, "Missing 'features' key"
        assert isinstance(data["features"], list)
    finally:
        shutil.rmtree(tmp)


def test_guide_contains_project_name():
    """long-task-guide.md should contain the project name."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("my-awesome-project", tmp)
        guide_path = os.path.join(tmp, "long-task-guide.md")
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "my-awesome-project" in content
    finally:
        shutil.rmtree(tmp)


def test_guide_contains_tdd_workflow():
    """long-task-guide.md should contain TDD workflow steps."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        guide_path = os.path.join(tmp, "long-task-guide.md")
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "TDD Red" in content
        assert "TDD Green" in content
        assert "TDD Refactor" in content
        assert "Code Review" in content or "code review" in content.lower()
    finally:
        shutil.rmtree(tmp)


def test_guide_contains_verification_rules():
    """long-task-guide.md should contain verification enforcement rules."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        guide_path = os.path.join(tmp, "long-task-guide.md")
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Verification enforcement" in content or "verification" in content.lower()
    finally:
        shutil.rmtree(tmp)


def test_scripts_dir_created():
    """scripts/ directory should be created."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        assert os.path.isdir(os.path.join(tmp, "scripts"))
    finally:
        shutil.rmtree(tmp)


def test_examples_dir_created():
    """examples/ directory should be created with README.md."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        assert os.path.isdir(os.path.join(tmp, "examples"))
        readme = os.path.join(tmp, "examples", "README.md")
        assert os.path.exists(readme)
        with open(readme, "r", encoding="utf-8") as f:
            content = f.read()
        assert "test-project" in content
    finally:
        shutil.rmtree(tmp)


def test_feature_list_has_tech_stack():
    """feature-list.json should contain tech_stack with TODO placeholders."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        fl_path = os.path.join(tmp, "feature-list.json")
        with open(fl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "tech_stack" in data, "Missing 'tech_stack' key"
        ts = data["tech_stack"]
        assert ts["language"] == "TODO"
        assert ts["test_framework"] == "TODO"
        assert ts["coverage_tool"] == "TODO"
        assert ts["mutation_tool"] == "TODO"
    finally:
        shutil.rmtree(tmp)


def test_feature_list_has_quality_gates():
    """feature-list.json should contain quality_gates with default thresholds."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        fl_path = os.path.join(tmp, "feature-list.json")
        with open(fl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "quality_gates" in data, "Missing 'quality_gates' key"
        qg = data["quality_gates"]
        assert qg["line_coverage_min"] == 90
        assert qg["branch_coverage_min"] == 80
        assert qg["mutation_score_min"] == 80
    finally:
        shutil.rmtree(tmp)


def test_guide_contains_coverage_gate():
    """long-task-guide.md should contain Coverage Gate step."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        guide_path = os.path.join(tmp, "long-task-guide.md")
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Coverage Gate" in content, "Missing Coverage Gate step"
        assert "pytest --cov" in content, "Missing Python coverage command"
        assert "jacoco" in content, "Missing Java coverage command"
    finally:
        shutil.rmtree(tmp)


def test_guide_contains_mutation_gate():
    """long-task-guide.md should contain Mutation Gate step."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        guide_path = os.path.join(tmp, "long-task-guide.md")
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Mutation Gate" in content, "Missing Mutation Gate step"
        assert "mutmut" in content, "Missing Python mutation command"
        assert "pitest" in content, "Missing Java mutation command"
        assert "stryker" in content, "Missing TypeScript mutation command"
    finally:
        shutil.rmtree(tmp)


def test_lang_preset_fills_tools():
    """--lang python should auto-fill pytest, pytest-cov, mutmut."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp, ["--lang", "python"])
        fl_path = os.path.join(tmp, "feature-list.json")
        with open(fl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data["tech_stack"]
        assert ts["language"] == "python"
        assert ts["test_framework"] == "pytest"
        assert ts["coverage_tool"] == "pytest-cov"
        assert ts["mutation_tool"] == "mutmut"
    finally:
        shutil.rmtree(tmp)


def test_custom_thresholds():
    """--line-cov, --branch-cov, --mutation-score should override defaults."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp, [
            "--lang", "java",
            "--line-cov", "85",
            "--branch-cov", "75",
            "--mutation-score", "70"
        ])
        fl_path = os.path.join(tmp, "feature-list.json")
        with open(fl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        qg = data["quality_gates"]
        assert qg["line_coverage_min"] == 85, f"Expected 85, got {qg['line_coverage_min']}"
        assert qg["branch_coverage_min"] == 75, f"Expected 75, got {qg['branch_coverage_min']}"
        assert qg["mutation_score_min"] == 70, f"Expected 70, got {qg['mutation_score_min']}"
        # Also verify Java preset was applied
        ts = data["tech_stack"]
        assert ts["language"] == "java"
        assert ts["test_framework"] == "junit"
        assert ts["coverage_tool"] == "jacoco"
        assert ts["mutation_tool"] == "pitest"
    finally:
        shutil.rmtree(tmp)


def test_tool_override_with_preset():
    """Explicit --coverage-tool should override the language preset."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp, [
            "--lang", "typescript",
            "--coverage-tool", "nyc"
        ])
        fl_path = os.path.join(tmp, "feature-list.json")
        with open(fl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data["tech_stack"]
        assert ts["language"] == "typescript"
        assert ts["coverage_tool"] == "nyc", f"Expected nyc override, got {ts['coverage_tool']}"
        assert ts["test_framework"] == "vitest"  # from preset
        assert ts["mutation_tool"] == "stryker"   # from preset
    finally:
        shutil.rmtree(tmp)


def test_feature_list_has_required_configs():
    """feature-list.json should contain required_configs as empty array."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        fl_path = os.path.join(tmp, "feature-list.json")
        with open(fl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "required_configs" in data, "Missing 'required_configs' key"
        assert isinstance(data["required_configs"], list)
        assert len(data["required_configs"]) == 0
    finally:
        shutil.rmtree(tmp)


def test_guide_contains_config_gate():
    """long-task-guide.md should contain Config Gate step."""
    tmp = tempfile.mkdtemp()
    try:
        run_init("test-project", tmp)
        guide_path = os.path.join(tmp, "long-task-guide.md")
        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Config Gate" in content, "Missing Config Gate step in guide"
        assert "required_configs" in content, "Guide should reference required_configs"
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    tests = [
        test_creates_all_artifacts,
        test_feature_list_is_valid_json,
        test_guide_contains_project_name,
        test_guide_contains_tdd_workflow,
        test_guide_contains_verification_rules,
        test_scripts_dir_created,
        test_examples_dir_created,
        test_feature_list_has_tech_stack,
        test_feature_list_has_quality_gates,
        test_guide_contains_coverage_gate,
        test_guide_contains_mutation_gate,
        test_lang_preset_fills_tools,
        test_custom_thresholds,
        test_tool_override_with_preset,
        test_feature_list_has_required_configs,
        test_guide_contains_config_gate,
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
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
