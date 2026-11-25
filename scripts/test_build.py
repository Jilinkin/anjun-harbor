import unittest
from build import build

def site(**changes):
    return dict({"key":"demo","name":"Demo","type":1,"api":"https://example.com/vod",
                 "approved":True,"authorization":"Fixture only"}, **changes)

def catalog(*sites):
    return {"version":1,"groups":[{"id":"featured","name":"Featured","sites":list(sites)}]}

class BuildTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(build(catalog())[1], {"urls":[]})
    def test_unapproved(self):
        self.assertEqual(build(catalog(site(approved=False)))[0], {})
    def test_vod_only(self):
        files, index = build(catalog(site(lives=[{}], spider="untrusted.jar", ext="untrusted.js")))
        config = files["warehouses/featured.json"]
        self.assertEqual(set(config), {"sites"})
        self.assertNotIn("ext", config["sites"][0])
        self.assertEqual(len(index["urls"]),1)
    def test_reject_type3(self):
        with self.assertRaises(ValueError):
            build(catalog(site(type=3)))
    def test_reject_credentials(self):
        with self.assertRaises(ValueError):
            build(catalog(site(api="https://user:password@example.com/vod")))
    def test_dedupe(self):
        files, _ = build(catalog(site(), site(key="another")))
        self.assertEqual(len(files["warehouses/featured.json"]["sites"]),1)
    def test_reject_duplicate_keys(self):
        with self.assertRaises(ValueError):
            build(catalog(site(), site(api="https://example.com/other")))
    def test_authorization_required(self):
        with self.assertRaises(ValueError):
            build(catalog(site(authorization="")))

if __name__ == "__main__":
    unittest.main()
