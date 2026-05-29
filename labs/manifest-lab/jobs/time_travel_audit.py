import polars as pl

# VULNERABLE state vs NEWEST PATCHED state
T1 = "data/minio/silver/snapshots/sboms_20260425223112.parquet"
T3 = "data/minio/silver/snapshots/sboms_20260425223450.parquet"

def run_audit():
    print("🕵️ Starting Forensic Time-Travel Audit...")
    
    df_t1 = pl.read_parquet(T1)
    df_t3 = pl.read_parquet(T3)
    
    # Calculate the Difference
    diff = df_t1.join(df_t3, on=["component_name", "component_version"], how="full", suffix="_new")
    
    # Identify improved security posture (CRITICAL -> NONE)
    improved = diff.filter(
        (pl.col("severity") == "CRITICAL") & (pl.col("severity_new") == "NONE")
    )
    
    print("\n🚀 Posture Improvement Report:")
    if not improved.is_empty():
        print(f"✅ Found {len(improved)} component(s) that were patched!")
        for row in improved.to_dicts():
            print(f" - {row['component_name']}@{row['component_version']}: CRITICAL -> SAFE")
    else:
        print("No improvements found between these snapshots.")

if __name__ == "__main__":
    run_audit()
