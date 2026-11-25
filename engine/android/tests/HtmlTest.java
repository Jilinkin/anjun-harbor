package com.github.catvod.spider;
import org.json.JSONObject;
import org.json.JSONArray;

public final class HtmlTest {
    static JSONObject sel(String kind,String path)throws Exception{return new JSONObject().put("kind",kind).put("path",path);}
    static JSONObject field(Object selector,String attr)throws Exception{return new JSONObject().put("selector",selector).put("attribute",attr);}
    static JSONObject fixture(String source)throws Exception{
        return new JSONObject().put("version",1).put("html",source).put("items",sel("css","article.film"))
            .put("fields",new JSONObject().put("id",field(JSONObject.NULL,"data-id")).put("name",field(sel("xpath","./h2"),"text")).put("url",field(sel("css","a.media"),"href")));
    }
    static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);}
    static void reject(JSONObject rule,HarborCatalog c)throws Exception{
        try{HarborHtml.load(rule,c);throw new AssertionError("Invalid input accepted");}
        catch(IllegalArgumentException expected){}
    }
    public static void main(String[] args)throws Exception{
        HarborCatalog c=new HarborCatalog(HarborData.FILMS);
        String[] f=c.get("bunny");
        String article="<article class=\"film\" data-id=\""+f[0]+"\"><h2>"+f[1]+"</h2><a class=\"media\" href=\""+f[4]+"\">Full</a></article>";
        JSONObject rule=fixture("<html><body>"+article+"</body></html>");
        check(HarborHtml.load(rule,c).query("","").size()==1,"CSS and XPath extraction");
        check(HarborHtml.load(fixture("<html><script>"+article+"</script></html>"),c).query("","").isEmpty(),"Script subtree ignored");
        reject(fixture("<!DOCTYPE html [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><html/>"),c);
        reject(fixture("<?xml version='1.0'?><html/>"),c);
        reject(fixture("<html>"+article+article+"</html>"),c);
        reject(fixture("<html>"+article.replace(f[4],"https://example.invalid/other")+"</html>"),c);
        JSONObject invalid=fixture("<html>"+article+"</html>");invalid.put("items",sel("xpath","//article"));
        reject(invalid,c);
        JSONObject mixed=new JSONObject().put("version",2).put("providers",new JSONArray().put(new JSONObject().put("id","html").put("kind","html-snapshot").put("snapshot",rule)));
        check(HarborRegistry.load(mixed.toString(),c).get("bunny")!=null,"Registry integration");
        System.out.println("Restricted XHTML snapshot checks passed");
    }
}
