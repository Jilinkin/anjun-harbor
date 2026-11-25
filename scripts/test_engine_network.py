import unittest
from unittest.mock import patch
from engine_network import endpoint,load_network,CmsNetworkAdapter,fetch_metadata

def config(name="first"):
    return {"provider":name,"approved":True,"authorization":"Synthetic fixture","api":"https://example.com/cms","media_hosts":["media.example.com"],"pages":2}

def row(i=1,host="media.example.com"):
    return {"vod_id":str(i),"vod_name":"Example "+str(i),"type_name":"Test","vod_play_url":"Episode$https://"+host+"/test.mp4"}

class NetworkTests(unittest.TestCase):
    def test_pages(self):
        calls=[]
        def fetch(url,page):
            calls.append(page)
            return {"list":[row(page)],"pagecount":2}
        cat,status=load_network({"providers":[config()]},fetch)
        self.assertEqual(calls,[1,2])
        self.assertEqual(len(cat.records),2)
        self.assertEqual(status[0]["status"],"ok")
    def test_failure_isolation_and_no_partial(self):
        a=config();b={**config("second"),"api":"https://example.org/cms"}
        def fetch(url,page):
            if "example.com" in url and page==2: raise TimeoutError()
            return {"list":[row(page)],"pagecount":2}
        cat,status=load_network({"providers":[a,b]},fetch)
        self.assertEqual(set(cat.providers),{"second"})
        self.assertEqual([x["status"] for x in status],["failed","ok"])
    def test_no_fetch_unapproved(self):
        with self.assertRaises(ValueError):
            load_network({"providers":[{**config(),"approved":False}]},lambda *_: self.fail("unexpected fetch"))
    def test_unapproved_media_host(self):
        cat,status=load_network({"providers":[config()]},lambda *_:{"list":[row(host="elsewhere.example")],"pagecount":1})
        self.assertFalse(cat.records)
        self.assertEqual(status[0]["status"],"failed")
    def test_duplicate_title(self):
        cat,status=load_network({"providers":[config()]},lambda *_:{"list":[row()],"pagecount":2})
        self.assertFalse(cat.records)
    def test_endpoints(self):
        for url in ("http://example.com/a","https://u:p@example.com/a","https://example.com/a?q=x","https://example.com:444/a"):
            with self.assertRaises(ValueError): endpoint(url)
    def test_bounds(self):
        with self.assertRaises(ValueError): CmsNetworkAdapter({**config(),"pages":4})
        with self.assertRaises(ValueError): load_network({"providers":[config()]*9})
    def test_private_dns_block(self):
        with patch("engine_network.public_ip",side_effect=ValueError("Non-public address")),patch("engine_network.PinnedHTTPS") as conn:
            with self.assertRaises(ValueError): fetch_metadata("https://example.com/cms",1)
            conn.assert_not_called()

if __name__=="__main__": unittest.main()
