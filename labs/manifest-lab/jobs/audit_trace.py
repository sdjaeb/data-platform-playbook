import os
import sys
import polars as pl
import httpx

# Configuration
CID = "00000e65a4186e4d4a1b382ec66821642f4138fa4317ce46d8f9067850957dfb"
SILVER_FILE = "data/minio/silver/enriched-sboms.parquet"

def run_audit(component_id):
    print(f"🔍 AUDIT TRACE for Component: {component_id}\n" + "="*40)
    
    # 1. Bronze Check
    bronze_path = f"data/minio/bronze/sboms/{CID}.json"
    if os.path.exists(bronze_path):
        print(f"🟢 BRONZE: Found raw evidence at {bronze_path}")
    else:
        print(f"🔴 BRONZE: Raw evidence missing for CID {CID}")

    # 2. Silver Check
    try:
        df = pl.read_parquet(SILVER_FILE)
        name = component_id.split("@")[0]
        version = component_id.split("@")[1] if "@" in component_id else ""
        
        match = df.filter(
            (pl.col("component_name") == name) & 
            (pl.col("component_version") == version)
        )
        if len(match) > 0:
            print(f"🟢 SILVER: Enriched record found (Severity: {match['severity'][0]})")
        else:
            print(f"🟡 SILVER: {component_id} not in Silver yet (Defaulting to clean for demo).")
    except Exception:
        print("🟡 SILVER: Could not read silver parquet.")

    # 3. Gold/API Check (The Serving Path)
    print("\n🌐 API VERDICT (Policy Enforcement):")
    try:
        payload = {"component_id": component_id}
        resp = httpx.post("http://localhost:8000/evaluate", json=payload, timeout=5.0)
        
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "UNKNOWN")
            reason = data.get("reason", "N/A")
            color = "🟢" if status == "APPROVED" else "🔴"
            print(f"{color} VERDICT: {status} ({reason})")
        else:
            print(f"🔴 API Error: {resp.status_code}")
    except Exception as e:
        print(f"🟡 API: Serving layer unreachable or error occurred: {e}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "log4j@2.14.1"
    run_audit(target)
