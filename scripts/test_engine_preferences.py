import unittest
from dataclasses import replace
from engine_preferences import template,apply
from engine_dedupe import fingerprint
from engine_server import route
from test_engine_dedupe import record,catalog

class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self.a=record("a")
        self.b=record("b",name="Other Film",category="Other")
        self.c=catalog(self.a,self.b)
    def test_rename_and_ids(self):
        p=template(self.c);p["warehouse_name"]="My Harbor"
        p["records"][self.a.id]={"name":"Renamed"}
        out,name,report=apply(self.c,p)
        self.assertEqual(out.records[self.a.id].name,"Renamed")
        self.assertEqual(out.records[self.a.id].episodes,self.a.episodes)
        self.assertEqual(out.records[self.a.id].license_note,self.a.license_note)
        self.assertEqual(self.c.records[self.a.id].name,self.a.name)
        self.assertEqual(route("/config.json","http://localhost",out,name)["sites"][0]["name"],"My Harbor")
        self.assertEqual(route("/api?wd=Renamed","http://localhost",out)["total"],1)
    def test_priority(self):
        p=template(self.c);p["provider_priority"]=["b","a"]
        out,_,_=apply(self.c,p)
        self.assertEqual(list(out.records),[self.b.id,self.a.id])
        p["records"][self.a.id]={"priority":10}
        out,_,_=apply(self.c,p)
        self.assertEqual(list(out.records),[self.a.id,self.b.id])
    def test_categories(self):
        p=template(self.c);p["category_names"]={"Test":"Unified","Other":"Unified"}
        out,_,_=apply(self.c,p)
        self.assertEqual(list(out.categories.values()),["Unified"])
    def test_hide(self):
        p=template(self.c);p["records"][self.a.id]={"hidden":True}
        out,_,report=apply(self.c,p)
        self.assertEqual(list(out.records),[self.b.id])
        self.assertEqual(report["hidden"],[self.a.id])
        self.assertEqual(len(self.c.records),2)
    def test_stale(self):
        p=template(self.c)
        changed=catalog(self.a,replace(self.b,name="Changed"))
        with self.assertRaises(ValueError):apply(changed,p)
    def test_invalid_edits(self):
        for edit in ({"url":"https://example.com"},{"hidden":1},{"priority":True},{"name":" "}):
            p=template(self.c);p["records"][self.a.id]=edit
            with self.assertRaises(ValueError):apply(self.c,p)
    def test_unknown(self):
        p=template(self.c);p["provider_priority"]=["unknown"]
        with self.assertRaises(ValueError):apply(self.c,p)
    def test_no_change(self):
        out,_,_=apply(self.c,template(self.c))
        self.assertEqual(fingerprint(out),fingerprint(self.c))
    def test_category_override(self):
        p=template(self.c);p["category_names"]={"Test":"Unified"}
        p["records"][self.a.id]={"category":"Personal"}
        out,_,_=apply(self.c,p)
        self.assertEqual(out.records[self.a.id].category,"Personal")
    def test_report_no_media(self):
        _,_,r=apply(self.c,template(self.c))
        self.assertNotIn("https://",str(r))

if __name__=="__main__":unittest.main()
