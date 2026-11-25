import unittest
import tempfile
import json
from pathlib import Path
from engine_html import HtmlRuleAdapter,Tree,nodes,load_html
from harbor_engine import Catalog

HTML='<main><article class="film" data-id="a"><h2>Sample <em>film</em></h2><p class="kind">Film</p><a class="episode" href="https://media.example.com/a.mp4">Full</a></article><script>ignored</script></main>'
def css(p): return {"kind":"css","path":p}
def xpath(p): return {"kind":"xpath","path":p}
def f(s=None,a="text"): return {"selector":s,"attribute":a}
def rule():
    return {"version":1,"provider":"html","approved":True,"authorization":"Synthetic fixture only","items":css("main article.film"),"fields":{"id":f(a="data-id"),"name":f(css("h2")),"category":f(css(".kind"))},"episodes":{"items":css("a.episode"),"name":f(),"url":f(a="href")},"media_hosts":["media.example.com"]}

class HtmlTests(unittest.TestCase):
    def test_css(self):
        cat=Catalog([HtmlRuleAdapter(rule(),HTML)])
        self.assertEqual(cat.cms({"wd":["sample"]})["list"][0]["vod_name"],"Sample film")
        self.assertIn("https://media.example.com/",cat.cms({"ac":["detail"]})["list"][0]["vod_play_url"])
    def test_xpath(self):
        r=rule();r["items"]=xpath(".//article[@class='film']");r["fields"]["name"]=f(xpath("./h2"))
        self.assertEqual(len(Catalog([HtmlRuleAdapter(r,HTML)]).records),1)
    def test_script_ignored(self):
        self.assertEqual(nodes(Tree(HTML).root,css("script")),[])
    def test_disallowed_selectors(self):
        for s in (css("a, b"),css("a:nth-child(2)"),xpath("//a"),xpath(".//a/..")):
            with self.assertRaises(ValueError): nodes(Tree(HTML).root,s)
    def test_unapproved(self):
        with self.assertRaises(ValueError): HtmlRuleAdapter({**rule(),"approved":False},HTML)
    def test_media_host(self):
        with self.assertRaises(ValueError): list(HtmlRuleAdapter({**rule(),"media_hosts":["other.example"]},HTML).titles())
    def test_ambiguous_field(self):
        with self.assertRaises(ValueError): list(HtmlRuleAdapter(rule(),HTML.replace("</h2>","</h2><h2>Duplicate</h2>")).titles())
    def test_depth_limit(self):
        with self.assertRaises(ValueError): Tree("<div>"*100)
    def test_local_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"rule.json").write_text(json.dumps(rule()))
            (root/"page.html").write_text(HTML)
            (root/"manifest.json").write_text(json.dumps({"providers":[{"rule":"rule.json","snapshot":"page.html"}]}))
            cat,status=load_html(root/"manifest.json")
            self.assertEqual(len(cat.records),1)
            self.assertEqual(status[0]["status"],"ok")
    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"manifest.json"
            p.write_text(json.dumps({"providers":[{"rule":"../escape.json","snapshot":"page.html"}]}))
            with self.assertRaises(ValueError): load_html(p)

if __name__=="__main__": unittest.main()
