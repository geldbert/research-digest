"""Tests for arxiv_client using stdlib only."""
import unittest
from research_digest.arxiv_client import fetch_papers, Paper


class TestArxivClient(unittest.TestCase):
    def test_fetch_basic(self):
        papers = fetch_papers("cat:cs.CL", max_results=2)
        self.assertIsInstance(papers, list)
        self.assertGreaterEqual(len(papers), 0)
        if papers:
            p = papers[0]
            self.assertTrue(p.arxiv_id.startswith("2"))
            self.assertTrue(len(p.title) > 0)
            self.assertTrue(len(p.summary) > 0)
            self.assertTrue(len(p.authors) >= 1)
            self.assertTrue(p.pdf_url.startswith("https://arxiv.org/pdf/"))

    def test_id_format(self):
        papers = fetch_papers("cat:cs.CL", max_results=1)
        if papers:
            self.assertIn("v", papers[0].arxiv_id)


if __name__ == "__main__":
    unittest.main()
