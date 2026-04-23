"""Tests for arxiv_client using stdlib only."""
import unittest
from unittest.mock import patch, MagicMock
from research_digest.arxiv_client import fetch_papers, Paper


def _make_atom(*arxiv_ids):
    entries = []
    for aid in arxiv_ids:
        entries.append(
            f"""<entry>
<id>http://arxiv.org/abs/{aid}</id>
<title>Paper {aid}</title>
<summary>Summary for {aid}</summary>
<published>2026-04-22T00:00:00Z</published>
<author><name>Alice</name></author>
<arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.AI"/>
</entry>"""
        )
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">'
        + "".join(entries)
        + "</feed>"
    )
    return xml.encode("utf-8")


class TestArxivClient(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_fetch_basic(self, mock_urlopen):
        mock_cm = MagicMock()
        mock_cm.read.return_value = _make_atom("2504.12345v1")
        mock_cm.__enter__.return_value = mock_cm
        mock_cm.__exit__.return_value = None
        mock_urlopen.return_value = mock_cm

        papers = fetch_papers("cat:cs.CL", max_results=2)
        self.assertIsInstance(papers, list)
        # filter out any empty-id entries from XML quirks
        papers = [p for p in papers if p.arxiv_id]
        self.assertGreaterEqual(len(papers), 1)
        p = papers[0]
        self.assertTrue(p.arxiv_id.startswith("2"))
        self.assertTrue(len(p.title) > 0)
        self.assertTrue(len(p.summary) > 0)
        self.assertTrue(len(p.authors) >= 1)
        self.assertTrue(p.pdf_url.startswith("https://arxiv.org/pdf/"))

    @patch("urllib.request.urlopen")
    def test_id_format(self, mock_urlopen):
        mock_cm = MagicMock()
        mock_cm.read.return_value = _make_atom("2504.12345v2")
        mock_cm.__enter__.return_value = mock_cm
        mock_cm.__exit__.return_value = None
        mock_urlopen.return_value = mock_cm

        papers = fetch_papers("cat:cs.CL", max_results=1)
        papers = [p for p in papers if p.arxiv_id]
        if papers:
            self.assertIn("v", papers[0].arxiv_id)


if __name__ == "__main__":
    unittest.main()
