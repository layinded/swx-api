import asyncio
import httpx
import time
import sys

# Configuration
API_URL = "http://127.0.0.1:8000/api"
CONCURRENT_REQUESTS = 10

async def check_health(client, request_id):
    """Fetch health status and measure latency."""
    start = time.time()
    try:
        response = await client.get(f"{API_URL}/utils/health")
        duration = time.time() - start
        print(f"Request {request_id}: Status {response.status_code}, Latency {duration:.4f}s")
        return response.status_code, duration
    except Exception as e:
        print(f"Request {request_id}: Failed with {e}")
        return 500, 0

async def run_smoke_test():
    """Run concurrent health checks to verify non-blocking behavior."""
    print(f"Starting async DB smoke test with {CONCURRENT_REQUESTS} concurrent requests...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [check_health(client, i) for i in range(CONCURRENT_REQUESTS)]
        
        start_total = time.time()
        results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_total
        
        success_count = sum(1 for status, _ in results if status == 200)
        avg_latency = sum(duration for _, duration in results) / CONCURRENT_REQUESTS
        
        print("\n--- Summary ---")
        print(f"Successful Requests: {success_count}/{CONCURRENT_REQUESTS}")
        print(f"Total Time for {CONCURRENT_REQUESTS} requests: {total_duration:.4f}s")
        print(f"Average Latency: {avg_latency:.4f}s")
        
        if success_count < CONCURRENT_REQUESTS:
            print("❌ FAILURE: Not all requests succeeded.")
            sys.exit(1)
            
        # If total duration is significantly less than CONCURRENT_REQUESTS * avg_latency, 
        # it proves requests were handled concurrently.
        if total_duration < (avg_latency * CONCURRENT_REQUESTS * 0.8):
            print("✅ SUCCESS: Requests handled concurrently.")
        else:
            print("⚠️ WARNING: Concurrency benefit seems low. check event loop.")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
