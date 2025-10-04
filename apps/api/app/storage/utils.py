from __future__ import annotations

from urllib.parse import urlparse


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse s3://bucket/key URIs.

    Returns (bucket, key).
    """
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path:
        raise ValueError(f"Not an s3 URI: {uri}")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return bucket, key


