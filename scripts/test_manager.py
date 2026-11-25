import re
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.pages = set()
        self.panels = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if "data-page" in a:
            self.pages.add(a["data-page"])
        if "data-panel" in a:
            self.panels.add(a["data-panel"])

class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / "manager.html").read_text(encoding="utf-8")
        self.parser = Parser()
        self.parser.feed(self.html)
    def test_unique_ids(self):
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))
    def test_script_references(self):
        self.assertFalse(set(re.findall(r"\$\('([^']+)'\)", self.html)) - set(self.parser.ids))
    def test_navigation(self):
        self.assertEqual(self.parser.pages, self.parser.panels)
        self.assertEqual(len(self.parser.pages), 7)
    def test_no_external_scripts(self):
        self.assertNotRegex(self.html, r"<script[^>]+src\s*=")
    def test_preview_and_draft(self):
        self.assertIn("function previewCatalog", self.html)
        self.assertIn("localStorage.setItem", self.html)
        self.assertIn("localStorage.getItem", self.html)

if __name__ == "__main__":
    unittest.main()
