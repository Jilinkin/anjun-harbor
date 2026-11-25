import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from local_library import scan,cms,byte_range,handler,open_media

class LibraryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        (self.root/"电影").mkdir()
        (self.root/"电影"/"示例.mp4").write_bytes(b"0123456789")
        (self.root/"secret.txt").write_text("not media")
        (self.root/"link.mp4").symlink_to(self.root/"电影"/"示例.mp4")
        self.groups,self.files=scan(self.root)
        self.mid=next(iter(self.files))
        self.gid=next(iter(self.groups))
    def test_scan(self):
        self.assertEqual(len(self.files),1)
        self.assertEqual(self.groups[self.gid]["name"],"电影")
    def test_search(self):
        a=cms(self.gid,{"wd":["示例"]},self.groups,self.files,"http://localhost")
        self.assertEqual(a["total"],1)
        self.assertEqual(cms(self.gid,{"wd":["no match"]},self.groups,self.files,"http://localhost")["total"],0)
    def test_range(self):
        self.assertEqual(byte_range("bytes=2-4",10),(2,4,True))
        self.assertEqual(byte_range("bytes=-2",10),(8,9,True))
        with self.assertRaises(ValueError):
            byte_range("bytes=10-",10)
    def test_replaced_media_rejected(self):
        p=self.files[self.mid]["path"]
        p.rename(p.with_suffix(".bak"))
        p.write_bytes(b"replacement")
        with self.assertRaises(ValueError):
            open_media(self.root,self.files[self.mid])
    def test_http(self):
        token="test-private-token"
        server=ThreadingHTTPServer(("127.0.0.1",0),handler(self.root,self.groups,self.files,"http://localhost/"+token,token))
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            base=f"http://127.0.0.1:{server.server_port}"
            with self.assertRaises(HTTPError) as err:
                urlopen(base+"/index.json")
            self.assertEqual(err.exception.code,404)
            with urlopen(base+"/"+token+"/index.json") as response:
                self.assertEqual(response.status,200)
            url=base+"/"+token+"/media/"+self.mid+".mp4"
            with urlopen(Request(url,headers={"Range":"bytes=2-4"})) as response:
                self.assertEqual(response.status,206)
                self.assertEqual(response.read(),b"234")
            with self.assertRaises(HTTPError) as err:
                urlopen(Request(url,headers={"Range":"bytes=20-"}))
            self.assertEqual(err.exception.code,416)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

if __name__=="__main__":
    unittest.main()
