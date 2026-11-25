package com.github.catvod.spider;

import java.util.ArrayList;
import java.util.HashSet;
import org.json.JSONArray;
import org.json.JSONObject;

/** Built-in snapshot registry with explicit first-party demo network mode. */
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
        int networkCount=0;
        // Validate every provider shape before making any network request.
        for(int i=0;i<providers.length();i++){
            JSONObject provider=providers.getJSONObject(i);
            require(provider.has("id")&&provider.has("kind"),"Missing provider identity");
            Object identity=provider.get("id");
            require(identity instanceof String&&((String)identity).matches("[a-z][a-z0-9_-]{0,39}")&&seenProviders.add((String)identity),"Invalid or duplicate provider");
            Object kind=provider.get("kind");
            if("cms-network-demo".equals(kind)){
                require(provider.length()==3&&Boolean.TRUE.equals(provider.opt("allow_network"))&&++networkCount<=1,"Explicit network opt-in required");
            }else{
                require(("cms-snapshot".equals(kind)||"json-snapshot".equals(kind)||"html-snapshot".equals(kind))&&provider.length()==3&&provider.opt("snapshot") instanceof JSONObject,"Unknown adapter or options");
            }
        }
        for(int i=0;i<providers.length();i++){
            JSONObject provider=providers.getJSONObject(i);
            Object kind=provider.get("kind");
            HarborCatalog items;
            if("cms-network-demo".equals(kind)){
                items=cms(HarborNetwork.fetch(),reviewed);
            }else{
            JSONObject data=provider.getJSONObject("snapshot");
            if("json-snapshot".equals(kind)){
                items=HarborRules.load(data.toString(),reviewed);
            }else if("html-snapshot".equals(kind)){
                items=HarborHtml.load(data,reviewed);
            }else if("cms-snapshot".equals(kind)){
                items=cms(data,reviewed);
            }else throw new IllegalArgumentException("Unknown adapter");
            }
            for(String[] row:items.query("","")){
                if(seenTitles.add(row[0]))merged.add(row);
            }
        }
        return new HarborCatalog(merged.toArray(new String[0][]));
    }
    static HarborCatalog cms(JSONObject data,HarborCatalog reviewed)throws Exception{
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
