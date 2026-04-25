"""Tests for CLI argument parsing and new flags."""
import unittest
from unittest.mock import patch, MagicMock
import io
import sys

from research_digest.cli import main, load_config, default_config


class TestCliFlags(unittest.TestCase):
    @patch("research_digest.cli.fetch_papers", return_value=[])
    @patch("research_digest.cli.fetch_feed", return_value=[])
    @patch("research_digest.cli.render_digest", return_value="# Test\n")
    def test_dry_run_prints_to_stdout(self, mock_render, mock_feed, mock_arxiv):
        """--dry-run should render and print to stdout."""
        captured = io.StringIO()
        with patch.object(sys, "stdout", captured):
            rc = main(["--dry-run", "--no-summarize"])
        self.assertEqual(rc, 0)
        output = captured.getvalue()
        self.assertIn("# Test", output)

    @patch("research_digest.cli.fetch_papers", return_value=[])
    @patch("research_digest.cli.fetch_feed", return_value=[])
    @patch("research_digest.cli.render_digest", return_value="# Quiet\n")
    def test_quiet_suppresses_stderr(self, mock_render, mock_feed, mock_arxiv):
        """--quiet should suppress progress output."""
        err = io.StringIO()
        with patch.object(sys, "stderr", err):
            rc = main(["--quiet", "--no-summarize"])
        self.assertEqual(rc, 0)
        self.assertEqual(err.getvalue(), "")

    @patch("research_digest.cli.fetch_papers", return_value=[])
    @patch("research_digest.cli.fetch_feed", return_value=[])
    @patch("research_digest.cli.render_digest", return_value="# Quiet Render\n")
    def test_quiet_with_dry_run(self, mock_render, mock_feed, mock_arxiv):
        """--quiet --dry-run should have empty stderr but non-empty stdout."""
        out = io.StringIO()
        err = io.StringIO()
        with patch.object(sys, "stdout", out), patch.object(sys, "stderr", err):
            rc = main(["--quiet", "--dry-run", "--no-summarize"])
        self.assertEqual(rc, 0)
        self.assertEqual(err.getvalue(), "")
        self.assertIn("# Quiet Render", out.getvalue())

    def test_default_config_returns_dict(self):
        """default_config() should return a dict with expected keys."""
        cfg = default_config()
        self.assertIn("arxiv", cfg)
        self.assertIn("feeds", cfg)
        self.assertIn("output", cfg)


class TestLoadConfig(unittest.TestCase):
    def test_load_nonexistent_uses_default(self):
        """Nonexistent config path should fall back to default_config()."""
        cfg = load_config("/does/not/exist.json")
        self.assertIn("arxiv", cfg)


if __name__ == "__main__":
    unittest.main()
