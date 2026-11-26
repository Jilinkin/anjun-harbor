import unittest
from rc4_media_probe import classify
class ProbeTest(unittest.TestCase):
    def test_range(self):
        self.assertEqual(classify(206,"video/quicktime","bytes 0-63/1234",b"1234ftyp1234"),"range_observed")
    def test_html(self):
        self.assertEqual(classify(200,"text/html","",b"1234ftyp1234"),"unexpected_type")
    def test_wrong_header(self):
        self.assertEqual(classify(200,"video/mp4","",b"not media data"),"unrecognized_container")
    def test_missing_range(self):
        self.assertEqual(classify(206,"video/mp4","",b"1234ftyp1234"),"invalid_range")
if __name__=="__main__":unittest.main()
