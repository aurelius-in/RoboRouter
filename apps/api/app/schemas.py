from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    source_uri: str
    crs: str
    sensor_meta: Optional[Dict[str, Any]] = Field(default=None)


class IngestResponse(BaseModel):
    scene_id: uuid.UUID
    artifact_ids: list[uuid.UUID]
    metrics: Dict[str, float]

class NavigationMapResponse(BaseModel):
    scene_id: uuid.UUID
    artifact_id: uuid.UUID
    metadata: Dict[str, Any]

class NavigationPlanRequest(BaseModel):
    scene_id: uuid.UUID
    start: list[float]
    goal: list[float]
    constraints: Dict[str, Any] | None = None

class NavigationPlanResponse(BaseModel):
    scene_id: uuid.UUID
    route: list[list[float]]
    allowed: bool
    reasons: list[str]
    costs: Dict[str, float]


class ArtifactDTO(BaseModel):
    id: uuid.UUID
    type: str
    uri: str
    created_at: str


class MetricDTO(BaseModel):
    name: str
    value: float
    created_at: str


class AuditDTO(BaseModel):
    id: uuid.UUID
    action: str
    details: Dict[str, Any] | None = None
    created_at: str


class SceneDetail(BaseModel):
    id: uuid.UUID
    source_uri: str
    crs: str
    sensor_meta: Dict[str, Any] | None = None
    created_at: str
    metrics: list[MetricDTO]
    artifacts: list[ArtifactDTO]
    audit: list[AuditDTO]


