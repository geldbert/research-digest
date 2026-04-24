"""Tests for rotate_digests.py utility."""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import rotate_digests as rd


class TestRotateDigests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.digests = Path(self.tmp.name) / "digests"
        self.digests.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write_digest(self, name: str, size: int = 100) -> None:
        (self.digests / name).write_bytes(b"x" * size)

    def test_no_files(self):
        result = rd.rotate(self.digests, 7, None, False, False)
        self.assertEqual(result["archived"], 0)
        self.assertEqual(result["deleted"], 0)

    def test_keeps_recent(self):
        today = datetime.now(timezone.utc)
        today_str = today.strftime("%Y-%m-%d")
        self._write_digest(f"digest_{today_str}.md")
        result = rd.rotate(self.digests, 7, None, False, False)
        self.assertEqual(result["archived"], 0)
        self.assertTrue((self.digests / f"digest_{today_str}.md").exists())

    def test_archives_old(self):
        old = datetime.now(timezone.utc) - timedelta(days=10)
        old_str = old.strftime("%Y-%m-%d")
        self._write_digest(f"digest_{old_str}.md", size=200)
        archive = Path(self.tmp.name) / "archive"
        result = rd.rotate(self.digests, 7, archive, False, False)
        self.assertEqual(result["archived"], 1)
        self.assertEqual(result["bytes_freed"], 200)
        self.assertFalse((self.digests / f"digest_{old_str}.md").exists())
        self.assertTrue((archive / f"digest_{old_str}.md").exists())

    def test_deletes_old(self):
        old = datetime.now(timezone.utc) - timedelta(days=10)
        old_str = old.strftime("%Y-%m-%d")
        self._write_digest(f"digest_{old_str}.md", size=300)
        result = rd.rotate(self.digests, 7, None, True, False)
        self.assertEqual(result["deleted"], 1)
        self.assertEqual(result["bytes_freed"], 300)
        self.assertFalse((self.digests / f"digest_{old_str}.md").exists())

    def test_dry_run(self):
        old = datetime.now(timezone.utc) - timedelta(days=10)
        old_str = old.strftime("%Y-%m-%d")
        self._write_digest(f"digest_{old_str}.md", size=400)
        result = rd.rotate(self.digests, 7, None, True, True)
        self.assertEqual(result["deleted"], 1)
        self.assertEqual(result["bytes_freed"], 400)
        self.assertTrue((self.digests / f"digest_{old_str}.md").exists())


if __name__ == "__main__":
    unittest.main()
