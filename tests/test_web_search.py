"""Tests for web_search Bing fallback."""
import unittest
from unittest.mock import patch, MagicMock
from research_digest.web_search import WebResult, fetch_web_results, _fetch_via_bing


class TestWebSearch(unittest.TestCase):
    def test_web_result_dataclass(self):
        r = WebResult(title="T", href="http://x", body="B")
        self.assertEqual(r.title, "T")
        self.assertEqual(r.href, "http://x")
        self.assertEqual(r.body, "B")

    @patch("research_digest.web_search._fetch_via_bing")
    def test_fetch_web_with_bing(self, mock_bing):
        mock_bing.return_value = [
            WebResult(title="B", href="http://b", body="C", source="web")
        ]
        results = fetch_web_results("q", max_results=1, backend="bing")
        self.assertEqual(results[0].title, "B")
        mock_bing.assert_called_once_with("q", 1)

    @patch("urllib.request.urlopen")
    def test_bing_fallback_parses_html(self, mock_urlopen):
        html = (
            '<a class="result__a" href="http://example.com">Example</a>'
            '<a class="result__snippet">Snippet text</a>'
        )
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        results = _fetch_via_bing("query", max_results=2)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Example")
        self.assertEqual(results[0].href, "http://example.com")
        self.assertEqual(results[0].body, "Snippet text")

    @patch("urllib.request.urlopen")
    def test_bing_empty_html(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"<html></html>"
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        results = _fetch_via_bing("q", max_results=5)
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
