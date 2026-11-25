package com.github.catvod.spider;

/** Atomically published catalog and sanitized provider diagnostics. */
final class HarborLoadResult {
    final HarborCatalog catalog;
    final String status;
    HarborLoadResult(HarborCatalog catalog,String status){
        this.catalog=catalog;
        this.status=status;
    }
}
