import unittest
from dataclasses import replace
from engine_rebase import rebase
from engine_preferences import template,apply
from test_engine_dedupe import catalog,record

class RebaseTests(unittest.TestCase):
    def setUp(self):
        self.a=record("a")
        self.b=record("b",name="Second",category="Other")
        self.old=catalog(self.a,self.b)
        self.p=template(self.old)
        self.p["warehouse_name"]="My Harbor"
        self.p["provider_priority"]=["b","a"]
        self.p["category_names"]={"Test":"Personal"}
        self.p["records"]={self.a.id:{"hidden":True},self.b.id:{"name":"Alias"}}
    def test_unchanged(self):
        r=rebase(self.old,self.old,self.p)
        self.assertEqual(r["candidate_preferences"],self.p)
        self.assertEqual(r["conflicts"],[])
        self.assertTrue(r["review_required"])
    def test_added(self):
        new=catalog(self.a,self.b,record("c",category="New"))
        r=rebase(self.old,new,self.p)
        self.assertEqual(len(r["added"]),1)
        self.assertEqual(r["candidate_preferences"]["records"],self.p["records"])
        self.assertEqual(r["candidate_visible"],2)
    def test_changed_identity(self):
        new=catalog(replace(self.a,name="Changed"),self.b)
        r=rebase(self.old,new,self.p)
        self.assertEqual(r["changed"],[self.a.id])
        self.assertNotIn(self.a.id,r["candidate_preferences"]["records"])
        self.assertIn(self.b.id,r["candidate_preferences"]["records"])
        self.assertEqual(r["candidate_visible"],2)
    def test_removed(self):
        r=rebase(self.old,catalog(self.a),self.p)
        self.assertEqual(r["removed"],[self.b.id])
        self.assertEqual(r["candidate_preferences"]["provider_priority"],["a"])
        self.assertNotIn(self.b.id,r["candidate_preferences"]["records"])
    def test_category_new_member(self):
        new=catalog(self.a,self.b,record("c"))
        r=rebase(self.old,new,self.p)
        self.assertEqual(r["candidate_preferences"]["category_names"],{})
        self.assertTrue(any(c["kind"]=="category_names" for c in r["conflicts"]))
    def test_stale(self):
        p=dict(self.p);p["catalog_fingerprint"]="bad"
        with self.assertRaises(ValueError):rebase(self.old,self.old,p)
    def test_authorization_change(self):
        new=catalog(replace(self.a,license_note="Different authorization"),self.b)
        r=rebase(self.old,new,self.p)
        self.assertNotIn(self.a.id,r["candidate_preferences"]["records"])
    def test_not_active_file(self):
        r=rebase(self.old,self.old,self.p)
        with self.assertRaises(ValueError):apply(self.old,r)
        r["candidate_preferences"]["records"][self.a.id]["hidden"]=False
        self.assertTrue(self.p["records"][self.a.id]["hidden"])
    def test_candidate_valid(self):
        new=catalog(self.a,self.b,record("c",category="New"))
        r=rebase(self.old,new,self.p)
        out,name,_=apply(new,r["candidate_preferences"])
        self.assertEqual(name,"My Harbor")
        self.assertEqual(len(out.records),2)

if __name__=="__main__":unittest.main()
