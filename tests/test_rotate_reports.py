"""Tests for scripts/rotate_reports.py"""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

from scripts.rotate_reports import rotate_reports


class TestRotateReports(TestCase):
    def _make_reports(self, output_dir: Path, ages_days: list[int]) -> dict:
        """Create dummy report files with specified ages."""
        files = {}
        now = datetime.now()
        for i, days in enumerate(ages_days):
            name = f"cycle_report_test_{i}.txt"
            fpath = output_dir / name
            fpath.write_text(f"report {i}")
            mtime = (now - timedelta(days=days)).timestamp()
            os.utime(fpath, (mtime, mtime))
            files[name] = fpath
        return files

    def test_dry_run_does_not_modify(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "output"
            output_dir.mkdir()
            self._make_reports(output_dir, [0, 1, 2])
            result = rotate_reports(output_dir, keep_days=5, dry_run=True)
            self.assertEqual(result["archived"], 0)
            self.assertEqual(result["deleted"], 0)
            self.assertEqual(result["bytes_freed"], 0)
            self.assertEqual(len(list(output_dir.iterdir())), 3)

    def test_archive_old_files(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "output"
            archive_dir = Path(td) / "archive"
            output_dir.mkdir()
            self._make_reports(output_dir, [0, 1, 5])
            result = rotate_reports(
                output_dir, keep_days=2, archive_dir=archive_dir, dry_run=False
            )
            self.assertEqual(result["archived"], 1)
            self.assertTrue((archive_dir / "cycle_report_test_2.txt").exists())
            self.assertFalse((output_dir / "cycle_report_test_2.txt").exists())

    def test_delete_old_files(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "output"
            output_dir.mkdir()
            self._make_reports(output_dir, [0, 1, 5])
            result = rotate_reports(output_dir, keep_days=2, archive_dir=None, dry_run=False)
            self.assertEqual(result["deleted"], 1)
            self.assertEqual(len(list(output_dir.iterdir())), 2)

    def test_keep_recent_files(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "output"
            output_dir.mkdir()
            self._make_reports(output_dir, [0, 1])
            result = rotate_reports(
                output_dir, keep_days=7, archive_dir=None, dry_run=False
            )
            self.assertEqual(result["archived"], 0)
            self.assertEqual(result["deleted"], 0)
            self.assertEqual(len(list(output_dir.iterdir())), 2)

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "output"
            output_dir.mkdir()
            result = rotate_reports(
                output_dir, keep_days=1, archive_dir=None, dry_run=False
            )
            self.assertEqual(result["archived"], 0)
            self.assertEqual(result["deleted"], 0)
            self.assertEqual(result["bytes_freed"], 0)

    def test_bytes_freed_accounts_correctly(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "output"
            output_dir.mkdir()
            files = self._make_reports(output_dir, [5])
            expected_size = files["cycle_report_test_0.txt"].stat().st_size
            result = rotate_reports(
                output_dir, keep_days=2, archive_dir=None, dry_run=False
            )
            self.assertEqual(result["bytes_freed"], expected_size)
