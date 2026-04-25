#!/usr/bin/env python3
"""Rotate old cycle reports to keep ~/.hermes/cron/output/ bounded.

Usage:
    python scripts/rotate_reports.py [--keep-days 30] [--archive-dir ~/archive] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path


def rotate_reports(
    output_dir: Path,
    keep_days: int = 30,
    archive_dir: Path | None = None,
    dry_run: bool = False,
) -> dict:
    """Archive or delete cycle reports older than keep_days."""
    cutoff = datetime.now() - timedelta(days=keep_days)
    processed = {"archived": 0, "deleted": 0, "bytes_freed": 0, "errors": []}

    if archive_dir:
        archive_dir.mkdir(parents=True, exist_ok=True)

    for child in sorted(output_dir.glob("cycle_report_*")):
        if not child.is_file():
            continue
        try:
            mtime = datetime.fromtimestamp(child.stat().st_mtime)
        except OSError as exc:
            processed["errors"].append(f"stat {child.name}: {exc}")
            continue

        if mtime >= cutoff:
            continue

        size = child.stat().st_size
        if archive_dir:
            dest = archive_dir / child.name
            if dry_run:
                print(f"[dry-run] Would archive: {child.name} → {dest}")
            else:
                shutil.move(str(child), str(dest))
                print(f"Archived: {child.name} → {dest}")
            processed["archived"] += 1
        else:
            if dry_run:
                print(f"[dry-run] Would delete: {child.name}")
            else:
                child.unlink()
                print(f"Deleted: {child.name}")
            processed["deleted"] += 1
        processed["bytes_freed"] += size

    return processed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rotate old cycle reports.")
    parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="Number of days to keep reports (default: 30)",
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        default=str(Path.home() / ".hermes/cron/archive"),
        help="Directory to archive old reports (default: ~/.hermes/cron/archive)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path.home() / ".hermes/cron/output"),
        help="Directory containing cycle reports",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    archive_dir = Path(args.archive_dir) if not args.dry_run or args.archive_dir else None
    if args.dry_run and not args.archive_dir:
        archive_dir = Path(args.archive_dir)

    if not output_dir.exists():
        print(f"Output directory does not exist: {output_dir}", file=sys.stderr)
        return 1

    result = rotate_reports(
        output_dir=output_dir,
        keep_days=args.keep_days,
        archive_dir=archive_dir,
        dry_run=args.dry_run,
    )

    print()
    print(f"Reports archived: {result['archived']}")
    print(f"Reports deleted:  {result['deleted']}")
    print(f"Bytes freed:      {result['bytes_freed']:,}")
    if result["errors"]:
        print(f"Errors:           {len(result['errors'])}")
        for err in result["errors"]:
            print(f"  - {err}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
