"""Bounded release-candidate checks; no arbitrary URL input and no media mirroring."""
import json
import re
import urllib.request
import urllib.error
from datetime import datetime,timezone

SOURCES={
    "bunny":"https://download.blender.org/peach/bigbuckbunny_movies/big_buck_bunny_480p_h264.mov",
    "steel":"https://mirrors.aliyun.com/blender/demo/movies/ToS/tears_of_steel_720p.mov"
}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None

def classify(status,content_type,content_range,body):
    if status not in (200,206):return "http_error"
    if content_type.split(";")[0].lower() not in ("video/quicktime","video/mp4","application/octet-stream","video/x-quicktime"):
        return "unexpected_type"
    if len(body)<12 or body[4:8] not in (b"ftyp",b"moov",b"mdat",b"wide",b"free"):
        return "unrecognized_container"
    if status==206 and not re.fullmatch(r"bytes 0-[0-9]+/[0-9]+",content_range or ""):
        return "invalid_range"
    return "range_observed" if status==206 else "media_header_only"

def probe(url):
    opener=urllib.request.build_opener(NoRedirect())
    req=urllib.request.Request(url,headers={"Range":"bytes=0-63","Accept-Encoding":"identity","User-Agent":"Harbor-open-film-acceptance/1"})
    try:
        with opener.open(req,timeout=8) as r:
            body=r.read(64)
            status=r.status
            ct=r.headers.get("Content-Type","")
            cr=r.headers.get("Content-Range","")
            return {"status":classify(status,ct,cr,body),"http":status,"content_type":ct[:100],"content_range":cr[:100]}
    except urllib.error.HTTPError as e:
        e.close()
        return {"status":"http_error","http":e.code}
    except (OSError,ValueError) as e:
        return {"status":"unreachable","error_type":type(e).__name__}

if __name__=="__main__":
    print(json.dumps({"checked_at":datetime.now(timezone.utc).isoformat(),"scope":"CI runner only; not mainland China or playback verification","sources":[{"id":k,"url":v,**probe(v)} for k,v in SOURCES.items()]},indent=2))
