import os
import json
import redis
import pymysql
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Manifest Staff Serving API")

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# TiDB Configuration (Gold Layer)
TIDB_HOST = os.getenv("TIDB_HOST", "localhost")
TIDB_PORT = int(os.getenv("TIDB_PORT", 4000))
TIDB_USER = os.getenv("TIDB_USER", "root")
TIDB_DB = os.getenv("TIDB_DB", "manifest_gold")

# Redis for high-speed policy cache
cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_db_connection():
    return pymysql.connect(
        host=TIDB_HOST,
        port=TIDB_PORT,
        user=TIDB_USER,
        password="",
        database=TIDB_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

class ComponentRequest(BaseModel):
    component_id: str
    version: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "healthy", "engine": "TiDB + Redis"}

@app.post("/evaluate")
async def evaluate_component(request: ComponentRequest):
    component_id = request.component_id
    
    # 1. Check Cache (Redis) - The 10ms Path
    cached_verdict = cache.get(f"verdict:{component_id}")
    if cached_verdict:
        return json.loads(cached_verdict)

    # 2. Check Gold Layer (TiDB) - The Durable Path
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Simple lookup in the materialized security view
            sql = "SELECT status, severity, reason FROM security_verdicts WHERE component_id = %s"
            cursor.execute(sql, (component_id,))
            result = cursor.fetchone()
            
        if not result:
            # Fallback for demo: if not in TiDB, we check if it's a known bad actor
            if "log4j" in component_id:
                result = {"status": "REJECTED", "severity": "CRITICAL", "reason": "CVE-2021-44228"}
            else:
                result = {"status": "APPROVED", "severity": "NONE", "reason": "No known vulnerabilities"}

        # 3. Update Cache
        cache.setex(f"verdict:{component_id}", 3600, json.dumps(result))
        return result

    except Exception:
        # For the lab, if TiDB is empty/not setup, we provide a forensic fallback
        if "log4j" in component_id:
            return {"status": "REJECTED", "severity": "CRITICAL", "reason": "Forensic Match: log4j vulnerability detected"}
        return {"status": "APPROVED", "severity": "NONE", "reason": "Defaulting to safe (Lab Mode)"}
    finally:
        if 'conn' in locals():
            conn.close()
