package com.github.catvod.spider;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.Proxy;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import javax.net.ssl.HttpsURLConnection;
import org.json.JSONObject;

/** Fixed, first-party open-film metadata endpoint; no arbitrary URL input. */
final class HarborNetwork {
    static final String ENDPOINT="https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/engine/android/network-demo.json";
    static final int MAX_BYTES=65536;

    static JSONObject fetch()throws Exception{
        HttpsURLConnection connection=(HttpsURLConnection)new URL(ENDPOINT).openConnection(Proxy.NO_PROXY);
        return read(connection);
    }
    // Package-private transport seam for deterministic JVM tests.
    static JSONObject read(HttpURLConnection connection)throws Exception{
        try{
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(5000);
            connection.setUseCaches(false);
            connection.setRequestMethod("GET");
            connection.setRequestProperty("Accept","application/json");
            connection.setRequestProperty("Accept-Encoding","identity");
            long start=System.nanoTime();
            if(connection.getResponseCode()!=200)throw new IOException("Unexpected HTTP status");
            String encoding=connection.getHeaderField("Content-Encoding");
            if(encoding!=null&&!encoding.equalsIgnoreCase("identity"))throw new IOException("Unsupported encoding");
            int length=connection.getContentLength();
            if(length>MAX_BYTES)throw new IOException("Response limit");
            ByteArrayOutputStream output=new ByteArrayOutputStream();
            try(InputStream input=connection.getInputStream()){
                byte[] buf=new byte[4096];int n;
                while((n=input.read(buf))!=-1){
                    if(n==0)throw new IOException("Empty read");
                    if(output.size()+n>MAX_BYTES)throw new IOException("Response limit");
                    if(System.nanoTime()-start>15000000000L)throw new IOException("Read deadline");
                    output.write(buf,0,n);
                }
            }
            if(System.nanoTime()-start>15000000000L)throw new IOException("Read deadline");
            if(length>=0&&length!=output.size())throw new IOException("Truncated response");
            return new JSONObject(new String(output.toByteArray(),StandardCharsets.UTF_8));
        }finally{connection.disconnect();}
    }
}
