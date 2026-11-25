import json
import tempfile
import unittest
from pathlib import Path
from engine_registry import load_mixed
from engine_server import ROOT,route

DEMO=ROOT/"engine"/"examples"/"mixed"/"manifest.json"

class RegistryTests(unittest.TestCase):
    def setup_manifest(self,mutate):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p=Path(tmp.name)
        for f in DEMO.parent.iterdir():
            if f.is_file(): (p/f.name).write_bytes(f.read_bytes())
        m=json.loads((p/"manifest.json").read_text())
        mutate(m)
        (p/"manifest.json").write_text(json.dumps(m))
        return p/"manifest.json"
    def test_mixed_catalog(self):
        cat,status=load_mixed(DEMO)
        self.assertEqual(len(cat.providers),3)
        self.assertEqual(len(cat.records),3)
        self.assertEqual([x["status"] for x in status],["ok"]*3)
        self.assertEqual(cat.cms({"wd":["Harbor"]})["total"],3)
        self.assertEqual(len(cat.categories),1)
        self.assertEqual(len(route("/config.json","http://localhost",cat)["sites"]),1)
    def test_failure_isolation(self):
        p=self.setup_manifest(lambda m:m["providers"][1].update(snapshot="missing.json"))
        cat,status=load_mixed(p)
        self.assertEqual(len(cat.records),2)
        self.assertEqual(status[1]["status"],"failed")
    def test_duplicate(self):
        p=self.setup_manifest(lambda m:m["providers"].append(dict(m["providers"][0])))
        with self.assertRaises(ValueError): load_mixed(p)
    def test_unknown_kind(self):
        p=self.setup_manifest(lambda m:m["providers"][0].update(kind="remote-script"))
        with self.assertRaises(ValueError): load_mixed(p)
    def test_review_gate(self):
        p=self.setup_manifest(lambda m:m["providers"][0].update(approved=False))
        with self.assertRaises(ValueError): load_mixed(p)
    def test_rule_identity(self):
        p=self.setup_manifest(lambda m:m["providers"][1].update(authorization="different"))
        cat,status=load_mixed(p)
        self.assertEqual(status[1]["status"],"failed")
        self.assertEqual(len(cat.records),2)
    def test_snapshot_escape(self):
        p=self.setup_manifest(lambda m:m["providers"][1].update(snapshot="../outside.json"))
        cat,status=load_mixed(p)
        self.assertEqual(status[1]["status"],"failed")
    def test_network_opt_in(self):
        def modify(m):
            m["providers"].append({"kind":"cms-network","provider":"net","approved":True,"authorization":"Synthetic","api":"https://example.com/cms","media_hosts":["media.example.com"]})
        p=self.setup_manifest(modify)
        with self.assertRaises(ValueError): load_mixed(p,fetcher=lambda *_:self.fail("unexpected network"))
        data={"list":[{"vod_id":"1","vod_name":"Harbor Network","type_name":"Test","vod_play_url":"Full$https://media.example.com/net.mp4"}],"pagecount":1}
        cat,status=load_mixed(p,True,lambda *_:data)
        self.assertEqual(len(cat.records),4)
        self.assertEqual(status[-1]["status"],"ok")
    def test_cms_media_allowlist(self):
        p=self.setup_manifest(lambda m:m["providers"][0].update(media_hosts=["other.example"]))
        cat,status=load_mixed(p)
        self.assertEqual(status[0]["status"],"failed")
        self.assertEqual(len(cat.records),2)

if __name__=="__main__":unittest.main()
