import polars as pl

# Updated vulnerabilities data (Log4j 2.14.1 is now PATCHED)
vulnerabilities = pl.DataFrame({
    "component_name": ["log4j", "openssl", "glibc"],
    "version": ["2.14.1", "1.1.1k", "2.31"],
    "cve_id": ["NONE", "CVE-2021-3711", "CVE-2021-33574"],
    "severity": ["NONE", "HIGH", "CRITICAL"]
})

vulnerabilities.write_parquet("labs/manifest-lab/vulnerabilities.parquet")
print("✅ Updated vulnerabilities: Log4j 2.14.1 is now marked as Safe.")
