"""Capture, store, and compare data-stream baseline snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class FlowSnapshot:
    flow_type: str
    streams: Dict[str, str]
    captured_at: str

    @classmethod
    def from_file(cls, path: Path) -> "FlowSnapshot":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            flow_type=data["flow_type"],
            streams={str(k): str(v) for k, v in data.get("streams", {}).items()},
            captured_at=data.get("captured_at", ""),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "flow_type": self.flow_type,
            "streams": dict(sorted(self.streams.items())),
            "stream_count": len(self.streams),
            "captured_at": self.captured_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def compare_stream_maps(baseline: Dict[str, str], current: Dict[str, str]) -> Dict[str, Any]:
    b = {str(k): str(v) for k, v in baseline.items()}
    c = {str(k): str(v) for k, v in current.items()}
    b_names, c_names = set(b), set(c)

    status_changed = [
        {"name": n, "baseline": b[n], "current": c[n]}
        for n in sorted(b_names & c_names)
        if b[n] != c[n]
    ]
    added = [{"name": n, "current": c[n]} for n in sorted(c_names - b_names)]
    removed = [{"name": n, "baseline": b[n]} for n in sorted(b_names - c_names)]

    return {
        "match": not status_changed and not added and not removed,
        "summary": {
            "baseline_count": len(b),
            "current_count": len(c),
            "unchanged": len(b_names & c_names) - len(status_changed),
            "status_changed": len(status_changed),
            "added": len(added),
            "removed": len(removed),
        },
        "status_changed": status_changed,
        "added": added,
        "removed": removed,
    }


class BaselineStore:
    """File-based baseline storage (swap for MongoDB in production)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def baseline_path(self, tenant: str, flow_type: str) -> Path:
        return self.root / tenant / f"{flow_type}_baseline.json"

    def save_baseline(self, tenant: str, snapshot: FlowSnapshot) -> Path:
        path = self.baseline_path(tenant, snapshot.flow_type)
        snapshot.save(path)
        return path

    def load_baseline(self, tenant: str, flow_type: str) -> FlowSnapshot | None:
        path = self.baseline_path(tenant, flow_type)
        return FlowSnapshot.from_file(path) if path.exists() else None

    def compare_tenant(self, tenant: str, current_dir: Path, flow_types: List[str] | None = None) -> Dict[str, Any]:
        flows = flow_types or ["stream", "orch"]
        results: Dict[str, Any] = {}
        overall_match = True
        for flow in flows:
            current_file = current_dir / f"{flow}_flow_snapshot.json"
            if not current_file.exists():
                results[flow] = {"match": False, "error": "missing current snapshot"}
                overall_match = False
                continue
            current = FlowSnapshot.from_file(current_file)
            baseline = self.load_baseline(tenant, flow)
            if baseline is None:
                results[flow] = {"match": False, "error": "missing baseline"}
                overall_match = False
                continue
            cmp = compare_stream_maps(baseline.streams, current.streams)
            results[flow] = cmp
            overall_match = overall_match and cmp["match"]
        return {"tenant": tenant, "match": overall_match, "flows": results}
