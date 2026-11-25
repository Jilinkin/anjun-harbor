package com.github.catvod.spider;

import java.net.SocketTimeoutException;
import java.io.IOException;
import javax.net.ssl.SSLHandshakeException;
import org.json.JSONObject;
import org.json.JSONArray;

public final class CacheTest {
    static class Source implements HarborCache.Fetcher {
        int calls;
        JSONObject data;
        Exception failure;
        public JSONObject fetch()throws Exception{
            calls++;if(failure!=null)throw failure;return data;
        }
    }
    static void check(boolean ok,String msg){if(!ok)throw new AssertionError(msg);}
    static JSONObject response(String[] f)throws Exception{
        return new JSONObject().put("list",new JSONArray().put(new JSONObject()
            .put("vod_id",f[0]).put("vod_name",f[1]).put("vod_play_url","Full$"+f[4])));
    }
    public static void main(String[] args)throws Exception{
        HarborCatalog reviewed=new HarborCatalog(HarborData.FILMS);
        String[] a=reviewed.get("bunny"),b=reviewed.get("steel");
        HarborCache cache=new HarborCache();Source src=new Source();
        long s=1000000000L,now=0;
        src.data=response(a);
        check(cache.get(reviewed,src,now).status.equals("network"),"First fetch");
        check(cache.get(reviewed,src,now+30*s).status.equals("cache_fresh")&&src.calls==1,"Fresh cache");
        src.failure=new SocketTimeoutException();
        check(cache.get(reviewed,src,now+61*s).status.equals("cache_stale")&&src.calls==2,"Transient fallback");
        check(cache.get(reviewed,src,now+70*s).status.equals("cache_stale")&&src.calls==2,"Backoff");
        src.failure=null;src.data=response(b);
        check(cache.get(reviewed,src,now+77*s).catalog.get("steel")!=null&&src.calls==3,"Recovered");
        src.failure=new SocketTimeoutException();
        try{cache.get(reviewed,src,now+378*s);throw new AssertionError("Expired fallback");}
        catch(SocketTimeoutException expected){}
        src.failure=null;src.data=response(a);
        cache.get(reviewed,src,now+400*s);
        src.failure=new SSLHandshakeException("bad cert");
        try{cache.get(reviewed,src,now+461*s);throw new AssertionError("TLS bypass");}
        catch(SSLHandshakeException expected){}
        src.failure=new SocketTimeoutException();
        try{cache.get(reviewed,src,now+462*s);throw new AssertionError("Retained invalid cache");}
        catch(SocketTimeoutException expected){}
        src.failure=null;src.data=response(a);cache.get(reviewed,src,now+500*s);
        src.data=new JSONObject().put("list",new JSONArray().put(new JSONObject()
            .put("vod_id",a[0]).put("vod_name",a[1]).put("vod_play_url","Full$https://example.invalid/unknown")));
        try{cache.get(reviewed,src,now+561*s);throw new AssertionError("Invalid response accepted");}
        catch(IllegalArgumentException expected){}
        src.failure=new SocketTimeoutException();
        try{cache.get(reviewed,src,now+562*s);throw new AssertionError("Invalid response retained cache");}
        catch(SocketTimeoutException expected){}
        System.out.println("Cache expiry, backoff and validation tests passed");
    }
}
