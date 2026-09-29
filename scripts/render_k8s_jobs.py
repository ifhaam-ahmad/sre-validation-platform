#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.k8s_renderer.job_renderer import write_job_manifest
from packages.tenant_resolver.resolver import load_tenants_from_json

tenants = load_tenants_from_json(Path("examples/tenants.sample.json"))
out = Path("results/k8s-jobs")
for t in tenants[:2]:
    p = write_job_manifest(t, out, execution_id="demo")
    print("wrote", p)
