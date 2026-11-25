import hashlib
import json
import unittest
from integrity_release import generate

class IntegrityTests(unittest.TestCase):
    def test_hints(self):
        data=b"synthetic fixture"
        sha=hashlib.sha256(data).hexdigest()
        md5=hashlib.md5(data).hexdigest()
        outputs=generate(data,sha,"rc2","a"*40)
        direct=json.loads(outputs["config-md5.json"])
        proxy=json.loads(outputs["config-cn-md5.json"])
        self.assertEqual(proxy["spider"],"https://gh-proxy.com/"+direct["spider"])
        self.assertTrue(direct["spider"].endswith(";md5;"+md5))
        self.assertIn("/"+"a"*40+"/",direct["spider"])
        self.assertEqual(json.loads(outputs["integrity.json"])["sha256"],sha)
    def test_rc3_demo(self):
        data=b"synthetic"
        cfg=json.loads(generate(data,hashlib.sha256(data).hexdigest(),"rc3","a"*40)["config-cn-md5.json"])
        self.assertEqual(cfg["sites"][0]["ext"],"harbor-rc3-demo")
    def test_wrong_sha(self):
        with self.assertRaises(ValueError):generate(b"bad","0"*64,"rc2","a"*40)
    def test_bad_version(self):
        with self.assertRaises(ValueError):generate(b"ok",hashlib.sha256(b"ok").hexdigest(),"../rc2","a"*40)
    def test_bad_revision(self):
        with self.assertRaises(ValueError):generate(b"ok",hashlib.sha256(b"ok").hexdigest(),"rc2","main")

if __name__=="__main__":unittest.main()
