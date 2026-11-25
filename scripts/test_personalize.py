import unittest
from personalize import personalize,relocate

BASE="https://example.com/repo/config.json"
PREF={"approved_keys":["a","b"],"authorization":"Synthetic fixture only","dependencies_reviewed":True}
def fixture():
    return {"spider":"./lib.jar;md5;abc","sites":[{"key":"a","name":"A","type":3,"api":"./script.js","ext":"./rules/a.json","searchable":0},{"key":"b","name":"B","type":1,"api":"https://example.com/vod","searchable":1},{"key":"c","name":"C","type":1}],"lives":[{}],"parses":[{"url":"./parser"}]}

class PersonalizeTests(unittest.TestCase):
    def test_paths_and_live_removal(self):
        source=fixture();out=personalize(source,BASE,PREF)
        self.assertNotIn("lives",out)
        self.assertIn("lives",source)
        self.assertEqual(out["spider"],"https://example.com/repo/lib.jar;md5;abc")
        self.assertEqual(out["sites"][0]["ext"],"https://example.com/repo/rules/a.json")
        self.assertEqual(out["parses"][0]["url"],"https://example.com/repo/parser")
    def test_priority_hide_rename(self):
        out=personalize(fixture(),BASE,{**PREF,"priority":["b"],"rename":{"b":"New"},"search_keys":["a"]})
        self.assertEqual([s["key"] for s in out["sites"]],["b","a"])
        self.assertEqual(out["sites"][0]["name"],"New")
        self.assertEqual(out["sites"][0]["searchable"],0)
        self.assertEqual(out["sites"][1]["searchable"],0)
        self.assertEqual(len(personalize(fixture(),BASE,{**PREF,"hide":["a"]})["sites"]),1)
    def test_unreviewed(self):
        with self.assertRaises(ValueError): personalize(fixture(),BASE,{**PREF,"dependencies_reviewed":False})
    def test_stale_key(self):
        with self.assertRaises(ValueError): personalize(fixture(),BASE,{**PREF,"approved_keys":["missing"]})
    def test_unknown_relative(self):
        with self.assertRaises(ValueError): relocate({"unknown":"./x"},BASE)
    def test_protocol_relative(self):
        with self.assertRaises(ValueError): relocate({"api":"//example.com/x"},BASE)

if __name__=="__main__": unittest.main()
