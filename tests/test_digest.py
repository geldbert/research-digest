"""Tests for digest rendering."""
import unittest
from pathlib import Path
import tempfile
from research_digest.digest import render_digest, save_digest
from research_digest.arxiv_client import Paper
from research_digest.rss_client import Article
from research_digest.summarizer import Summary


class TestDigestRender(unittest.TestCase):
    def test_render_empty(self):
        md = render_digest([], [], [], [], title="Test", date="2026-04-22")
        self.assertIn("# Test", md)
        self.assertIn("2026-04-22", md)
        self.assertIn("No papers fetched", md)
        self.assertIn("No articles fetched", md)

    def test_render_with_content(self):
        papers = [
            Paper(
                arxiv_id="2601.00001v1",
                title="Test Paper",
                summary="Summary text.",
                authors=["A. One", "B. Two"],
                published="2026-04-22",
                primary_category="cs.CL",
                pdf_url="https://arxiv.org/pdf/2601.00001v1.pdf",
            )
        ]
        articles = [
            Article(
                title="Blog Post",
                link="https://example.com/post",
                summary="Post summary.",
                published="2026-04-22",
                feed_name="Ex",
            )
        ]
        summaries = [Summary(headline="HL", key_points=["K1"], relevance="R")]
        md = render_digest(papers, articles, summaries, summaries)
        self.assertIn("Test Paper", md)
        self.assertIn("Blog Post", md)
        self.assertIn("HL", md)
        self.assertIn("K1", md)

    def test_save_digest(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.md"
            save_digest("# Hello", p)
            self.assertTrue(p.exists())
            self.assertEqual(p.read_text(), "# Hello")


if __name__ == "__main__":
    unittest.main()
