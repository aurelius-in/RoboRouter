from __future__ import annotations

from typing import Any, Dict, List

from ..utils.tracing import span


class OrchestratorStub:
    """Minimal orchestrator placeholder.

    Plans and reports steps without altering execution.
    """

    def plan(self, steps: List[str]) -> List[str]:  # type: ignore[type-arg]
        return steps

    def run(self, scene_id: str, steps: List[str]) -> Dict[str, Any]:  # type: ignore[type-arg]
        with span("orchestrator.plan"):
            plan = self.plan(steps)
        return {"engine": "stub", "plan": plan}


