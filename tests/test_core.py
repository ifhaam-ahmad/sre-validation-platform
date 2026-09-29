"""Portfolio tests for validation platform."""

import json
from pathlib import Path

from packages.k8s_renderer.job_renderer import render_validation_job
from packages.parallel_runner.runner import ParallelValidationRunner, ValidationOutcome
from packages.report_generator.html_report import ValidationReportGenerator
from packages.stream_baseline.baseline import BaselineStore, FlowSnapshot, compare_stream_maps
from packages.tenant_resolver.resolver import TenantTarget, load_tenants_from_json


def test_stream_compare_match():
    r = compare_stream_maps({"a": "OK"}, {"a": "OK"})
    assert r["match"] is True


def test_stream_compare_detects_change():
    r = compare_stream_maps({"a": "OK"}, {"a": "FAIL"})
    assert r["match"] is False
    assert r["summary"]["status_changed"] == 1


def test_baseline_store_roundtrip(tmp_path: Path):
    store = BaselineStore(tmp_path)
    snap = FlowSnapshot("stream", {"s1": "RUNNING"}, "2026-01-01T00:00:00Z")
    store.save_baseline("t1", snap)
    loaded = store.load_baseline("t1", "stream")
    assert loaded is not None
    assert loaded.streams["s1"] == "RUNNING"


def test_parallel_runner(tmp_path: Path):
    tenants = [TenantTarget("t1", "https://example.com", "c1", "staging")]

    def ok(t, d):
        return ValidationOutcome(t, "pass", artifacts_dir=d)

    run = ParallelValidationRunner(workers=1, results_root=tmp_path).run(tenants, ok, execution_id="test")
    assert run.passed == 1


def test_html_report(tmp_path: Path):
    t = TenantTarget("t1", "https://example.com", "cluster-a", "staging")
    from packages.parallel_runner.runner import ValidationRun

    run = ValidationRun("exec-1", outcomes=[ValidationOutcome(t, "pass", detail="ok", duration_sec=1.2)])
    out = ValidationReportGenerator().write(run, tmp_path / "report.html")
    assert "cluster-a" in out.read_text(encoding="utf-8")


def test_k8s_job_render():
    t = TenantTarget("tenant_a", "https://demo.example.com", "c1", "staging")
    doc = render_validation_job(t, execution_id="123")
    assert doc["kind"] == "Job"
    assert "tenant_a" in doc["metadata"]["labels"]["tenant"]


def test_load_tenants_json():
    tenants = load_tenants_from_json(Path("examples/tenants.sample.json"))
    assert len(tenants) >= 3
