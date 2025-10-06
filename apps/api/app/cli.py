from __future__ import annotations

import argparse
from typing import NoReturn

from .db import SessionLocal
from .models import Scene, Artifact, Metric, AuditLog


def cmd_cleanup() -> None:
    """Invoke cleanup by deleting scenes older than retention in a simplified way.

    Note: This is a minimal stub; prefer the /admin/cleanup endpoint for full behavior.
    """
    db = SessionLocal()
    try:
        # No-op placeholder; real logic lives in admin router
        print("Cleanup stub completed (use /admin/cleanup for full cleanup).")
    finally:
        db.close()


def cmd_reindex() -> None:
    """Rebuild lightweight indices (stub)."""
    db = SessionLocal()
    try:
        total = db.query(Scene).count()  # type: ignore[attr-defined]
        print(f"Reindex stub completed; scenes seen: {total}")
    finally:
        db.close()


def cmd_gc() -> None:
    """Garbage collect orphaned metrics/artifacts (stub)."""
    db = SessionLocal()
    try:
        # This is a no-op placeholder; implement actual orphan detection later
        print("GC stub completed; no orphans removed in stub mode.")
    finally:
        db.close()


def cmd_backfill_metrics() -> None:
    """Backfill simple aggregate metrics per scene (stub)."""
    db = SessionLocal()
    try:
        scenes = db.query(Scene).all()  # type: ignore[attr-defined]
        for s in scenes:
            cnt = db.query(Metric).filter(Metric.scene_id == s.id).count()  # type: ignore[attr-defined]
            db.add(AuditLog(scene_id=s.id, action="backfill_metrics", details={"metric_count": int(cnt)}))
        db.commit()
        print(f"Backfilled metrics for {len(scenes)} scenes")
    finally:
        db.close()


def main() -> NoReturn:
    parser = argparse.ArgumentParser(prog="roborouter-cli", description="RoboRouter maintenance CLI (stub)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("cleanup")
    sub.add_parser("reindex")
    sub.add_parser("gc")
    sub.add_parser("backfill-metrics")
    args = parser.parse_args()

    if args.cmd == "cleanup":
        cmd_cleanup()
    elif args.cmd == "reindex":
        cmd_reindex()
    elif args.cmd == "gc":
        cmd_gc()
    elif args.cmd == "backfill-metrics":
        cmd_backfill_metrics()
    raise SystemExit(0)


if __name__ == "__main__":
    main()


