"""Unit tests for scripts/health_check.py"""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.health_check import check_arxiv, check_feeds, check_python  # type: ignore


class TestHealthCheck(unittest.TestCase):
    def test_check_python_ok(self):
        ok, _ = check_python()
        self.assertTrue(ok)
        self.assertRegex(_, r"^\d+\.\d+\.\d+")

    @patch("urllib.request.urlopen")
    def test_check_arxiv_ok(self, mock_urlopen):
        mock_cm = MagicMock()
        mock_cm.status = 200
        mock_cm.__enter__.return_value = mock_cm
        mock_cm.__exit__.return_value = None
        mock_urlopen.return_value = mock_cm
        ok, msg = check_arxiv()
        self.assertTrue(ok)
        self.assertIn("200", msg)

    @patch("urllib.request.urlopen")
    def test_check_arxiv_429(self, mock_urlopen):
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError("url", 429, "Too Many Requests", None, None)
        ok, msg = check_arxiv()
        self.assertTrue(ok)  # 429 is treated as "available, rate limited"
        self.assertIn("429", msg)

    @patch("urllib.request.urlopen")
    def test_check_feeds_mixed(self, mock_urlopen):
        ok200 = MagicMock()
        ok200.status = 200
        ok200.__enter__.return_value = ok200
        ok200.__exit__.return_value = None
        err404 = MagicMock()
        err404.status = 404
        err404.__enter__.return_value = err404
        err404.__exit__.return_value = None

        def side_effect(*args, **kwargs):
            url = args[0].full_url
            if "openai" in url:
                return ok200
            if "feedburner" in url:
                return ok200
            raise Exception("not found")

        mock_urlopen.side_effect = side_effect
        feeds_ok, details = check_feeds({
            "feeds": [
                {"url": "https://openai.com/news/rss.xml"},
                {"url": "https://feeds.feedburner.com/blogspot/gJZg"},
                {"url": "https://dead.example.com/feed"},
            ]
        })
        self.assertFalse(feeds_ok)
        self.assertTrue(details["https://openai.com/news/rss.xml"][0])
        self.assertFalse(details["https://dead.example.com/feed"][0])


if __name__ == "__main__":
    unittest.main()
