"""Wave-based parallel validation runner with result aggregation."""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from packages.tenant_resolver.resolver import TenantTarget

logger = logging.getLogger(__name__)


@dataclass
class ValidationOutcome:
    tenant: TenantTarget
    status: str  # pass | fail | error | skip
    detail: str = ""
    duration_sec: float = 0.0
    artifacts_dir: Optional[Path] = None

    @property
    def passed(self) -> bool:
        return self.status == "pass"


@dataclass
class ValidationRun:
    execution_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    outcomes: List[ValidationOutcome] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for o in self.outcomes if o.passed)

    @property
    def failed(self) -> int:
        return sum(1 for o in self.outcomes if o.status == "fail")

    @property
    def errors(self) -> int:
        return sum(1 for o in self.outcomes if o.status == "error")


class ParallelValidationRunner:
    """
    Execute validation checks across many tenants in controlled waves.
    Mirrors K8s parallel Job deployment with wave size + pause for cluster stability.
    """

    def __init__(
        self,
        workers: int | None = None,
        wave_size: int | None = None,
        wave_pause_sec: float | None = None,
        results_root: Path | None = None,
    ) -> None:
        self.workers = workers or int(os.getenv("VALIDATION_PARALLEL_WORKERS", "5"))
        self.wave_size = wave_size or int(os.getenv("VALIDATION_WAVE_SIZE", "4"))
        self.wave_pause = wave_pause_sec or float(os.getenv("VALIDATION_WAVE_PAUSE_SEC", "2"))
        self.results_root = results_root or Path(os.getenv("RESULTS_ROOT", "results"))

    def _chunks(self, items: List[TenantTarget]) -> List[List[TenantTarget]]:
        return [items[i : i + self.wave_size] for i in range(0, len(items), self.wave_size)]

    def run(
        self,
        tenants: List[TenantTarget],
        check_fn: Callable[[TenantTarget, Path], ValidationOutcome],
        execution_id: str | None = None,
    ) -> ValidationRun:
        exec_id = execution_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run = ValidationRun(execution_id=exec_id)
        base = self.results_root / exec_id
        base.mkdir(parents=True, exist_ok=True)

        for wave_idx, wave in enumerate(self._chunks(tenants), start=1):
            logger.info("Wave %s — %s tenant(s)", wave_idx, len(wave))
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                futures = {
                    pool.submit(check_fn, tenant, base / tenant.tenant_name): tenant
                    for tenant in wave
                }
                for future in as_completed(futures):
                    tenant = futures[future]
                    try:
                        run.outcomes.append(future.result())
                    except Exception as exc:
                        run.outcomes.append(ValidationOutcome(tenant, "error", detail=str(exc)))
            if wave_idx * self.wave_size < len(tenants):
                time.sleep(self.wave_pause)

        summary_path = base / "tenant_results_summary.txt"
        lines = [f"{o.tenant.tenant_name}\t{o.status}\t{o.detail}" for o in run.outcomes]
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return run
