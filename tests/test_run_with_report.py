"""Tests for scripts/run_with_report.py — command output capture wrapper."""

import os
import subprocess
import sys
import tempfile

import pytest

SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "scripts", "run_with_report.py"
)


def run_wrapper(report_path, command, tail=None, label=None):
    """Helper to invoke run_with_report.py and return (stdout, exit_code, report_content)."""
    args = [sys.executable, SCRIPT, report_path]
    if tail is not None:
        args += ["--tail", str(tail)]
    if label is not None:
        args += ["--label", label]
    args += ["--"] + command
    result = subprocess.run(args, capture_output=True, text=True)
    report_content = ""
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            report_content = f.read()
    return result.stdout, result.returncode, report_content


class TestPassCase:
    def test_exit_code_zero(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, code, _ = run_wrapper(report, ["echo", "hello"])
        assert code == 0

    def test_stdout_contains_pass(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, _ = run_wrapper(report, ["echo", "hello"])
        assert "PASS" in stdout

    def test_report_file_created(self, tmp_path):
        report = str(tmp_path / "report.txt")
        run_wrapper(report, ["echo", "hello"])
        assert os.path.exists(report)

    def test_report_contains_full_output(self, tmp_path):
        report = str(tmp_path / "report.txt")
        _, _, content = run_wrapper(report, ["echo", "hello"])
        assert "hello" in content

    def test_report_contains_header(self, tmp_path):
        report = str(tmp_path / "report.txt")
        _, _, content = run_wrapper(report, ["echo", "hello"])
        assert content.startswith("# Command:")
        assert "# Exit code: 0" in content


class TestFailCase:
    def test_exit_code_nonzero(self, tmp_path):
        report = str(tmp_path / "report.txt")
        _, code, _ = run_wrapper(report, ["false"])
        assert code != 0

    def test_stdout_contains_fail(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, _ = run_wrapper(report, ["false"])
        assert "FAIL" in stdout

    def test_stdout_contains_read_hint(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, _ = run_wrapper(report, ["false"])
        assert "Read" in stdout
        assert "report.txt" in stdout

    def test_report_file_created_on_fail(self, tmp_path):
        report = str(tmp_path / "report.txt")
        run_wrapper(report, ["false"])
        assert os.path.exists(report)


class TestTailOption:
    def test_default_tail_20(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, _ = run_wrapper(report, ["seq", "1", "50"])
        # Default tail=20, should see "last 20 lines"
        assert "last 20 lines" in stdout

    def test_custom_tail(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, _ = run_wrapper(report, ["seq", "1", "50"], tail=5)
        assert "last 5 lines" in stdout
        # Should contain lines 46-50
        assert "50" in stdout
        assert "46" in stdout

    def test_tail_larger_than_output(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, _ = run_wrapper(report, ["seq", "1", "3"], tail=100)
        # Should show all 3 lines
        assert "last 3 lines" in stdout


class TestLabelOption:
    def test_custom_label(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, _ = run_wrapper(report, ["echo", "ok"], label="coverage-gate")
        assert "[coverage-gate]" in stdout

    def test_default_label_from_filename(self, tmp_path):
        report = str(tmp_path / "my-report.txt")
        stdout, _, _ = run_wrapper(report, ["echo", "ok"])
        assert "[my-report]" in stdout


class TestDirectoryCreation:
    def test_auto_creates_parent_dirs(self, tmp_path):
        report = str(tmp_path / "sub" / "dir" / "report.txt")
        run_wrapper(report, ["echo", "ok"])
        assert os.path.exists(report)


class TestLargeOutput:
    def test_only_tail_in_stdout(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, content = run_wrapper(report, ["seq", "1", "200"], tail=5)
        # stdout should NOT contain line "1\n2\n3..." in full
        stdout_lines = [l for l in stdout.strip().split("\n") if l.strip().isdigit()]
        assert len(stdout_lines) <= 5
        # But report file should have all 200 lines
        assert "200" in content
        assert "# Exit code: 0" in content


class TestStderrCapture:
    def test_stderr_in_report(self, tmp_path):
        report = str(tmp_path / "report.txt")
        # Use python to write to stderr
        cmd = [sys.executable, "-c", "import sys; sys.stderr.write('error msg\\n')"]
        _, _, content = run_wrapper(report, cmd)
        assert "error msg" in content


class TestOverwrite:
    def test_second_run_overwrites(self, tmp_path):
        report = str(tmp_path / "report.txt")
        run_wrapper(report, ["echo", "first"])
        _, _, content = run_wrapper(report, ["echo", "second"])
        assert "second" in content
        assert "first" not in content


class TestMissingSeparator:
    def test_no_separator_exits_2(self):
        """Missing '--' separator should exit with code 2."""
        result = subprocess.run(
            [sys.executable, SCRIPT, "/tmp/r.txt", "echo", "hello"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2

    def test_no_command_after_separator(self, tmp_path):
        """Empty command after '--' should exit with code 2."""
        result = subprocess.run(
            [sys.executable, SCRIPT, str(tmp_path / "r.txt"), "--"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2


class TestReportLineCount:
    def test_line_count_in_stdout(self, tmp_path):
        report = str(tmp_path / "report.txt")
        stdout, _, _ = run_wrapper(report, ["seq", "1", "42"])
        assert "42 lines" in stdout
