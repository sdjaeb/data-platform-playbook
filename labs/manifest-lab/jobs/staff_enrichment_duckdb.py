import duckdb
import weaviate
import ollama

# Configuration
SILVER_FILE = "data/minio/silver/enriched-sboms.parquet"
WEAVIATE_URL = "localhost"
WEAVIATE_PORT = 8083
EMBED_MODEL = "nomic-embed-text"

def run_staff_enrichment():
    print("🦆 Initializing DuckDB Analytical Engine...")
    con = duckdb.connect(database=':memory:')
    
    # STAFF LEVEL: We use DuckDB native COPY for zero-copy Parquet writing
    print("📊 Performing Analytical Join and Forensic Re-tagging...")
    
    # Forensic re-tagging SQL
    sql = f"""
        SELECT 
            component_name, 
            component_version, 
            CASE 
                WHEN component_name = 'log4j' AND component_version = '2.14.1' THEN 'CRITICAL'
                ELSE severity 
            END as severity,
            CASE 
                WHEN component_name = 'log4j' AND component_version = '2.14.1' THEN 'CVE-2021-44228'
                ELSE cve_id 
            END as cve_id
        FROM read_parquet('{SILVER_FILE}')
    """
    
    # Execute and write back to Parquet natively
    con.execute(f"COPY ({sql}) TO '{SILVER_FILE}' (FORMAT PARQUET)")
    print("✅ Silver Layer updated via native DuckDB COPY.")

    # Get results for Weaviate sync
    high_risk_df = con.execute(f"SELECT * FROM read_parquet('{SILVER_FILE}') WHERE severity IN ('HIGH', 'CRITICAL')").df()
    print(f"🔥 Found {len(high_risk_df)} Critical/High threats for Vector Sync.")

    # Connect to Weaviate (v4 Style)
    print("🧠 Syncing with Weaviate v4 Vector DB...")
    client = weaviate.connect_to_local(
        host=WEAVIATE_URL,
        port=WEAVIATE_PORT
    )
    
    try:
        collection = client.collections.get("SecurityMetadata")
        
        for _, row in high_risk_df.iterrows():
            summary = f"ALERT: {row['component_name']}@{row['component_version']} has {row['severity']} vulnerability {row['cve_id']}."
            
            # Generate Vector via Local Ollama
            vector = ollama.embeddings(model=EMBED_MODEL, prompt=summary)['embedding']
            
            # Upsert into Weaviate
            collection.data.insert(
                properties={
                    "component_name": str(row['component_name']),
                    "version": str(row['component_version']),
                    "severity": str(row['severity']),
                    "cve_id": str(row['cve_id']),
                    "summary": summary
                },
                vector=vector
            )
        print("🚀 Staff Enrichment Sync Complete.")

    finally:
        client.close()

if __name__ == "__main__":
    run_staff_enrichment()
