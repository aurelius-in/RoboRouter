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

    class Config:
        env_prefix = "ROBOROUTER_"


settings = Settings()


