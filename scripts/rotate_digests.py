"""rotate_digests.py — Archive or purge old digest files to keep digests/ bounded.

Usage:
    python scripts/rotate_digests.py --keep-days 7 --archive-dir digests/archive/
    python scripts/rotate_digests.py --keep-days 7 --delete

Defaults come from environment or CLI switches; intended to be wired into cron.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_KEEP_DAYS = 7
DEFAULT_DIGESTS_DIR = "digests"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rotate old digest files")
    p.add_argument("--digests-dir", default=os.getenv("DIGESTS_DIR", DEFAULT_DIGESTS_DIR))
    p.add_argument("--keep-days", type=int, default=int(os.getenv("KEEP_DAYS", str(DEFAULT_KEEP_DAYS))))
    p.add_argument("--archive-dir", default=os.getenv("ARCHIVE_DIR", ""))
    p.add_argument("--delete", action="store_true", help="Delete instead of archive")
    p.add_argument("--dry-run", action="store_true", help="Show what would be done")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output")
    return p.parse_args(argv)


def rotate(digests_dir: Path, keep_days: int, archive_dir: Path | None, delete: bool, dry_run: bool, quiet: bool = False) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    processed = {"archived": 0, "deleted": 0, "bytes_freed": 0, "errors": []}

    for child in digests_dir.iterdir():
        if not child.is_file() or not child.name.startswith("digest_"):
            continue
        # Parse YYYY-MM-DD from filename
        try:
            date_part = child.name.split("_", 1)[1].split(".")[0]
            file_date = datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if file_date >= cutoff:
            continue

        action = "delete" if delete else "archive"
        if dry_run:
            if not quiet:
                print(f"[dry-run] Would {action}: {child.name}")
            processed["archived"] += 0 if delete else 1
            processed["deleted"] += 1 if delete else 0
            processed["bytes_freed"] += child.stat().st_size
            continue

        try:
            size = child.stat().st_size
            if delete:
                child.unlink()
                processed["deleted"] += 1
                processed["bytes_freed"] += size
            elif archive_dir:
                archive_dir.mkdir(parents=True, exist_ok=True)
                dest = archive_dir / child.name
                shutil.move(str(child), str(dest))
                processed["archived"] += 1
                processed["bytes_freed"] += size
        except Exception as exc:
            processed["errors"].append(f"{child.name}: {exc}")

    return processed


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    digests_dir = Path(args.digests_dir).expanduser().resolve()
    if not digests_dir.exists():
        print(f"ERROR: digests dir not found: {digests_dir}", file=sys.stderr)
        return 1

    archive_dir: Path | None = None
    if args.archive_dir:
        archive_dir = Path(args.archive_dir).expanduser().resolve()

    result = rotate(digests_dir, args.keep_days, archive_dir, args.delete, args.dry_run, args.quiet)
    if not args.quiet:
        print(f"Rotation complete: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
