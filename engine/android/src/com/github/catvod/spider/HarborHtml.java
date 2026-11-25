package com.github.catvod.spider;

import java.io.StringReader;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.InputSource;
import org.json.JSONObject;

/** Restricted well-formed XHTML snapshot mapper. No browser, network or executable rules. */
final class HarborHtml {
    private static void require(boolean ok,String message){
        if(!ok)throw new IllegalArgumentException(message);
    }
    private static boolean blocked(Element e){
        String tag=e.getTagName().toLowerCase(java.util.Locale.ROOT);
        return tag.equals("script")||tag.equals("style")||tag.equals("iframe")||tag.equals("object")||tag.equals("template")||tag.equals("noscript");
    }
    private static Element tree(String source)throws Exception{
        require(source.length()<=32768,"Snapshot limit");
        // No declarations, DTDs, external entities or processing instructions.
        require(!source.contains("<!")&&!source.contains("<?"),"Markup declarations forbidden");
        DocumentBuilderFactory f=DocumentBuilderFactory.newInstance();
        f.setNamespaceAware(false);
        f.setExpandEntityReferences(false);
        Element root=f.newDocumentBuilder().parse(new InputSource(new StringReader(source))).getDocumentElement();
        int[] count={0};validate(root,0,count);
        return root;
    }
    private static void validate(Element root,int depth,int[] count){
        require(depth<=40&&++count[0]<=4000,"Tree limit");
        for(Node n=root.getFirstChild();n!=null;n=n.getNextSibling())
            if(n instanceof Element)validate((Element)n,depth+1,count);
    }
    private static boolean matches(Element e,String token){
        if(blocked(e))return false;
        int dot=token.indexOf('.');
        String tag=dot<0?token:token.substring(0,dot);
        if(!tag.isEmpty()&&!tag.equals(e.getTagName()))return false;
        if(dot<0)return true;
        for(String cls:e.getAttribute("class").split("\\s+"))
            if(cls.equals(token.substring(dot+1)))return true;
        return false;
    }
    private static void descendants(Element e,String token,List<Element> out){
        if(blocked(e))return;
        for(Node n=e.getFirstChild();n!=null;n=n.getNextSibling())
            if(n instanceof Element){
                Element child=(Element)n;
                if(matches(child,token))out.add(child);
                descendants(child,token,out);
            }
    }
    private static List<Element> select(Element root,JSONObject selector)throws Exception{
        require(selector.length()==2&&selector.has("kind")&&selector.has("path"),"Invalid selector");
        String kind=selector.getString("kind"),path=selector.getString("path");
        require(path.length()<=150,"Selector limit");
        List<Element> out=new ArrayList<>();
        if(kind.equals("css")){
            require(path.matches("(?:[a-zA-Z][a-zA-Z0-9_-]*(?:\\.[a-zA-Z0-9_-]+)?|\\.[a-zA-Z0-9_-]+)"),"Unsupported CSS");
            descendants(root,path,out);
        }else if(kind.equals("xpath")){
            require(path.matches("\\./[a-zA-Z][a-zA-Z0-9_-]*(?:/[a-zA-Z][a-zA-Z0-9_-]*){0,4}"),"Unsupported XPath");
            out.add(root);
            for(String token:path.substring(2).split("/")){
                List<Element> next=new ArrayList<>();
                for(Element parent:out)if(!blocked(parent))
                    for(Node n=parent.getFirstChild();n!=null;n=n.getNextSibling())
                        if(n instanceof Element&&matches((Element)n,token))next.add((Element)n);
                out=next;
            }
        }else throw new IllegalArgumentException("Unknown selector");
        return out;
    }
    private static String field(Element item,JSONObject spec)throws Exception{
        require(spec.length()==2&&spec.has("selector")&&spec.has("attribute"),"Invalid field");
        Element e=item;
        if(!spec.isNull("selector")){
            List<Element> found=select(item,spec.getJSONObject("selector"));
            require(found.size()==1,"Expected unique field");
            e=found.get(0);
        }
        String attr=spec.getString("attribute"),value;
        if(attr.equals("text")){
            StringBuilder b=new StringBuilder();
            for(Node n=e.getFirstChild();n!=null;n=n.getNextSibling()){
                require(n.getNodeType()==Node.TEXT_NODE,"Only direct text fields supported");
                b.append(n.getNodeValue());
            }
            value=b.toString().trim();
        }else{
            require(attr.equals("data-id")||attr.equals("href"),"Unsupported attribute");
            value=e.getAttribute(attr);
        }
        require(!value.isEmpty()&&value.length()<=2000,"Invalid field value");
        return value;
    }
    static HarborCatalog load(JSONObject data,HarborCatalog reviewed)throws Exception{
        require(data.length()==4&&data.has("version")&&data.has("html")&&data.has("items")&&data.has("fields")&&Integer.valueOf(1).equals(data.get("version")),"Invalid HTML rule");
        Element root=tree(data.getString("html"));
        JSONObject fields=data.getJSONObject("fields");
        require(fields.length()==3&&fields.has("id")&&fields.has("name")&&fields.has("url"),"Invalid fields");
        List<Element> nodes=select(root,data.getJSONObject("items"));
        require(nodes.size()<=100,"Row limit");
        HashSet<String> seen=new HashSet<>();
        ArrayList<String[]> out=new ArrayList<>();
        for(Element item:nodes){
            String id=field(item,fields.getJSONObject("id"));
            String name=field(item,fields.getJSONObject("name"));
            String url=field(item,fields.getJSONObject("url"));
            String[] canonical=reviewed.get(id);
            require(canonical!=null&&canonical[1].equals(name)&&canonical[4].equals(url)&&seen.add(id),"Unreviewed or duplicate fixture");
            out.add(canonical);
        }
        return new HarborCatalog(out.toArray(new String[0][]));
    }
}
