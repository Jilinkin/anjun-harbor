package com.github.catvod.spider;
import org.json.JSONObject;
import org.json.JSONArray;
public final class RulesTest {
    public static void main(String[] args)throws Exception{
        HarborCatalog c=new HarborCatalog(HarborData.FILMS);
        String[] f=c.get("bunny");
        JSONObject row=new JSONObject().put("identity",f[0]).put("title",f[1]).put("media",f[4]);
        JSONObject fields=new JSONObject().put("id",new JSONArray().put("identity")).put("name",new JSONArray().put("title")).put("url",new JSONArray().put("media"));
        JSONObject root=new JSONObject().put("version",1).put("data",new JSONObject().put("entries",new JSONArray().put(row))).put("items",new JSONArray().put("entries")).put("fields",fields);
        HarborCatalog mapped=HarborRules.load(root.toString(),c);
        if(mapped.query("","").size()!=1||mapped.get("bunny")==null||mapped.get("steel")!=null)throw new AssertionError("Mapping");
        row.put("media","https://example.com/not-reviewed.mp4");
        try{HarborRules.load(root.toString(),c);throw new AssertionError("Unexpected media accepted");}catch(IllegalArgumentException expected){}
        System.out.println("Rule tests passed");
    }
}
