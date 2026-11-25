package com.github.catvod.spider;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Collections;

public final class IsolationTest {
    static void check(boolean v,String why){if(!v)throw new AssertionError(why);}
    static JSONObject provider(String id,String[] f,String url)throws Exception{
        return new JSONObject().put("id",id).put("kind","cms-snapshot").put("snapshot",
            new JSONObject().put("list",new JSONArray().put(new JSONObject().put("vod_id",f[0]).put("vod_name",f[1]).put("vod_play_url","Full$"+url))));
    }
    static String config(JSONObject... rows)throws Exception{
        JSONArray arr=new JSONArray();for(JSONObject row:rows)arr.put(row);
        return new JSONObject().put("version",3).put("providers",arr).toString();
    }
    public static void main(String[] args)throws Exception{
        HarborCatalog c=new HarborCatalog(HarborData.FILMS);
        String[] a=c.get("bunny"),b=c.get("steel");
        JSONObject good=provider("good",a,a[4]),bad=provider("bad",b,"https://example.invalid/private");
        JSONObject dup=provider("dup",a,a[4]);
        HarborLoadResult r=HarborRegistry.loadDetailed(config(bad,good,dup),c);
        JSONArray diag=new JSONArray(r.status);
        check(r.catalog.query("","").size()==1&&r.catalog.get("bunny")!=null,"Surviving provider");
        check(diag.length()==3&&diag.getJSONObject(0).getString("status").equals("failed"),"Failure diagnostic");
        check(diag.getJSONObject(1).getInt("unique")==1&&diag.getJSONObject(2).getInt("unique")==0,"Duplicate accounting");
        check(!r.status.contains("https://")&&!r.status.contains("private"),"Sanitized diagnostics");
        Harbor h=new Harbor();h.init(null,config(good,bad));
        JSONObject home=new JSONObject(h.homeContent(false));
        check(home.getJSONArray("list").length()==1&&home.getJSONArray("harbor_status").length()==2,"Plugin partial home");
        check(new JSONObject(h.searchContent("Bunny",false)).getJSONArray("list").length()==1,"Search survives");
        check(new JSONObject(h.playerContent("Harbor","steel",Collections.<String>emptyList())).getString("url").isEmpty(),"Failed source excluded");
        h.init(null,config(bad));
        check(new JSONObject(h.homeContent(false)).getJSONArray("list").length()==0,"All failed gives empty");
        check(new JSONArray(h.harborDiagnostics()).getJSONObject(0).getString("status").equals("failed"),"All failed diagnostic");
        try{h.init(null,config(good,good));throw new AssertionError("Duplicate provider accepted");}catch(IllegalArgumentException expected){}
        check(new JSONObject(h.homeContent(false)).getJSONArray("list").length()==0,"Invalid config fails closed");
        h.init(null,"");
        check(new JSONObject(h.homeContent(false)).getJSONArray("list").length()==2&&new JSONArray(h.harborDiagnostics()).length()==0,"Reset");
        System.out.println("Isolation and diagnostic checks passed");
    }
}
