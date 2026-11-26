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
    private static final String STATIC="https://gh-proxy.com/https://raw.githubusercontent.com/Jilinkin/anjun-harbor/abefe13500b01b8a7474ad9d58271c49c9b070cb/android-demo/rc2/";
    private static final HarborCatalog DEMO=new HarborCatalog(new String[][]{
        HarborData.FILMS[0],HarborData.FILMS[1],
        {"diagnostic","Harbor 播放测试","diagnostic","2026",STATIC+"diagnostic.mp4","Harbor 原创五秒测试画面和提示音，非正片。"}
    });
    private static String[] withSource(String[] film,String url,String note){
        String[] copy=film.clone();copy[4]=url;copy[5]+=" | "+note;return copy;
    }
    private static final HarborCatalog RC4=new HarborCatalog(new String[][]{
        withSource(HarborData.FILMS[0],"https://download.blender.org/peach/bigbuckbunny_movies/big_buck_bunny_480p_h264.mov","Blender 官方 480p 候选，国内播放待验。"),
        withSource(HarborData.FILMS[1],"https://mirrors.aliyun.com/blender/demo/movies/ToS/tears_of_steel_720p.mov","阿里云 Blender 镜像 720p 候选，国内播放待验。"),
        DEMO.get("diagnostic")
    });
    private static final HarborLoadResult DEFAULT=new HarborLoadResult(CATALOG,"[]");
    private volatile HarborLoadResult state=DEFAULT;
    public synchronized void init(Context c) {state=DEFAULT;}
    public synchronized void init(Context c,String ext) throws Exception {
        if(ext==null||ext.trim().isEmpty()){state=DEFAULT;return;}
        if("harbor-rc4-demo".equals(ext)){state=new HarborLoadResult(RC4,"[]");return;}
        if("harbor-rc3-demo".equals(ext)){state=new HarborLoadResult(DEMO,"[]");return;}
        // Never briefly expose the default or previous catalog on invalid input.
        state=new HarborLoadResult(new HarborCatalog(new String[0][]),"[]");
        state=HarborRegistry.loadDetailed(ext,CATALOG);
    }
    public String harborDiagnostics(){return state.status;}
    private JSONObject row(String[] f,boolean detail) throws Exception {
        JSONObject j=new JSONObject().put("vod_id",f[0]).put("vod_name",f[1])
            .put("type_id",f[2]).put("type_name",f[2].equals("animation")?"动画":f[2].equals("scifi")?"科幻":"播放测试").put("vod_year",f[3]).put("vod_pic",STATIC+("diagnostic".equals(f[0])?"bunny":f[0])+".png").put("vod_remarks","diagnostic".equals(f[0])?"五秒测试":"开放影片");
        if(detail) j.put("vod_content",f[5]).put("vod_play_from","Harbor").put("vod_play_url","Full$"+f[0]);
        return j;
    }
    private JSONObject result(JSONArray rows,int page,int total) throws Exception {
        return new JSONObject().put("list",rows).put("page",page).put("pagecount",(total+19)/20).put("limit",20).put("total",total);
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
        if(!catalog.query("diagnostic","").isEmpty()) c.put(new JSONObject().put("type_id","diagnostic").put("type_name","播放测试"));
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
        String[] f=state.catalog.get(id);
        if(f!=null&&"Harbor".equals(flag)) return new JSONObject().put("parse",0).put("url",f[4]).toString();
        return new JSONObject().put("parse",0).put("url","").toString();
    }
}
