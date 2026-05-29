import asyncio
import httpx
import time

URL = "http://localhost:8001/ingest/sbom"
NUM_REQUESTS = 20000 # Double the buffer size to trigger backpressure
BATCH_SIZE = 500

async def send_request(client, i):
    payload = [{"name": f"component_{i}", "version": "1.0.0"}]
    try:
        resp = await client.post(URL, json=payload, timeout=2.0)
        return resp.status_code
    except Exception:
        return 0

async def run_load_test():
    print(f"🚀 Flooding the Go Ingestor with {NUM_REQUESTS} requests...")
    start_time = time.time()
    
    counts = {202: 0, 429: 0, 0: 0}
    
    async with httpx.AsyncClient() as client:
        # Send in batches to avoid local OS socket exhaustion
        for i in range(0, NUM_REQUESTS, BATCH_SIZE):
            tasks = [send_request(client, j) for j in range(i, i + BATCH_SIZE)]
            results = await asyncio.gather(*tasks)
            for res in results:
                counts[res] = counts.get(res, 0) + 1
            
            time.time() - start_time
            print(f"Progress: {i + BATCH_SIZE}/{NUM_REQUESTS} | 202: {counts[202]} | 429: {counts.get(429, 0)}")

    total_time = time.time() - start_time
    print("\n--- Load Test Results ---")
    print(f"Total Requests: {NUM_REQUESTS}")
    print(f"Total Time:     {total_time:.2f}s")
    print(f"Accepted (202): {counts[202]}")
    print(f"Rejected (429): {counts.get(429, 0)}")
    print(f"Failures (Err): {counts.get(0, 0)}")
    
    if counts.get(429, 0) > 0:
        print("\n✅ SUCCESS: Backpressure logic was triggered! The system protected itself.")
    else:
        print("\n⚠️  NOTICE: No 429s seen. Either the consumer was too fast or the buffer is larger than expected.")

if __name__ == "__main__":
    asyncio.run(run_load_test())
