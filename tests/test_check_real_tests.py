"""Tests for scripts/check_real_tests.py"""

import json
import os
import subprocess
import sys
import textwrap

import pytest

SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "check_real_tests.py"
)


def run_script(feature_list_path, *extra_args):
    """Run check_real_tests.py and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, SCRIPT, feature_list_path] + list(extra_args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def make_feature_list(tmp_path, features=None, real_test=None, language="python"):
    """Create a minimal feature-list.json in tmp_path and return its path."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {"language": language, "test_framework": "pytest",
                       "coverage_tool": "pytest-cov", "mutation_tool": "mutmut"},
        "quality_gates": {"line_coverage_min": 90, "branch_coverage_min": 80,
                          "mutation_score_min": 80},
        "features": features or [],
    }
    if real_test is not None:
        data["real_test"] = real_test

    fl_path = tmp_path / "feature-list.json"
    fl_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(fl_path)


def make_test_file(tmp_path, filename, content):
    """Create a test file in tmp_path/tests/ directory."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    fpath = tests_dir / filename
    fpath.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(fpath)


# --- Basic scenarios ---

class TestNoRealTestConfig:
    """When feature-list.json has no real_test config, defaults are used."""

    def test_no_config_no_features_passes(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[])
        (tmp_path / "tests").mkdir()
        code, out, _ = run_script(fl)
        assert code == 0
        assert "PASS" in out

    def test_no_config_with_features_no_test_dir_fails(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        # No tests/ directory
        code, out, _ = run_script(fl)
        assert code == 1
        assert "FAIL" in out


class TestRealTestDiscovery:
    """Marker pattern correctly discovers real tests in test files."""

    def test_finds_real_tests_by_marker(self, tmp_path):
        make_test_file(tmp_path, "test_auth.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_db_connection():
                assert True

            def test_normal_unit():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Real tests found: 1" in out
        assert "test_real_db_connection" in out
        assert "PASS" in out

    def test_finds_real_tests_by_comment_label(self, tmp_path):
        make_test_file(tmp_path, "test_api.py", """
            # [real-test] config — reads actual .env.test
            def test_real_config_loaded():
                assert True

            def test_normal():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ], real_test={
            "marker_pattern": "real.test",
            "mock_patterns": [],
            "test_dir": "tests"
        })
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Real tests found: 1" in out

    def test_finds_real_tests_by_function_name(self, tmp_path):
        make_test_file(tmp_path, "test_feature.py", """
            def test_real_test_db_persist():
                assert True

            def test_unit_logic():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Real tests found: 1" in out
        assert "test_real_test_db_persist" in out

    def test_no_real_tests_with_active_features_fails(self, tmp_path):
        make_test_file(tmp_path, "test_stuff.py", """
            def test_normal():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 1
        assert "FAIL" in out
        assert "No real tests found" in out


class TestMockWarnings:
    """Mock patterns correctly flagged as warnings in real test bodies."""

    def test_mock_in_real_test_warns(self, tmp_path):
        make_test_file(tmp_path, "test_service.py", """
            from unittest.mock import MagicMock
            import pytest

            @pytest.mark.real_test
            def test_real_api_call():
                client = MagicMock()
                client.get.return_value = {"ok": True}
                assert client.get()["ok"] is True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 2  # WARN
        assert "WARN" in out
        assert "Mock warnings" in out
        assert "MagicMock" in out

    def test_mock_patch_in_real_test_warns(self, tmp_path):
        make_test_file(tmp_path, "test_config.py", """
            from unittest import mock
            import pytest

            @pytest.mark.real_test
            def test_real_config():
                with mock.patch("os.getenv", return_value="test_key"):
                    pass
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 2
        assert "mock\\.patch" in out or "mock.patch" in out

    def test_no_mock_in_real_test_passes(self, tmp_path):
        make_test_file(tmp_path, "test_clean.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_db():
                # No mock usage here — truly real
                result = 1 + 1
                assert result == 2
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "PASS" in out

    def test_mock_in_regular_test_not_flagged(self, tmp_path):
        """Mock in a non-real test should not generate warnings."""
        make_test_file(tmp_path, "test_mixed.py", """
            from unittest.mock import MagicMock
            import pytest

            @pytest.mark.real_test
            def test_real_clean():
                assert True

            def test_normal_with_mock():
                m = MagicMock()
                assert m is not None
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Mock warnings" not in out


class TestFeatureFiltering:
    """--feature flag filters to specific feature."""

    def test_feature_filter(self, tmp_path):
        make_test_file(tmp_path, "test_auth.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_auth():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
            {"id": 2, "category": "core", "title": "F2", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
        ])
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 0
        assert "Active features: 1" in out

    def test_feature_filter_nonexistent(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
        ])
        (tmp_path / "tests").mkdir()
        code, out, _ = run_script(fl, "--feature", "99")
        assert code == 1
        assert "not found" in out


class TestDeprecatedFeatures:
    """Deprecated features are excluded from active count."""

    def test_deprecated_excluded(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "passing",
             "verification_steps": ["step1"],
             "deprecated": True, "deprecated_reason": "superseded"},
        ])
        (tmp_path / "tests").mkdir()
        code, out, _ = run_script(fl)
        assert code == 0  # No active features = PASS
        assert "Active features: 0" in out


class TestJsonOutput:
    """--json flag produces valid JSON output."""

    def test_json_output(self, tmp_path):
        make_test_file(tmp_path, "test_x.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_x():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl, "--json")
        assert code == 0
        data = json.loads(out)
        assert data["verdict"] == "PASS"
        assert isinstance(data["real_tests"], list)
        assert len(data["real_tests"]) == 1
        assert data["real_tests"][0]["func_name"] == "test_real_x"


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_missing_feature_list(self, tmp_path):
        code, out, _ = run_script(str(tmp_path / "nonexistent.json"))
        assert code == 1

    def test_invalid_json(self, tmp_path):
        bad_file = tmp_path / "feature-list.json"
        bad_file.write_text("not json", encoding="utf-8")
        code, out, _ = run_script(str(bad_file))
        assert code == 1

    def test_empty_test_dir(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[])
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        code, out, _ = run_script(fl)
        assert code == 0

    def test_invalid_marker_pattern(self, tmp_path):
        """Invalid regex in marker_pattern should not crash."""
        make_test_file(tmp_path, "test_x.py", """
            def test_something():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ], real_test={
            "marker_pattern": "[invalid regex",
            "mock_patterns": [],
            "test_dir": "tests"
        })
        code, out, _ = run_script(fl)
        assert code == 1  # No real tests found with invalid pattern

    def test_custom_test_dir(self, tmp_path):
        """Custom test_dir is respected."""
        custom_dir = tmp_path / "src" / "test"
        custom_dir.mkdir(parents=True)
        test_file = custom_dir / "test_feature.py"
        test_file.write_text(textwrap.dedent("""
            import pytest

            @pytest.mark.real_test
            def test_real_feature():
                assert True
        """), encoding="utf-8")

        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ], real_test={
            "marker_pattern": "real_test",
            "mock_patterns": [],
            "test_dir": "src/test"
        })
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Real tests found: 1" in out
