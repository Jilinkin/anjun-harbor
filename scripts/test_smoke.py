import json
import unittest
from urllib.parse import urlsplit
from build import ROOT, BASE
from smoke_server import cms,route,SLUGS,fixture

class SmokeTests(unittest.TestCase):
    def test_static_multi(self):
        index=json.loads((ROOT/"smoke.json").read_text())
        self.assertEqual(len(index["urls"]),2)
        for entry in index["urls"]:
            self.assertTrue(entry["url"].startswith(BASE))
            config=json.loads((ROOT/entry["url"][len(BASE):]).read_text())
            self.assertEqual(set(config),{"sites"})
            site=config["sites"][0]
            self.assertEqual(site["type"],1)
            self.assertEqual(site["searchable"],0)
            data=json.loads((ROOT/site["api"][len(BASE):]).read_text())
            self.assertEqual(len(data["list"]),1)
    def test_media_and_credit(self):
        for slug in SLUGS:
            vod=fixture(slug)["list"][0]
            self.assertIn("creativecommons.org/licenses/by/3.0/",vod["vod_content"])
            self.assertEqual(urlsplit(vod["vod_play_url"].split("$",1)[1]).hostname,"storage.googleapis.com")
    def test_search(self):
        self.assertEqual(cms("animation",{"wd":["bunny"]})["total"],1)
        self.assertEqual(cms("animation",{"wd":["nonexistent"]})["total"],0)
    def test_detail_and_category(self):
        self.assertEqual(len(cms("scifi",{"ids":["2"],"t":["2"]})["list"]),1)
        self.assertEqual(len(cms("scifi",{"ids":["1"]})["list"]),0)
    def test_page(self):
        self.assertEqual(cms("animation",{"pg":["2"]})["list"],[])
    def test_local_routes(self):
        base="http://192.168.1.10:8899"
        index=route("/index.json",base)
        for e in index["urls"]:
            site=route(urlsplit(e["url"]).path,base)["sites"][0]
            self.assertEqual(site["searchable"],1)
            self.assertEqual(route(urlsplit(site["api"]).path+"?ac=list",base)["total"],1)
        self.assertIsNone(route("/../../README.md",base))
    def test_not_production(self):
        self.assertNotIn("smoke.json",(ROOT/"index.json").read_text())

if __name__=="__main__":
    unittest.main()
