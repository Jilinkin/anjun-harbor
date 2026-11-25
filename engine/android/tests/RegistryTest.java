package com.github.catvod.spider;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Collections;

public final class RegistryTest {
    private static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static JSONObject provider(String id,String kind,JSONObject snapshot)throws Exception {
        return new JSONObject().put("id",id).put("kind",kind).put("snapshot",snapshot);
    }
    private static JSONObject cms(String[] f)throws Exception {
        return new JSONObject().put("list",new JSONArray().put(new JSONObject()
            .put("vod_id",f[0]).put("vod_name",f[1]).put("vod_play_url","Full$"+f[4])));
    }
    private static JSONObject rule(String[] f)throws Exception {
        return new JSONObject().put("version",1).put("data",new JSONArray().put(new JSONArray().put(f[0]).put(f[1]).put(f[4])))
            .put("items",new JSONArray()).put("fields",new JSONObject().put("id",new JSONArray().put(0))
            .put("name",new JSONArray().put(1)).put("url",new JSONArray().put(2)));
    }
    private static JSONObject registry(JSONObject... providers)throws Exception {
        JSONArray arr=new JSONArray();for(JSONObject p:providers)arr.put(p);
        return new JSONObject().put("version",2).put("providers",arr);
    }
    private static void reject(JSONObject config,HarborCatalog c)throws Exception {
        try{HarborRegistry.load(config.toString(),c);throw new AssertionError("Unexpected acceptance");}
        catch(IllegalArgumentException expected){}
    }
    public static void main(String[] args)throws Exception {
        HarborCatalog c=new HarborCatalog(HarborData.FILMS);
        String[] a=c.get("bunny"),b=c.get("steel");
        JSONObject one=provider("one","cms-snapshot",cms(a));
        JSONObject two=provider("two","json-snapshot",rule(b));
        JSONObject duplicate=provider("three","json-snapshot",rule(a));
        JSONObject mixed=registry(one,two,duplicate);
        HarborCatalog out=HarborRegistry.load(mixed.toString(),c);
        check(out.query("","").size()==2,"Exact canonical duplicate collapsed");
        check(out.get("bunny")!=null&&out.get("steel")!=null,"Both formats");
        check(out.query("","").get(0)[0].equals("bunny"),"First occurrence ordering");
        reject(registry(one,one),c);
        reject(registry(provider("bad","remote-script",cms(a))),c);
        JSONObject wrong=cms(a);wrong.getJSONArray("list").getJSONObject(0).put("vod_play_url","Full$https://example.com/x");
        reject(registry(one,provider("bad","cms-snapshot",wrong)),c);
        Harbor h=new Harbor();h.init(null,mixed.toString());
        check(new JSONObject(h.homeContent(false)).getJSONArray("list").length()==2,"Plugin mixed home");
        check(new JSONObject(h.searchContent("steel",false)).getJSONArray("list").length()==1,"Plugin mixed search");
        try{h.init(null,registry(one,provider("bad","cms-snapshot",wrong)).toString());throw new AssertionError("Invalid registry accepted");}
        catch(IllegalArgumentException expected){}
        check(new JSONObject(h.homeContent(false)).getJSONArray("list").length()==0,"Atomic failure closed");
        check(new JSONObject(h.playerContent("Harbor","bunny",Collections.<String>emptyList())).getString("url").isEmpty(),"No stale player");
        h.init(null,rule(a).toString());
        check(new JSONObject(h.homeContent(false)).getJSONArray("list").length()==1,"V1 compatibility");
        System.out.println("Mixed adapter checks passed");
    }
}
