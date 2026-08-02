"""Build logs and structured reports."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Sequence


@dataclass
class Report:
    version: str
    package: str
    stages: list[dict] = field(default_factory=list)
    status: str = "running"

    def stage(self, name: str, status: str, **details) -> None:
        for stage in reversed(self.stages):
            if stage["name"] == name and stage["status"] in {"running", "passed"}:
                stage.update(status=status, **details)
                return
        self.stages.append({"name": name, "status": status, **details})


class Reporter:
    def __init__(self, logs_dir: Path, report_json: Path, report_text: Path, version: str, package: str):
        self.logs_dir = logs_dir
        self.report_json = report_json
        self.report_text = report_text
        self.report = Report(version=version, package=package)

    def start(self) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def stage(self, name: str, status: str, **details) -> None:
        self.report.stage(name, status, **details)

    def command(
        self,
        name: str,
        command: Sequence[str],
        cwd: Path,
        *,
        check: bool = True,
        reject_pattern: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        started = time.monotonic()
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        log_path = self.logs_dir / f"{name}.log"
        log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
        rejected = reject_pattern is not None and re.search(reject_pattern, result.stdout + result.stderr, re.I)
        failed = result.returncode != 0 or rejected
        self.report.stage(name, "failed" if failed else "passed", returncode=result.returncode, log=str(log_path), seconds=round(time.monotonic() - started, 3))
        if check and failed:
            raise RuntimeError(f"{name} failed with exit code {result.returncode}; see {log_path}")
        return result

    def finish(self, status: str, **details) -> None:
        if status == "failed":
            for stage in self.report.stages:
                if stage["status"] == "running":
                    stage.update(status="failed", **details)
        self.report.status = status
        self.report_data = {"status": status, "version": self.report.version, "package": self.report.package, "stages": self.report.stages, **details}
        self.report_json.parent.mkdir(parents=True, exist_ok=True)
        self.report_json.write_text(json.dumps(self.report_data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        lines = [f"status={status}", f"version={self.report.version}", f"package={self.report.package}"]
        for stage in self.report.stages:
            lines.append(f"{stage['name']}={stage['status']}")
        for key, value in details.items():
            lines.append(f"{key}={value}")
        self.report_text.write_text("\n".join(lines) + "\n", encoding="utf-8")
