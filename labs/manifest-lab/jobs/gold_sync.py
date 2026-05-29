import polars as pl
import os
from pymongo import MongoClient, UpdateOne
import redis
from datetime import datetime

# Configuration
SILVER_FILE = "data/minio/silver/enriched-sboms.parquet"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "Manifest_gold"
COLLECTION_NAME = "vulnerability_status"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = 6379

def sync_to_gold():
    print(f"🚀 Starting Gold sync job at {datetime.now()}")
    
    try:
        # 1. Read Silver Parquet
        df = pl.read_parquet(SILVER_FILE)
        
        # 2. Prepare MongoDB Client
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Staff-level: Ensure index on component_id for fast point lookups
        # In this context, we'll use a unique identifier (e.g., component_name + version)
        collection.create_index("component_id", unique=True)
        
        # 3. Bulk Upsert into MongoDB
        operations = []
        for row in df.to_dicts():
            component_id = f"{row['component_name']}@{row['component_version']}"
            operations.append(
                UpdateOne(
                    {"component_id": component_id},
                    {"$set": {
                        "component_name": row["component_name"],
                        "version": row["component_version"],
                        "cve_id": row.get("cve_id", "NONE"),
                        "severity": row.get("severity", "NONE"),
                        "last_updated": datetime.now()
                    }},
                    upsert=True
                )
            )
        
        if operations:
            result = collection.bulk_write(operations)
            print(f"✅ Upserted {result.upserted_count} new and updated {result.modified_count} existing records.")
        
        # 4. Invalidate/Warm Redis Cache
        # For the lab, we'll just clear the cache to ensure fresh data
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        r.flushdb()
        print("✅ Redis cache invalidated.")

    except Exception as e:
        print(f"❌ Gold sync failed: {str(e)}")

if __name__ == "__main__":
    sync_to_gold()
