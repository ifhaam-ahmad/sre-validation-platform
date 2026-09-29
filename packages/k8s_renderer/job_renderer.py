"""Render Kubernetes validation Job manifests from tenant templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml
from jinja2 import Template

from packages.tenant_resolver.resolver import TenantTarget

JOB_TEMPLATE = Template("""
apiVersion: batch/v1
kind: Job
metadata:
  name: validation-{{ tenant.tenant_name | replace('_', '-') }}-{{ execution_id }}
  namespace: {{ namespace }}
  labels:
    app: post-upgrade-validation
    tenant: {{ tenant.tenant_name }}
    cluster: {{ tenant.cluster_name }}
spec:
  backoffLimit: 1
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app: post-upgrade-validation
        tenant: {{ tenant.tenant_name }}
    spec:
      restartPolicy: Never
      containers:
        - name: validate
          image: {{ image }}
          env:
            - name: TENANT_NAME
              value: "{{ tenant.tenant_name }}"
            - name: TENANT_URL
              value: "{{ tenant.tenant_url }}"
            - name: CLUSTER_NAME
              value: "{{ tenant.cluster_name }}"
            - name: ENVIRONMENT
              value: "{{ tenant.environment }}"
            - name: BASELINE_MODE
              value: "{{ baseline_mode }}"
          volumeMounts:
            - name: results
              mountPath: /results
      volumes:
        - name: results
          emptyDir: {}
""")


def render_validation_job(
    tenant: TenantTarget,
    *,
    execution_id: str,
    namespace: str = "validation",
    image: str = "ghcr.io/example/validation-platform:latest",
    baseline_mode: str = "compare",
) -> Dict[str, Any]:
    rendered = JOB_TEMPLATE.render(
        tenant=tenant,
        execution_id=execution_id,
        namespace=namespace,
        image=image,
        baseline_mode=baseline_mode,
    )
    return yaml.safe_load(rendered)


def write_job_manifest(tenant: TenantTarget, output_dir: Path, **kwargs: Any) -> Path:
    doc = render_validation_job(tenant, **kwargs)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"job-{tenant.tenant_name}.yaml"
    path.write_text(yaml.dump(doc, sort_keys=False), encoding="utf-8")
    return path
