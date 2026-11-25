package com.github.catvod.spider;

import java.util.ArrayList;
import java.util.HashSet;
import org.json.JSONArray;
import org.json.JSONObject;

/** Inline declarative mapping of reviewed demo records only, no network or code evaluation. */
final class HarborRules {
    private static Object select(Object node,JSONArray path)throws Exception {
        if(path.length()>12)throw new IllegalArgumentException("Path limit");
        for(int i=0;i<path.length();i++){
            Object key=path.get(i);
            if(key instanceof String && node instanceof JSONObject && ((String)key).length()<=100)
                node=((JSONObject)node).get((String)key);
            else if(key instanceof Integer && node instanceof JSONArray && ((Integer)key)>=0)
                node=((JSONArray)node).get((Integer)key);
            else throw new IllegalArgumentException("Invalid path");
        }
        return node;
    }
    private static String str(Object node,JSONArray path)throws Exception {
        Object value=select(node,path);
        if(!(value instanceof String)||((String)value).isEmpty()||((String)value).length()>2000)
            throw new IllegalArgumentException("Invalid string");
        return (String)value;
    }
    static HarborCatalog load(String inline,HarborCatalog reviewed)throws Exception{
        if(inline.length()>65536)throw new IllegalArgumentException("Input limit");
        JSONObject root=new JSONObject(inline);
        if(root.length()!=4||root.getInt("version")!=1||!root.has("data")||!root.has("items")||!root.has("fields"))
            throw new IllegalArgumentException("Invalid rule");
        JSONObject f=root.getJSONObject("fields");
        if(f.length()!=3)throw new IllegalArgumentException("Invalid fields");
        JSONArray ids=f.getJSONArray("id"),names=f.getJSONArray("name"),urls=f.getJSONArray("url");
        Object selected=select(root.get("data"),root.getJSONArray("items"));
        if(!(selected instanceof JSONArray))throw new IllegalArgumentException("Invalid rows");
        JSONArray rows=(JSONArray)selected;
        if(rows.length()>100)throw new IllegalArgumentException("Row limit");
        ArrayList<String[]> out=new ArrayList<>();
        HashSet<String> seen=new HashSet<>();
        for(int i=0;i<rows.length();i++){
            Object row=rows.get(i);
            String id=str(row,ids), name=str(row,names), url=str(row,urls);
            String[] canonical=reviewed.get(id);
            if(canonical==null||!canonical[1].equals(name)||!canonical[4].equals(url)||!seen.add(id))
                throw new IllegalArgumentException("Unreviewed or duplicate record");
            out.add(canonical);
        }
        return new HarborCatalog(out.toArray(new String[0][]));
    }
}
