import unittest
from harbor_engine import Catalog,CmsSnapshotAdapter,Episode
from engine_server import demo,route

class EngineTests(unittest.TestCase):
    def test_demo_single_warehouse(self):
        cat=demo()
        self.assertEqual(len(cat.providers),2)
        self.assertEqual(len(cat.records),2)
        self.assertEqual(len(route("/config.json","http://localhost",cat)["sites"]),1)
    def test_search_and_detail(self):
        cat=demo()
        result=cat.cms({"wd":["bunny"]})
        self.assertEqual(result["total"],1)
        row=result["list"][0]
        self.assertNotIn("vod_play_url",row)
        detail=cat.cms({"ac":["detail"],"ids":[row["vod_id"]]})
        self.assertIn("https://",detail["list"][0]["vod_play_url"])
        self.assertIn("CC BY",detail["list"][0]["vod_content"])
    def test_categories(self):
        cat=demo()
        for category in cat.categories:
            self.assertEqual(cat.cms({"t":[category]})["total"],1)
    def test_pagination_and_empty(self):
        cat=demo()
        self.assertEqual(cat.cms({"pg":["2"]})["list"],[])
        self.assertEqual(cat.cms({"wd":["missing"]})["total"],0)
        with self.assertRaises(ValueError): cat.cms({"pg":["0"]})
    def test_unsafe_media(self):
        for value in ("file:///tmp/a","javascript:alert(1)","https://u:p@example.com/a","https://example.com/a#x"):
            with self.assertRaises(ValueError): Episode("play",value)
    def test_duplicate_provider(self):
        adapter=CmsSnapshotAdapter("test",{"list":[]},"synthetic")
        with self.assertRaises(ValueError): Catalog([adapter,adapter])
    def test_requires_authorization(self):
        with self.assertRaises(ValueError): CmsSnapshotAdapter("test",{"list":[]},"")
    def test_unknown_route(self):
        self.assertIsNone(route("/unknown","http://localhost",demo()))

if __name__=="__main__":unittest.main()
