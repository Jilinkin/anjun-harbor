import json
import tempfile
import unittest
from pathlib import Path
from engine_rules import JsonRuleAdapter,select,load_rules
from harbor_engine import Catalog

def rule(provider="test"):
    return {"version":1,"provider":provider,"approved":True,"authorization":"Synthetic test fixture","items":["payload","videos"],"fields":{"id":["id"],"name":["meta","title"],"category":["meta","kind"],"year":["meta","year"]},"episodes":{"items":["streams"],"name":["label"],"url":["file"]},"media_hosts":["media.example.com"]}

def data():
    return {"payload":{"videos":[{"id":1,"meta":{"title":"Sample","kind":"Film","year":2020},"streams":[{"label":"Full","file":"https://media.example.com/example.mp4"}]}]}}

class RuleTests(unittest.TestCase):
    def test_mapping(self):
        cat=Catalog([JsonRuleAdapter(rule(),data())])
        r=cat.cms({"ac":["detail"],"wd":["sample"]})
        self.assertEqual(r["total"],1)
        self.assertEqual(r["list"][0]["vod_year"],"2020")
        self.assertIn("https://media.example.com/",r["list"][0]["vod_play_url"])
    def test_second_structure(self):
        r=rule("other");r["items"]=[];r["fields"]={"id":[0],"name":[1],"category":[2]};r["episodes"]={"items":[3],"name":[0],"url":[1]}
        cat=Catalog([JsonRuleAdapter(rule(),data()),JsonRuleAdapter(r,[[1,"Second","Film",[["Full","https://media.example.com/b.mp4"]]]])])
        self.assertEqual(len(cat.records),2)
        self.assertEqual(len(cat.categories),1)
    def test_invalid_path(self):
        for p in ("payload",[-1],[True],["missing"]):
            with self.assertRaises(ValueError): select(data(),p)
    def test_unapproved(self):
        with self.assertRaises(ValueError): JsonRuleAdapter({**rule(),"approved":False},data())
    def test_no_executable_fields(self):
        with self.assertRaises(ValueError): JsonRuleAdapter({**rule(),"script":"anything"},data())
    def test_media_host(self):
        r=rule();r["media_hosts"]=["other.example"]
        with self.assertRaises(ValueError): list(JsonRuleAdapter(r,data()).titles())
    def test_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            files={"a.json":rule(),"b.json":rule("other"),"data.json":data(),"bad.json":{},"manifest.json":{"providers":[{"rule":"a.json","snapshot":"data.json"},{"rule":"b.json","snapshot":"bad.json"}]}}
            for k,v in files.items(): (root/k).write_text(json.dumps(v))
            cat,status=load_rules(root/"manifest.json")
            self.assertEqual(len(cat.records),1)
            self.assertEqual([x["status"] for x in status],["ok","failed"])
    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"manifest.json";p.write_text(json.dumps({"providers":[{"rule":"../escape.json","snapshot":"a.json"}]}))
            with self.assertRaises(ValueError): load_rules(p)

if __name__=="__main__": unittest.main()
