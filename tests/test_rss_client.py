"""Tests for rss_client."""
import unittest
from research_digest.rss_client import fetch_feed, Article

# Use arXiv Atom feed as a stable RSS/Atom source
TEST_FEED = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=2"


class TestRssClient(unittest.TestCase):
    def test_fetch_arxiv_atom(self):
        articles = fetch_feed(TEST_FEED, feed_name="arXiv Test")
        self.assertIsInstance(articles, list)
        self.assertGreaterEqual(len(articles), 0)
        if articles:
            a = articles[0]
            self.assertTrue(len(a.title) > 0)
            self.assertTrue(a.link.startswith("http"))

    def test_article_dataclass(self):
        a = Article(title="T", link="http://x", summary="S", published="2026-04-22")
        self.assertEqual(a.title, "T")


if __name__ == "__main__":
    unittest.main()
