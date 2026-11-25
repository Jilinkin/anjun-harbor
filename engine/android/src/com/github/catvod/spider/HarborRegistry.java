package com.github.catvod.spider;

import java.util.ArrayList;
import java.util.HashSet;
import org.json.JSONArray;
import org.json.JSONObject;

/** Built-in offline adapter registry for the reviewed open-film fixture catalog. */
final class HarborRegistry {
    private static void require(boolean ok,String message) {
        if(!ok)throw new IllegalArgumentException(message);
    }
    static HarborCatalog load(String inline,HarborCatalog reviewed)throws Exception {
        require(inline.length()<=65536,"Input limit");
        JSONObject root=new JSONObject(inline);
        Object version=root.get("version");
        require(version instanceof Integer,"Invalid version");
        if(((Integer)version)==1)return HarborRules.load(inline,reviewed);
        require(((Integer)version)==2&&root.length()==2&&root.has("providers"),"Invalid registry");
        JSONArray providers=root.getJSONArray("providers");
        require(providers.length()>=1&&providers.length()<=8,"Provider limit");
        HashSet<String> seenProviders=new HashSet<>();
        HashSet<String> seenTitles=new HashSet<>();
        ArrayList<String[]> merged=new ArrayList<>();
        for(int i=0;i<providers.length();i++){
            JSONObject provider=providers.getJSONObject(i);
            require(provider.length()==3&&provider.has("id")&&provider.has("kind")&&provider.has("snapshot"),"Unknown provider option");
            Object identity=provider.get("id");
            require(identity instanceof String&&((String)identity).matches("[a-z][a-z0-9_-]{0,39}")&&seenProviders.add((String)identity),"Invalid or duplicate provider");
            Object kind=provider.get("kind");
            JSONObject data=provider.getJSONObject("snapshot");
            HarborCatalog items;
            if("json-snapshot".equals(kind)){
                items=HarborRules.load(data.toString(),reviewed);
            }else if("cms-snapshot".equals(kind)){
                items=cms(data,reviewed);
            }else throw new IllegalArgumentException("Unknown adapter");
            for(String[] row:items.query("","")){
                if(seenTitles.add(row[0]))merged.add(row);
            }
        }
        return new HarborCatalog(merged.toArray(new String[0][]));
    }
    private static HarborCatalog cms(JSONObject data,HarborCatalog reviewed)throws Exception{
        require(data.length()==1&&data.has("list"),"Invalid CMS fixture");
        JSONArray rows=data.getJSONArray("list");
        require(rows.length()<=100,"Row limit");
        ArrayList<String[]> out=new ArrayList<>();
        HashSet<String> seen=new HashSet<>();
        for(int i=0;i<rows.length();i++){
            JSONObject row=rows.getJSONObject(i);
            require(row.length()==3&&row.has("vod_id")&&row.has("vod_name")&&row.has("vod_play_url"),"Invalid CMS fields");
            Object id=row.get("vod_id"),name=row.get("vod_name"),play=row.get("vod_play_url");
            require(id instanceof String&&name instanceof String&&play instanceof String,"Invalid CMS type");
            String[] canonical=reviewed.get((String)id);
            require(canonical!=null&&canonical[1].equals(name)&&("Full$"+canonical[4]).equals(play)&&seen.add((String)id),"Unreviewed or duplicate fixture");
            out.add(canonical);
        }
        return new HarborCatalog(out.toArray(new String[0][]));
    }
}
