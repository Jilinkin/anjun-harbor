package com.github.catvod.spider;
import android.content.Context;
import com.github.catvod.crawler.Spider;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

/** Original offline ABI prototype for two open films. */
public final class Harbor extends Spider {
    private static final HarborCatalog CATALOG = new HarborCatalog(HarborData.FILMS);
    public void init(Context c) {}
    public void init(Context c,String ext) {}
    private JSONObject row(String[] f,boolean detail) throws Exception {
        JSONObject j=new JSONObject().put("vod_id",f[0]).put("vod_name",f[1])
            .put("type_id",f[2]).put("vod_year",f[3]).put("vod_pic","");
        if(detail) j.put("vod_content",f[5]).put("vod_play_from","Harbor").put("vod_play_url","Full$"+f[0]);
        return j;
    }
    private JSONObject result(JSONArray rows,int page,int total) throws Exception {
        return new JSONObject().put("list",rows).put("page",page).put("pagecount",total==0?0:1).put("limit",20).put("total",total);
    }
    private int page(String p) {
        try{return Math.max(1,Integer.parseInt(p));}catch(NumberFormatException e){return 1;}
    }
    private JSONObject list(String category,String key,int page) throws Exception {
        JSONArray rows=new JSONArray(); int total=0;
        for(String[] f:CATALOG.query(category,key)){
            total++; if(page==1) rows.put(row(f,false));
        }
        return result(rows,page,total);
    }
    public String homeContent(boolean filter) throws Exception {
        JSONArray c=new JSONArray();
        c.put(new JSONObject().put("type_id","animation").put("type_name","Animation"));
        c.put(new JSONObject().put("type_id","scifi").put("type_name","Sci-Fi"));
        return list("","",1).put("class",c).toString();
    }
    public String homeVideoContent() throws Exception {return list("","",1).toString();}
    public String categoryContent(String tid,String pg,boolean filter,HashMap<String,String> ext) throws Exception {return list(tid,"",page(pg)).toString();}
    public String detailContent(List<String> ids) throws Exception {
        JSONArray rows=new JSONArray();
        for(String[] f:CATALOG.query("","")) if(ids.contains(f[0])) rows.put(row(f,true));
        return result(rows,1,rows.length()).toString();
    }
    public String searchContent(String key,boolean quick) throws Exception {return searchContent(key,quick,"1");}
    public String searchContent(String key,boolean quick,String pg) throws Exception {return list("",key==null?"":key,page(pg)).toString();}
    public String playerContent(String flag,String id,List<String> flags) throws Exception {
        String[] f=CATALOG.get(id);
        if(f!=null&&"Harbor".equals(flag)) return new JSONObject().put("parse",0).put("url",f[4]).toString();
        return new JSONObject().put("parse",0).put("url","").toString();
    }
}
