package com.github.catvod.spider;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import org.json.JSONObject;

/** Single endpoint, memory only. Every cached response is revalidated before use. */
final class HarborCache {
    interface Fetcher { JSONObject fetch() throws Exception; }
    static final long FRESH=60000000000L, MAX_AGE=300000000000L, RETRY=15000000000L;
    private String data;
    private long storedAt,failedAt;
    private boolean backedOff;
    private void clear(){data=null;backedOff=false;}
    private HarborLoadResult cached(HarborCatalog reviewed,String status)throws Exception {
        try{return new HarborLoadResult(HarborRegistry.cms(new JSONObject(data),reviewed),status);}
        catch(Exception ex){clear();throw ex;}
    }
    synchronized HarborLoadResult get(HarborCatalog reviewed,Fetcher fetcher,long now)throws Exception {
        if(Thread.currentThread().isInterrupted())throw new InterruptedException();
        long age=now-storedAt;
        if(data!=null&&(age<0||age>=MAX_AGE))clear();
        if(data!=null&&age<FRESH)return cached(reviewed,"cache_fresh");
        if(data!=null&&backedOff&&now-failedAt>=0&&now-failedAt<RETRY)
            return cached(reviewed,"cache_stale");
        JSONObject response;
        try {
            response=fetcher==null?HarborNetwork.fetch():fetcher.fetch();
        }catch(Exception ex){
            if(ex instanceof InterruptedException||Thread.currentThread().isInterrupted())throw ex;
            // Only connection establishment, DNS and socket timeout failures are recoverable.
            if(data!=null&&(ex instanceof ConnectException||ex instanceof UnknownHostException||ex instanceof SocketTimeoutException)){
                backedOff=true;failedAt=now;
                return cached(reviewed,"cache_stale");
            }
            clear();throw ex;
        }
        try {
            if(Thread.currentThread().isInterrupted())throw new InterruptedException();
            HarborCatalog validated=HarborRegistry.cms(response,reviewed);
            String serialized=response.toString();
            if(serialized.length()>HarborNetwork.MAX_BYTES)throw new IllegalArgumentException("Cache size limit");
            data=serialized;storedAt=now;backedOff=false;
            return new HarborLoadResult(validated,"network");
        }catch(Exception ex){clear();throw ex;}
    }
}
