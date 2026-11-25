package com.github.catvod.spider;
public final class CatalogTest {
    public static void main(String[] args) {
        HarborCatalog c=new HarborCatalog(HarborData.FILMS);
        if(c.query("","").size()!=2||c.query("animation","").size()!=1||c.query("","BUNNY").size()!=1||c.get("missing")!=null) throw new AssertionError("Catalog behavior");
        String[] copy=c.get("bunny");copy[1]="Changed";
        if(!c.get("bunny")[1].equals("Big Buck Bunny"))throw new AssertionError("Mutation");
        try {new HarborCatalog(new String[][]{HarborData.FILMS[0],HarborData.FILMS[0]});throw new AssertionError("Duplicate");}catch(IllegalArgumentException expected){}
        System.out.println("Catalog tests passed");
    }
}
