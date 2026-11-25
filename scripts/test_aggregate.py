import tempfile
import unittest
from pathlib import Path
from aggregate import parse_config,inventory,analyze,make_catalog,digest,snapshots

class AggregateTests(unittest.TestCase):
    def test_jsonc(self):
        self.assertEqual(parse_config('{"url":"https://example.com/a",// comment\n"sites":[],}'),{"url":"https://example.com/a","sites":[]})
    def test_duplicate_fields(self):
        with self.assertRaises(ValueError): parse_config('{"x":1,"x":2}')
    def test_expand_and_cycle(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); a="https://example.com/a.json"; b="https://example.com/b.json"
            (root/"a").write_text('{"urls":[{"url":"b.json"},{"url":"a.json"},{"url":"missing.json"}]}')
            (root/"b").write_text('{"sites":[]}')
            ws,issues=inventory([a],{a:root/"a",b:root/"b"})
            self.assertEqual(len(ws),1)
            self.assertEqual({x["reason"] for x in issues},{"cycle","snapshot_missing"})
    def test_dedupe_report(self):
        s={"key":"x","name":"X","type":1,"api":"https://example.com/vod"}
        ws=[("https://example.com/a",{"sites":[s]}),("https://example.com/b",{"sites":[s]})]
        r=analyze(ws,[])
        self.assertEqual(len(r["same_independent_api_candidates"]),1)
        self.assertEqual(len(r["identical_config_content_candidates"]),1)
    def test_selection_and_dedupe(self):
        s={"key":"x","name":"X","type":1,"api":"https://example.com/vod"}
        ws=[("https://example.com/a",{"sites":[s]}),("https://example.com/b",{"sites":[s]})]
        choices=[{"id":digest([u,0,s]),"group":"featured","approved":True,"independent_confirmed":True,"authorization":"Synthetic fixture"} for u,_ in ws]
        self.assertEqual(len(make_catalog(ws,{"entries":choices})["groups"][0]["sites"]),1)
        choices[0]["approved"]=False
        with self.assertRaises(ValueError): make_catalog(ws,{"entries":choices})
    def test_complex_rejected(self):
        s={"key":"x","type":3,"api":"csp_X","name":"X"}
        u="https://example.com/a"
        with self.assertRaises(ValueError):
            make_catalog([(u,{"sites":[s]})],{"entries":[{"id":digest([u,0,s]),"group":"featured","approved":True,"independent_confirmed":True,"authorization":"fixture"}]})
    def test_root_escape(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                snapshots({"snapshots":[{"url":"https://example.com/a","file":"../secret"}]},d)

if __name__=="__main__": unittest.main()
