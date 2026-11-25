import hashlib
import io
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from http.server import ThreadingHTTPServer
from serve_test import verified_jar,validate_address,make_handler

def fixture(extra=False):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("classes.dex",b"dex\n035\0synthetic")
        if extra: z.writestr("unexpected.class",b"test")
    return b.getvalue()

class DeployTest(unittest.TestCase):
    def verify(self,data,expected=None):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"harbor.jar";p.write_bytes(data)
            return verified_jar(p,expected or hashlib.sha256(data).hexdigest())
    def test_checksum(self):
        data=fixture()
        self.assertEqual(self.verify(data)[0],data)
        with self.assertRaises(ValueError): self.verify(data,"0"*64)
    def test_archive(self):
        with self.assertRaises(ValueError): self.verify(fixture(True))
    def test_address(self):
        self.assertEqual(validate_address("127.0.0.1",8897),"127.0.0.1")
        self.assertEqual(validate_address("192.168.1.10",8897,True),"192.168.1.10")
        for h,opt in [("0.0.0.0",True),("8.8.8.8",True),("192.168.1.10",False)]:
            with self.assertRaises(ValueError): validate_address(h,8897,opt)
    def test_http(self):
        data=fixture();digest=hashlib.sha256(data).hexdigest()
        # Reserve the actual loopback port before constructing config URLs.
        server=ThreadingHTTPServer(("127.0.0.1",0),None)
        base="http://127.0.0.1:"+str(server.server_port)
        handler,path=make_handler(base,"test-token",data,digest)
        server.RequestHandlerClass=handler
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            with urllib.request.urlopen(base+path,timeout=3) as r: cfg=json.load(r)
            self.assertEqual(len(cfg["sites"]),1)
            self.assertEqual(cfg["sites"][0]["api"],"csp_Harbor")
            with urllib.request.urlopen(cfg["spider"],timeout=3) as r: self.assertEqual(r.read(),data)
            req=urllib.request.Request(cfg["spider"],method="HEAD")
            with urllib.request.urlopen(req,timeout=3) as r:
                self.assertEqual(int(r.headers["Content-Length"]),len(data))
                self.assertEqual(r.read(),b"")
            for suffix in ("/config.json","/test-token/../catalog.json","/test-token/unknown"):
                with self.assertRaises(urllib.error.HTTPError) as err: urllib.request.urlopen(base+suffix,timeout=3)
                self.assertEqual(err.exception.code,404)
        finally:
            server.shutdown();server.server_close();worker.join(3)
    def test_real_ci_artifact(self):
        root=Path(__file__).resolve().parent/"build"
        if not os.environ.get("HARBOR_REQUIRE_ARTIFACT"):
            self.skipTest("Artifact verification requires built CI JAR")
        expected=(root/"sha256.txt").read_text().split()[0]
        data,digest=verified_jar(root/"harbor.jar",expected)
        self.assertEqual(digest,expected)
        self.assertTrue(data.startswith(b"PK"))

if __name__=="__main__": unittest.main()
