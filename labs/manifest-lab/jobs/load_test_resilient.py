import asyncio
import httpx
import time
import random

URL = "http://localhost:8001/ingest/sbom"
NUM_REQUESTS = 500
BATCH_SIZE = 50
MAX_RETRIES = 5

async def send_with_backoff(client, i):
    """Sends a request with exponential backoff if a 429 is received."""
    payload = [{"name": f"resilient-comp-{i}", "version": "1.0.0"}]
    retry_count = 0
    
    while retry_count <= MAX_RETRIES:
        try:
            resp = await client.post(URL, json=payload, timeout=5.0)
            
            if resp.status_code == 202:
                return "SUCCESS"
            
            if resp.status_code == 429:
                # Backoff logic: 2^retry + jitter
                wait_time = (2 ** retry_count) + random.uniform(0, 1)
                print(f"⚠️  [Request {i}] Received 429 (Full). Retrying in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
                retry_count += 1
                continue
            
            return f"ERROR_{resp.status_code}"
            
        except Exception as e:
            return f"FAILED_{str(e)}"
            
    return "MAX_RETRIES_EXCEEDED"

async def run_resilient_test():
    print(f"🚀 Starting Resilient Load Test ({NUM_REQUESTS} requests)...")
    print(f"Strategy: Exponential Backoff (Max {MAX_RETRIES} retries)")
    
    start_time = time.time()
    stats = {"SUCCESS": 0, "MAX_RETRIES_EXCEEDED": 0}
    
    async with httpx.AsyncClient() as client:
        for i in range(0, NUM_REQUESTS, BATCH_SIZE):
            tasks = [send_with_backoff(client, j) for j in range(i, i + BATCH_SIZE)]
            results = await asyncio.gather(*tasks)
            
            for res in results:
                stats[res] = stats.get(res, 0) + 1
            
            print(f"Progress: {i + BATCH_SIZE}/{NUM_REQUESTS} | Completed: {stats['SUCCESS']}")

    total_time = time.time() - start_time
    print("\n--- Resilient Test Results ---")
    print(f"Total Requests: {NUM_REQUESTS}")
    print(f"Total Time:     {total_time:.2f}s")
    print(f"✅ Final Success: {stats['SUCCESS']}/{NUM_REQUESTS}")
    
    if stats.get("MAX_RETRIES_EXCEEDED", 0) > 0:
        print(f"❌ Dropped: {stats['MAX_RETRIES_EXCEEDED']} (Server remained full too long)")
    else:
        print("\n🏆 PERFECT RECOVERY: All 429s were successfully replayed and accepted.")

if __name__ == "__main__":
    asyncio.run(run_resilient_test())
