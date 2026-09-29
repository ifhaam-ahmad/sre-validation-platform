"""Resolve tenant scope for validation runs from JSON or MongoDB filters."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pymongo import MongoClient


@dataclass
class TenantTarget:
    tenant_name: str
    tenant_url: str
    cluster_name: str
    environment: str
    username: str = ""

    @classmethod
    def from_doc(cls, doc: Dict[str, Any]) -> "TenantTarget":
        return cls(
            tenant_name=str(doc.get("tenant_name", "")),
            tenant_url=str(doc.get("tenant_url", "")),
            cluster_name=str(doc.get("cluster_name", "default")),
            environment=str(doc.get("environment", "staging")),
            username=str(doc.get("username", "")),
        )


def load_tenants_from_json(path: Path) -> List[TenantTarget]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [TenantTarget.from_doc(item) for item in data]


def _regex_clause(field: str, values: List[str]) -> Dict[str, Any]:
    return {"$or": [{field: {"$regex": re.escape(v), "$options": "i"}} for v in values]}


class TenantResolver:
    def __init__(self, mongo_uri: str, db_name: str = "validation_platform", collection: str = "tenant_configuration") -> None:
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection = collection

    def resolve(
        self,
        *,
        clusters: Optional[List[str]] = None,
        environments: Optional[List[str]] = None,
        tenant_names: Optional[List[str]] = None,
        enabled_only: bool = True,
    ) -> List[TenantTarget]:
        query: Dict[str, Any] = {}
        if enabled_only:
            query["enabled"] = {"$ne": False}
        if clusters:
            query.update(_regex_clause("cluster_name", clusters))
        if environments:
            query["environment"] = {"$in": environments}
        if tenant_names:
            query["tenant_name"] = {"$in": tenant_names}

        with MongoClient(self.mongo_uri) as client:
            docs = list(client[self.db_name][self.collection].find(query))
        return [TenantTarget.from_doc(d) for d in docs if d.get("tenant_name")]

    def export_report(self, tenants: List[TenantTarget]) -> Dict[str, Any]:
        by_cluster: Dict[str, List[str]] = {}
        for t in tenants:
            by_cluster.setdefault(t.cluster_name, []).append(t.tenant_name)
        return {
            "total": len(tenants),
            "clusters": {k: sorted(v) for k, v in sorted(by_cluster.items())},
        }
