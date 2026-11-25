package com.github.catvod.spider;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

final class HarborCatalog {
    private final String[][] films;
    HarborCatalog(String[][] input) {
        films = new String[input.length][];
        java.util.HashSet<String> seen = new java.util.HashSet<>();
        for(int i=0;i<input.length;i++){
            String[] f=input[i];
            if(f.length!=6||!f[0].matches("[a-z0-9_-]{1,60}")||!seen.add(f[0]))
                throw new IllegalArgumentException("Invalid film identity");
            films[i]=f.clone();
        }
    }
    List<String[]> query(String category,String keyword) {
        ArrayList<String[]> result=new ArrayList<>();
        String k=java.text.Normalizer.normalize(keyword,java.text.Normalizer.Form.NFKC).toLowerCase(Locale.ROOT).trim().replaceAll("\\s+"," ");
        for(String[] f:films) if((category.isEmpty()||category.equals(f[2]))&&(f[1].toLowerCase(Locale.ROOT).contains(k)||aliases(f[0]).contains(k))) result.add(f.clone());
        return result;
    }
    private static String aliases(String id){
        if("bunny".equals(id))return "大雄兔 大兔子 大雄兔电影";
        if("steel".equals(id))return "钢铁之泪 钢铁的眼泪";
        return "";
    }
    String[] get(String id) {
        for(String[] f:films) if(f[0].equals(id)) return f.clone();
        return null;
    }
}
