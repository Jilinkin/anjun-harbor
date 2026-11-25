import tempfile
import unittest
from pathlib import Path
from release import stage,verify,publish,read
from build import write

def catalog(name="A", enabled=True):
    return {"version":1,"groups":[{"id":"featured","name":"Featured","sites":[
        {"key":"a","name":name,"type":1,"api":"https://example.com/vod","approved":enabled,"authorization":"Fixture only"}]}]}

class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.legacy={"urls":[{"name":"Legacy","url":"https://example.com/old.json"}]}
        write(self.root/"legacy.json",self.legacy)
        write(self.root/"catalog.json",catalog())
        self.select("legacy")
    def select(self,value):
        write(self.root/"release-control.json",{"version":1,"active":value})
    def test_stage_keeps_production(self):
        status=publish(self.root)
        self.assertEqual(read(self.root/"index.json"),self.legacy)
        self.assertIn(status["candidate"],read(self.root/"test.json")["urls"][0]["url"])
    def test_promote_then_new_candidate(self):
        first=publish(self.root)["candidate"]
        self.select(first)
        write(self.root/"catalog.json",catalog("B"))
        status=publish(self.root)
        self.assertNotEqual(first,status["candidate"])
        self.assertEqual(read(self.root/"index.json"),verify(self.root,first))
    def test_rollback(self):
        first=publish(self.root)["candidate"]
        self.select(first)
        publish(self.root)
        self.select("legacy")
        publish(self.root)
        self.assertEqual(read(self.root/"index.json"),self.legacy)
    def test_empty_keeps_active(self):
        first=publish(self.root)["candidate"]
        self.select(first)
        write(self.root/"catalog.json",catalog(enabled=False))
        status=publish(self.root)
        self.assertIsNone(status["candidate"])
        self.assertEqual(read(self.root/"test.json"),{"urls":[]})
        self.assertEqual(read(self.root/"index.json"),verify(self.root,first))
    def test_tampering_rejected(self):
        rid,_=stage(self.root,catalog())
        write(self.root/"releases"/rid/"warehouses/featured.json",{"sites":[]})
        with self.assertRaises(ValueError):
            verify(self.root,rid)
        with self.assertRaises(ValueError):
            stage(self.root,catalog())
    def test_invalid_selection_preserves_index(self):
        publish(self.root)
        self.select("../bad")
        with self.assertRaises(ValueError):
            publish(self.root)
        self.assertEqual(read(self.root/"index.json"),self.legacy)
    def test_stable_id(self):
        a,_=stage(self.root,catalog())
        b,_=stage(self.root,catalog())
        self.assertEqual(a,b)
    def test_missing_release_rejected(self):
        self.select("0"*64)
        with self.assertRaises(FileNotFoundError):
            publish(self.root)

if __name__=="__main__":
    unittest.main()
