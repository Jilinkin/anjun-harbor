import unittest
from dataclasses import replace
from harbor_engine import Catalog,Title,Episode
from engine_network import LoadedAdapter
from engine_dedupe import preview,apply
from engine_server import route

def record(provider,**kw):
    fields=dict(provider=provider,native_id="1",name="Example Film",category="Test",year="2024",description="Synthetic fixture",episodes=(Episode("Full","https://media.example.com/a.mp4"),),license_note="Synthetic fixture only")
    fields.update(kw)
    return Title(**fields)

def catalog(*items):
    return Catalog([LoadedAdapter(t.provider,[t]) for t in items])

def selection(c):
    r=preview(c);g=r["exact_record_candidates"][0]
    return {"version":1,"catalog_fingerprint":r["catalog_fingerprint"],"decisions":[{"group":g["group"],"keep":g["members"][0],"remove":g["members"][1:],"approved":True}]}

class DedupeTests(unittest.TestCase):
    def test_exact_review(self):
        c=catalog(record("a"),record("b"))
        r=preview(c)
        self.assertEqual(len(r["exact_record_candidates"]),1)
        self.assertEqual(len(c.records),2)
        out,history=apply(c,selection(c))
        self.assertEqual(len(out.records),1)
        self.assertEqual(history["hidden"],1)
        self.assertEqual(len(c.records),2)
        self.assertEqual(route("/api?wd=Example","http://localhost",out)["total"],1)
    def test_same_name_different_media(self):
        c=catalog(record("a"),record("b",episodes=(Episode("Full","https://media.example.com/b.mp4"),)))
        r=preview(c)
        self.assertEqual(r["exact_record_candidates"],[])
        self.assertEqual(len(r["same_title_year_candidates"]),1)
    def test_year_and_credit(self):
        c=catalog(record("a"),record("b",year="2023"),record("c",license_note="Other authorization"))
        self.assertEqual(preview(c)["exact_record_candidates"],[])
    def test_episode_order(self):
        eps=(Episode("1","https://media.example.com/1.mp4"),Episode("2","https://media.example.com/2.mp4"))
        c=catalog(record("a",episodes=eps),record("b",episodes=eps[::-1]))
        self.assertEqual(preview(c)["exact_record_candidates"],[])
    def test_stale(self):
        c=catalog(record("a"),record("b"))
        with self.assertRaises(ValueError):apply(catalog(record("a"),record("b",description="Changed")),selection(c))
    def test_no_approval(self):
        c=catalog(record("a"),record("b"));s=selection(c);s["decisions"][0]["approved"]=False
        with self.assertRaises(ValueError):apply(c,s)
    def test_keep_cannot_remove(self):
        c=catalog(record("a"),record("b"));s=selection(c);s["decisions"][0]["remove"]=[s["decisions"][0]["keep"]]
        with self.assertRaises(ValueError):apply(c,s)
    def test_no_choices(self):
        c=catalog(record("a"),record("b"));s=selection(c);s["decisions"]=[]
        out,h=apply(c,s)
        self.assertEqual(len(out.records),2)
        self.assertEqual(h["hidden"],0)
    def test_preview_no_media_urls(self):
        self.assertNotIn("https://",str(preview(catalog(record("a"),record("b")))))

if __name__=="__main__":unittest.main()
