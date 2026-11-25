package com.github.catvod.spider;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import org.json.JSONArray;
import org.json.JSONObject;

public final class NetworkTest {
    static class Mock extends HttpURLConnection {
        byte[] body;int status,length;String encoding;boolean closed=false,opened=false;
        Mock(byte[] body,int status,int length,String encoding)throws Exception{
            super(new URL("https://example.invalid/demo"));
            this.body=body;this.status=status;this.length=length;this.encoding=encoding;
        }
        public int getResponseCode(){return status;}
        public int getContentLength(){return length;}
        public String getHeaderField(String name){return encoding;}
        public InputStream getInputStream(){opened=true;return new ByteArrayInputStream(body);}
        public void disconnect(){closed=true;}
        public boolean usingProxy(){return false;}
        public void connect(){}
    }
    private static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);}
    private static void reject(Mock m)throws Exception{
        try{HarborNetwork.read(m);throw new AssertionError("Bad response accepted");}
        catch(IOException expected){}
        check(m.closed,"Disconnected");
    }
    public static void main(String[] args)throws Exception{
        HarborCatalog c=new HarborCatalog(HarborData.FILMS);
        String[] f=c.get("bunny");
        JSONObject row=new JSONObject().put("vod_id",f[0]).put("vod_name",f[1]).put("vod_play_url","Full$"+f[4]);
        byte[] data=new JSONObject().put("list",new JSONArray().put(row)).toString().getBytes(StandardCharsets.UTF_8);
        Mock valid=new Mock(data,200,data.length,null);
        HarborCatalog result=HarborRegistry.cms(HarborNetwork.read(valid),c);
        check(result.get("bunny")!=null&&result.get("steel")==null,"Mapped remote metadata");
        check(valid.closed&&!valid.getInstanceFollowRedirects(),"No redirects");
        check(valid.getConnectTimeout()==5000&&valid.getReadTimeout()==5000,"Timeouts");
        Mock redirect=new Mock(data,302,data.length,null);reject(redirect);check(!redirect.opened,"Redirect body not read");
        reject(new Mock(data,503,data.length,null));
        reject(new Mock(data,200,data.length,"gzip"));
        reject(new Mock(data,200,HarborNetwork.MAX_BYTES+1,null));
        reject(new Mock(new byte[HarborNetwork.MAX_BYTES+1],200,-1,null));
        reject(new Mock(data,200,data.length+1,null));
        row.put("vod_play_url","Full$https://example.invalid/changed.mp4");
        try{HarborRegistry.cms(new JSONObject().put("list",new JSONArray().put(row)),c);throw new AssertionError("Unknown URL accepted");}
        catch(IllegalArgumentException expected){}
        JSONObject provider=new JSONObject().put("id","net").put("kind","cms-network-demo").put("allow_network",false);
        JSONObject manifest=new JSONObject().put("version",2).put("providers",new JSONArray().put(provider));
        try{HarborRegistry.load(manifest.toString(),c);throw new AssertionError("Missing opt-in");}
        catch(IllegalArgumentException expected){}
        provider.put("allow_network",true).put("url","https://example.invalid");
        try{HarborRegistry.load(manifest.toString(),c);throw new AssertionError("URL override accepted");}
        catch(IllegalArgumentException expected){}
        System.out.println("Network transport and review gates passed");
    }
}
