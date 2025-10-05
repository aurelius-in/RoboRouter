from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RoboRouter API"

    database_url: str = (
        "postgresql+psycopg2://roborouter:roborouter@postgres:5432/roborouter"
    )

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "adminadmin"
    minio_secure: bool = False
    minio_bucket_raw: str = "roborouter-raw"
    minio_bucket_processed: str = "roborouter-processed"
    presign_expires_seconds: int = 3600

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    api_key: str | None = None
    rate_limit_rpm: int = 120
    retention_days: int = 30

    # Ingest (PDAL) defaults
    ingest_voxel_size_m: float = 0.05
    ingest_outlier_mean_k: int = 8
    ingest_outlier_multiplier: float = 1.0
    ingest_intensity_min: float = 0.0
    ingest_intensity_max: float = 1.0

    # Change detection defaults
    change_voxel_size_m: float = 0.10
    change_min_points_per_voxel: int = 3

    # Registration (Open3D) defaults
    reg_voxel_size_m: float = 0.05
    reg_fgr_max_corr_mult: float = 1.5
    reg_icp_max_iter: int = 50

    # Segmentation (MinkowskiEngine/KPConv)
    seg_use_minkowski: bool = False
    seg_model_path: str | None = None
    seg_num_classes: int = 5

    # Learned change detection
    change_use_learned: bool = False
    change_pose_drift_default: float = 0.05

    # Policy / OPA
    opa_policy_path: str | None = "configs/opa/policy.yaml"

    # Orchestrator
    orchestrator: str = "stub"  # one of: stub, ray, langgraph

    class Config:
        env_prefix = "ROBOROUTER_"


settings = Settings()


