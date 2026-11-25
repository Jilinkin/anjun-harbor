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
    private static final HarborLoadResult DEFAULT=new HarborLoadResult(CATALOG,"[]");
    private volatile HarborLoadResult state=DEFAULT;
    public synchronized void init(Context c) {state=DEFAULT;}
    public synchronized void init(Context c,String ext) throws Exception {
        if(ext==null||ext.trim().isEmpty()){state=DEFAULT;return;}
        // Never briefly expose the default or previous catalog on invalid input.
        state=new HarborLoadResult(new HarborCatalog(new String[0][]),"[]");
        state=HarborRegistry.loadDetailed(ext,CATALOG);
    }
    public String harborDiagnostics(){return state.status;}
    private static final String STATIC="https://gh-proxy.com/https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/android-demo/rc2/";
    private JSONObject row(String[] f,boolean detail) throws Exception {
        JSONObject j=new JSONObject().put("vod_id",f[0]).put("vod_name",f[1])
            .put("type_id",f[2]).put("type_name",f[2].equals("animation")?"动画":"科幻").put("vod_year",f[3]).put("vod_pic",STATIC+f[0]+".png").put("vod_remarks","开放影片");
        if(detail) {
            String lines="Harbor$$诊断短片（非正片）", urls="Full$"+f[0]+"$$5秒测试$diag-"+f[0];
            if("bunny".equals(f[0])){lines+="$$Blender 官方备选";urls+="$$Full$official-bunny";}
            j.put("vod_content",f[5]+" | 诊断短片为 Harbor 原创测试画面，不是影片内容。").put("vod_play_from",lines).put("vod_play_url",urls);
        }
        return j;
    }
    private JSONObject result(JSONArray rows,int page,int total) throws Exception {
        return new JSONObject().put("code",1).put("msg","success").put("list",rows).put("page",page).put("pagecount",(total+19)/20).put("limit",20).put("total",total);
    }
    private int page(String p) {
        try{return Math.max(1,Integer.parseInt(p));}catch(NumberFormatException e){return 1;}
    }
    private JSONObject list(String category,String key,int page) throws Exception {
        return list(state.catalog,category,key,page);
    }
    private JSONObject list(HarborCatalog catalog,String category,String key,int page) throws Exception {
        JSONArray rows=new JSONArray(); int total=0;
        for(String[] f:catalog.query(category,key)){
            total++; if((long)(page-1)*20<total && total<=(long)page*20) rows.put(row(f,false));
        }
        return result(rows,page,total);
    }
    public String homeContent(boolean filter) throws Exception {
        HarborLoadResult current=state;
        HarborCatalog catalog=current.catalog;
        JSONArray c=new JSONArray();
        if(!catalog.query("animation","").isEmpty()) c.put(new JSONObject().put("type_id","animation").put("type_name","动画"));
        if(!catalog.query("scifi","").isEmpty()) c.put(new JSONObject().put("type_id","scifi").put("type_name","科幻"));
        return list(catalog,"","",1).put("class",c).put("harbor_status",new JSONArray(current.status)).toString();
    }
    public String homeVideoContent() throws Exception {return list("","",1).toString();}
    public String categoryContent(String tid,String pg,boolean filter,HashMap<String,String> ext) throws Exception {return list(tid,"",page(pg)).toString();}
    public String detailContent(List<String> ids) throws Exception {
        JSONArray rows=new JSONArray();
        for(String[] f:state.catalog.query("","")) if(ids.contains(f[0])) rows.put(row(f,true));
        return result(rows,1,rows.length()).toString();
    }
    public String searchContent(String key,boolean quick) throws Exception {return searchContent(key,quick,"1");}
    public String searchContent(String key,boolean quick,String pg) throws Exception {return list("",key==null?"":key,page(pg)).toString();}
    public String playerContent(String flag,String id,List<String> flags) throws Exception {
        HarborCatalog catalog=state.catalog;
        if("诊断短片（非正片）".equals(flag)&&id!=null&&id.startsWith("diag-")&&catalog.get(id.substring(5))!=null)
            return new JSONObject().put("parse",0).put("url",STATIC+"diagnostic.mp4").toString();
        if("Blender 官方备选".equals(flag)&&"official-bunny".equals(id)&&catalog.get("bunny")!=null)
            return new JSONObject().put("parse",0).put("url","https://download.blender.org/peach/bigbuckbunny_movies/big_buck_bunny_480p_h264.mov").toString();
        String[] f=catalog.get(id);
        if(f!=null&&"Harbor".equals(flag)) return new JSONObject().put("parse",0).put("url",f[4]).toString();
        return new JSONObject().put("parse",0).put("url","").toString();
    }
}
