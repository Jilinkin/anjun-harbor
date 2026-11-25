package com.github.catvod.spider;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import org.json.JSONArray;
import org.json.JSONObject;

public final class PluginTest {
    private static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static JSONObject obj(String raw)throws Exception{return new JSONObject(raw);}
    public static void main(String[] args)throws Exception{
        Harbor h=new Harbor();
        Init.init(null);
        h.init(null);
        JSONObject home=obj(h.homeContent(false));
        check(home.getJSONArray("class").length()==2&&home.getJSONArray("list").length()==2,"Home");
        check(obj(h.homeVideoContent()).getJSONArray("list").length()==2,"Recent");
        check(obj(h.categoryContent("animation","1",false,new HashMap<String,String>())).getJSONArray("list").length()==1,"Category");
        check(obj(h.searchContent("BUNNY",false)).getJSONArray("list").length()==1,"Search");
        check(obj(h.searchContent("BUNNY",false,"2")).getJSONArray("list").length()==0,"Pagination");
        JSONObject detail=obj(h.detailContent(Arrays.asList("bunny"))).getJSONArray("list").getJSONObject(0);
        check(detail.getString("vod_play_url").equals("Full$bunny"),"RC1 detail identity");
        check(detail.getString("vod_play_from").equals("Harbor"),"Single playback line");
        JSONObject envelope=obj(h.detailContent(Arrays.asList("bunny")));
        check(!envelope.has("code")&&!envelope.has("msg"),"No status fields in detail");
        check(obj(h.searchContent("大雄兔",false)).getJSONArray("list").length()==1,"Chinese alias");
        check(obj(h.searchContent("ｂｕｎｎｙ",true)).getJSONArray("list").length()==1,"Full width query");
        check(detail.getString("vod_content").contains("CC BY 3.0"),"Credit");
        check(obj(h.playerContent("Harbor","bunny",Collections.<String>emptyList())).getString("url").equals(HarborData.FILMS[0][4]),"Known player ID");
        check(obj(h.playerContent("Harbor","https://example.com/x",Collections.<String>emptyList())).getString("url").isEmpty(),"Unknown ID");
        check(obj(h.playerContent("wrong","bunny",Collections.<String>emptyList())).getString("url").isEmpty(),"Unknown flag");
        String[] f=HarborData.FILMS[0];
        JSONObject rule=new JSONObject().put("version",1).put("data",new JSONArray().put(new JSONArray().put(f[0]).put(f[1]).put(f[4])))
            .put("items",new JSONArray()).put("fields",new JSONObject().put("id",new JSONArray().put(0)).put("name",new JSONArray().put(1)).put("url",new JSONArray().put(2)));
        h.init(null,rule.toString());
        check(obj(h.homeContent(false)).getJSONArray("class").length()==1,"Filtered categories");
        check(obj(h.searchContent("steel",false)).getJSONArray("list").length()==0,"Filtered search");
        check(obj(h.playerContent("Harbor","steel",Collections.<String>emptyList())).getString("url").isEmpty(),"Filtered player");
        try{h.init(null,"https://example.com/config.json");throw new AssertionError("URL accepted");}catch(org.json.JSONException expected){}
        check(obj(h.homeContent(false)).getJSONArray("list").length()==0,"Fail closed");
        check(obj(h.homeContent(false)).getJSONArray("class").length()==0,"Empty categories");
        h.init(null,"");
        check(obj(h.homeContent(false)).getJSONArray("list").length()==2,"Restore");
        check(obj(h.playerContent("Harbor","diagnostic",Collections.<String>emptyList())).getString("url").isEmpty(),"Diagnostic disabled by default");
        h.init(null,"harbor-rc3-demo");
        check(obj(h.homeContent(false)).getJSONArray("list").length()==3,"RC3 home");
        check(obj(h.homeContent(false)).getJSONArray("class").length()==3,"RC3 categories");
        JSONObject diagnostic=obj(h.detailContent(Arrays.asList("diagnostic"))).getJSONArray("list").getJSONObject(0);
        check(diagnostic.getString("vod_play_url").equals("Full$diagnostic"),"Single diagnostic episode");
        check(obj(h.playerContent("Harbor","diagnostic",Collections.<String>emptyList())).getString("url").endsWith("/diagnostic.mp4"),"Original diagnostic media");
        h.init(null,"");
        check(obj(h.homeContent(false)).getJSONArray("list").length()==2,"Reset diagnostic");
        System.out.println("Plugin contract checks passed");
    }
}
