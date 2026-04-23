"""Tests for rss_client."""
import unittest
from unittest.mock import patch, MagicMock
from research_digest.rss_client import fetch_feed, Article


def _make_atom_feed(title="T", link="http://x"):
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        f'<entry><title>{title}</title>'
        f'<link href="{link}"/><summary>S</summary>'
        '<published>2026-04-22T00:00:00Z</published>'
        '</entry></feed>'
    )
    return xml.encode("utf-8")


class TestRssClient(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_fetch_arxiv_atom(self, mock_urlopen):
        mock_cm = MagicMock()
        mock_cm.read.return_value = _make_atom_feed()
        mock_cm.__enter__.return_value = mock_cm
        mock_cm.__exit__.return_value = None
        mock_urlopen.return_value = mock_cm

        articles = fetch_feed("http://example.com/feed", feed_name="arXiv Test")
        self.assertIsInstance(articles, list)
        self.assertGreaterEqual(len(articles), 1)
        a = articles[0]
        self.assertTrue(len(a.title) > 0)
        self.assertTrue(a.link.startswith("http"))

    def test_article_dataclass(self):
        a = Article(title="T", link="http://x", summary="S", published="2026-04-22")
        self.assertEqual(a.title, "T")


if __name__ == "__main__":
    unittest.main()
