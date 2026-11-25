import hashlib
import tempfile
import unittest
from pathlib import Path
from audit_dependencies import audit

class AuditTests(unittest.TestCase):
    def test_local_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"test.js").write_bytes(b"fixture")
            data=audit({"sites":[{"type":3,"api":"./test.js"}]},root)
            item=data["dependencies"][0]
            self.assertEqual(item["status"],"local_hashed")
            self.assertEqual(item["sha256"],hashlib.sha256(b"fixture").hexdigest())
            self.assertTrue(item["executable_or_archive"])
    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            data=audit({"sites":[],"spider":"../secret.jar"},d)
            self.assertEqual(data["dependencies"][0]["status"],"outside_root")
    def test_encoded_escape(self):
        with tempfile.TemporaryDirectory() as d:
            data=audit({"sites":[],"spider":"%2e%2e/secret.jar"},d)
            self.assertEqual(data["dependencies"][0]["status"],"outside_root")
    def test_remote_redaction(self):
        with tempfile.TemporaryDirectory() as d:
            data=audit({"sites":[],"spider":"https://user:pass@example.com/a.jar?token=secret"},d)
            item=data["dependencies"][0]
            self.assertEqual(item["status"],"unsupported_remote")
            self.assertEqual(item["reference"],"https://example.com/a.jar")
    def test_missing_and_base(self):
        with tempfile.TemporaryDirectory() as d:
            item=audit({"sites":[{"ext":"./rules/a.json"}]},d,"https://example.com/config/main.json")["dependencies"][0]
            self.assertEqual(item["status"],"local_missing")
            self.assertEqual(item["resolved_url"],"https://example.com/config/rules/a.json")
    def test_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/"a.jar").write_bytes(b"test")
            item=audit({"sites":[],"spider":"./a.jar;md5;"+"0"*32},d)["dependencies"][0]
            self.assertEqual(item["status"],"hash_mismatch")
    def test_no_api_media(self):
        with tempfile.TemporaryDirectory() as d:
            data=audit({"sites":[{"type":1,"api":"https://example.com/vod"}]},d)
            self.assertEqual(data["dependencies"],[])
    def test_conflicting_names(self):
        with tempfile.TemporaryDirectory() as d:
            data=audit({"sites":[{"ext":"./a/test.js"},{"ext":"./b/test.js"}]},d)
            self.assertEqual(len(data["possible_name_conflicts"]),1)
    def test_invalid_base(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                audit({"sites":[]},d,"file:///tmp/main.json")

if __name__ == "__main__":
    unittest.main()
