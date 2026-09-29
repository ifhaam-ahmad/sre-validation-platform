"""Cluster-grouped HTML validation report generator."""

from __future__ import annotations

import html
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from packages.parallel_runner.runner import ValidationOutcome, ValidationRun


class ValidationReportGenerator:
    STATUS_COLORS = {
        "pass": "#d4edda",
        "fail": "#f8d7da",
        "error": "#fff3cd",
        "skip": "#e2e3e5",
    }

    def render(self, run: ValidationRun) -> str:
        by_cluster: dict[str, List[ValidationOutcome]] = defaultdict(list)
        for outcome in run.outcomes:
            by_cluster[outcome.tenant.cluster_name].append(outcome)

        sections = []
        for cluster in sorted(by_cluster):
            rows = []
            for o in sorted(by_cluster[cluster], key=lambda x: x.tenant.tenant_name):
                color = self.STATUS_COLORS.get(o.status, "#ffffff")
                rows.append(
                    f"<tr style='background:{color}'>"
                    f"<td>{html.escape(o.tenant.tenant_name)}</td>"
                    f"<td>{html.escape(o.tenant.environment)}</td>"
                    f"<td>{html.escape(o.status)}</td>"
                    f"<td>{html.escape(o.detail)}</td>"
                    f"<td>{o.duration_sec:.1f}s</td>"
                    f"</tr>"
                )
            sections.append(
                f"<h2>Cluster: {html.escape(cluster)} ({len(by_cluster[cluster])} tenants)</h2>"
                f"<table border='1' cellpadding='6' cellspacing='0' width='100%'>"
                f"<tr><th>Tenant</th><th>Environment</th><th>Status</th><th>Detail</th><th>Duration</th></tr>"
                f"{''.join(rows)}</table>"
            )

        generated = datetime.now(timezone.utc).isoformat()
        return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>Validation Report {html.escape(run.execution_id)}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; }}
h1 {{ color: #1a365d; }}
.summary {{ background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 20px; }}
</style></head><body>
<h1>Post-Upgrade Validation Report</h1>
<div class='summary'>
  <strong>Execution:</strong> {html.escape(run.execution_id)}<br>
  <strong>Generated:</strong> {generated}<br>
  <strong>Total:</strong> {len(run.outcomes)} |
  <strong style='color:green'>Passed:</strong> {run.passed} |
  <strong style='color:red'>Failed:</strong> {run.failed} |
  <strong style='color:orange'>Errors:</strong> {run.errors}
</div>
{''.join(sections)}
</body></html>"""

    def write(self, run: ValidationRun, output: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.render(run), encoding="utf-8")
        return output
