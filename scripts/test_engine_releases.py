import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from engine_releases import Store,compare
from test_engine_dedupe import record,catalog
from engine_server import route

class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name)/"local")
        self.a=record("a");self.b=record("b")
        self.c=catalog(self.a,self.b)
    def test_stage_separate(self):
        rid=self.store.stage(self.c,"Harbor")
        self.assertIsNone(self.store.state()["active"])
        c,n=self.store.channel("candidate")
        self.assertEqual(list(c.records),list(self.c.records))
        self.assertEqual(route("/config.json","http://localhost",c,n)["sites"][0]["name"],"Harbor")
    def test_promote_and_rollback(self):
        first=self.store.stage(self.c,"First")
        self.store.promote(first,None)
        second=self.store.stage(catalog(self.b),"Second")
        self.assertEqual(self.store.channel("active")[1],"First")
        self.store.promote(second,first)
        self.assertEqual(self.store.channel("active")[1],"Second")
        self.store.rollback(second)
        self.assertEqual(self.store.channel("active")[1],"First")
    def test_stale(self):
        first=self.store.stage(self.c,"First")
        second=self.store.stage(self.c,"Second")
        with self.assertRaises(ValueError):self.store.promote(first,None)
        self.store.promote(second,None)
        with self.assertRaises(ValueError):self.store.promote(second,None)
    def test_tamper(self):
        rid=self.store.stage(self.c,"Harbor")
        (self.store.snapshots/(rid+".json")).write_text("{}")
        with self.assertRaises(ValueError):self.store.channel("candidate")
    def test_idempotent(self):
        rid=self.store.stage(self.c,"Harbor")
        self.assertEqual(self.store.stage(self.c,"Harbor"),rid)
    def test_diff(self):
        old=(self.c,"A");new=(catalog(replace(self.a,name="Changed")),"B")
        r=compare(old,new)
        self.assertTrue(r["warehouse_name_changed"])
        self.assertEqual(r["removed"],[self.b.id])
        self.assertEqual(r["changed"],[self.a.id])
        self.assertEqual(r["added"],[])
    def test_order(self):
        c=catalog(self.b,self.a)
        rid=self.store.stage(c,"Harbor")
        out,_=self.store.get(rid)
        self.assertEqual(list(out.records),[self.b.id,self.a.id])
        self.assertTrue(compare((self.c,"Harbor"),(out,"Harbor"))["order_changed"])
    def test_invalid_id(self):
        with self.assertRaises(ValueError):self.store.get("../other")
    def test_empty(self):
        from harbor_engine import Catalog
        with self.assertRaises(ValueError):self.store.stage(Catalog([]),"Harbor")

if __name__=="__main__":unittest.main()
