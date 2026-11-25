import unittest
from compare_upstream import compare

def cfg(*sites, **extra):
    return {"sites":list(sites), **extra}

def site(key, **extra):
    return {"key":key,"type":1,"name":key,**extra}

class CompareTests(unittest.TestCase):
    def test_added_removed(self):
        d=compare(cfg(site("a"),site("b")),cfg(site("b"),site("c")))
        self.assertEqual(d["summary"],{"added":1,"removed":1,"changed":0,"unchanged":1})
    def test_field_changes(self):
        d=compare(cfg(site("a",api="https://example.com/old")),cfg(site("a",api="https://example.com/new")))
        self.assertEqual(d["changed"][0]["fields"],["api"])
        self.assertTrue(d["changed"][0]["dependency_review"])
    def test_rename(self):
        d=compare(cfg(site("a")),cfg(site("a",name="new")))
        self.assertFalse(d["changed"][0]["dependency_review"])
    def test_order(self):
        self.assertTrue(compare(cfg(site("a"),site("b")),cfg(site("b"),site("a")))["reordered"])
        self.assertFalse(compare(cfg(site("a"),site("b")),cfg(site("c"),site("a"),site("b")))["reordered"])
    def test_top_level(self):
        d=compare(cfg(spider="old.jar"),cfg(spider="new.jar",lives=[]))
        self.assertEqual(d["top_level_fields"],["lives","spider"])
        self.assertTrue(d["global_dependency_review"])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            compare(cfg(site("a"),site("a")),cfg())
    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            compare({"sites":[{}]},cfg())
    def test_dictionary_order_ignored(self):
        self.assertEqual(compare(cfg({"key":"a","type":1}),cfg({"type":1,"key":"a"}))["summary"]["unchanged"],1)
    def test_null_and_missing_distinct(self):
        self.assertEqual(compare(cfg(site("a")),cfg(site("a",ext=None)))["changed"][0]["fields"],["ext"])

if __name__ == "__main__":
    unittest.main()
