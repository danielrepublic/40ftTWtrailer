import json
from pathlib import Path
import sys
import tempfile
import unittest

from tools.build.reporting import Reporter, StageValidationError


class ReportingTests(unittest.TestCase):
    def test_running_stage_is_updated_in_place(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reporter = Reporter(
                root / "logs",
                root / "build-report.json",
                root / "build-report.txt",
                "1.1",
                "tw40ch_v1.1.scs",
            )
            reporter.start()
            reporter.stage("export", "running")
            reporter.stage("export", "passed", output="chassis.pim")
            reporter.finish("success")

            report = json.loads((root / "build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["stages"], [{"name": "export", "status": "passed", "output": "chassis.pim"}])

    def test_failed_report_closes_running_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reporter = Reporter(
                root / "logs",
                root / "build-report.json",
                root / "build-report.txt",
                "1.1",
                "tw40ch_v1.1.scs",
            )
            reporter.start()
            reporter.stage("export", "running")
            reporter.finish("failed", error="MCP unavailable")

            report = json.loads((root / "build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["stages"][0]["status"], "failed")
            self.assertEqual(report["stages"][0]["error"], "MCP unavailable")

    def test_run_stage_rejects_warning_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reporter = Reporter(root / "logs", root / "build-report.json", root / "build-report.txt", "1.1", "tw40ch_v1.1.scs")
            reporter.start()
            with self.assertRaises(RuntimeError):
                reporter.run_stage(
                    "reverse_verify",
                    [sys.executable, "-c", "print('warning: test')"],
                    root,
                    reject_pattern=r"\b(error|warning)\b",
                )
            reporter.finish("failed", error="warning")
            report = json.loads((root / "build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["stages"][0]["status"], "failed")

    def test_validator_details_are_recorded_on_one_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reporter = Reporter(root / "logs", root / "build-report.json", root / "build-report.txt", "1.1", "tw40ch_v1.1.scs")
            reporter.start()

            def validate(_result):
                return {"accepted_warnings": ["accepted warning"]}

            reporter.run_stage(
                "reverse_verify",
                [sys.executable, "-c", "print('warning: accepted')"],
                root,
                validator=validate,
            )
            reporter.finish("success")

            report = json.loads((root / "build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["stages"]), 1)
            self.assertEqual(report["stages"][0]["accepted_warnings"], ["accepted warning"])

    def test_validator_failure_is_recorded_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reporter = Reporter(root / "logs", root / "build-report.json", root / "build-report.txt", "1.1", "tw40ch_v1.1.scs")
            reporter.start()

            def validate(_result):
                raise StageValidationError("invalid reverse verification", unexpected_warnings=["unexpected warning"])

            with self.assertRaises(StageValidationError):
                reporter.run_stage(
                    "reverse_verify",
                    [sys.executable, "-c", "print('warning: unexpected')"],
                    root,
                    validator=validate,
                )
            reporter.finish("failed", error="invalid reverse verification")

            report = json.loads((root / "build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["stages"]), 1)
            self.assertEqual(report["stages"][0]["status"], "failed")
            self.assertEqual(report["stages"][0]["unexpected_warnings"], ["unexpected warning"])

    def test_validator_details_are_combined_with_command_failure_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reporter = Reporter(root / "logs", root / "build-report.json", root / "build-report.txt", "1.1", "tw40ch_v1.1.scs")
            reporter.start()

            def validate(_result):
                raise StageValidationError("invalid reverse verification", unexpected_warnings=["unexpected warning"])

            with self.assertRaises(StageValidationError):
                reporter.run_stage(
                    "reverse_verify",
                    [sys.executable, "-c", "import sys; sys.exit(3)"],
                    root,
                    check=False,
                    validator=validate,
                )
            reporter.finish("failed", error="invalid reverse verification")

            report = json.loads((root / "build-report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["stages"]), 1)
            self.assertEqual(report["stages"][0]["status"], "failed")
            self.assertEqual(report["stages"][0]["returncode"], 3)
            self.assertEqual(report["stages"][0]["unexpected_warnings"], ["unexpected warning"])


if __name__ == "__main__":
    unittest.main()
