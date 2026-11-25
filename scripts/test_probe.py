import unittest
from unittest.mock import patch
from probe import inspect_body, public_ip, report

def site(**changes):
    return dict({"key":"demo","name":"Demo","type":1,"api":"https://example.com/vod",
                 "approved":True,"authorization":"Fixture only","probe":True}, **changes)

def catalog(*sites):
    return {"version":1,"groups":[{"id":"featured","name":"Featured","sites":list(sites)}]}

class ProbeTests(unittest.TestCase):
    def test_json(self):
        self.assertEqual(inspect_body(b'{"list":[{}]}', 1), 1)
        self.assertIsNone(inspect_body(b'{"error":"bad"}', 1))
    def test_xml(self):
        self.assertEqual(inspect_body(b'<rss><list><video/></list></rss>', 0), 1)
        self.assertIsNone(inspect_body(b'<!DOCTYPE rss><rss/>', 0))
    def test_empty(self):
        self.assertEqual(report(catalog())["checks"], [])
    def test_opt_in(self):
        with patch("probe.probe") as mock:
            result = report(catalog(site(probe=False)), checker=mock)
            mock.assert_not_called()
            self.assertEqual(result["checks"][0]["status"],"not_requested")
    def test_unapproved(self):
        with patch("probe.probe") as mock:
            result = report(catalog(site(approved=False)), checker=mock)
            mock.assert_not_called()
            self.assertEqual(result["checks"][0]["status"],"not_published")
    def test_record(self):
        result = report(catalog(site()), checker=lambda _:{"status":"metadata_ok","score":100})
        self.assertEqual(result["checks"][0]["score"],100)
    def test_private_address(self):
        with patch("probe.socket.getaddrinfo", return_value=[(2,1,6,"",("127.0.0.1",443))]):
            with self.assertRaises(ValueError):
                public_ip("example.com",443)

if __name__ == "__main__":
    unittest.main()
