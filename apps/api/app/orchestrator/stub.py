from __future__ import annotations

from typing import Any, Dict, List

from ..utils.tracing import span
from ..config import settings


class OrchestratorStub:
    """Minimal orchestrator placeholder.

    Plans and reports steps without altering execution.
    """

    def plan(self, steps: List[str]) -> List[str]:  # type: ignore[type-arg]
        return steps

    def run(self, scene_id: str, steps: List[str]) -> Dict[str, Any]:  # type: ignore[type-arg]
        engine = settings.orchestrator
        with span(f"orchestrator.plan.{engine}"):
            plan = self.plan(steps)
        # Stub lineage and retry metadata
        lineage = {"scene_id": scene_id, "steps": plan, "retries": {s: 0 for s in plan}}
        return {"engine": engine, "plan": plan, "lineage": lineage}

    def cancel(self, run_id: str) -> Dict[str, Any]:
        return {"run_id": run_id, "status": "cancelled"}

    def resume(self, run_id: str) -> Dict[str, Any]:
        return {"run_id": run_id, "status": "resumed"}


