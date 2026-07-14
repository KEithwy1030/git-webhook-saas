# -*- coding: utf-8 -*-
"""
DevOps SaaS Web Server Stress Testing Tool (压测与资源负荷测试脚本)
Uses multi-threading to fire concurrent requests to target endpoints
and computes QPS (Queries Per Second) and latency metrics.
"""
import time
import requests
import threading
from collections import Counter

# Test Settings
TARGET_URL = "http://35.186.147.150:18340/"  # Your Singapore VPS live URL
CONCURRENT_THREADS = 15                      # Number of simultaneous threads
REQUESTS_PER_THREAD = 8                      # Number of requests each thread fires
TIMEOUT_SECONDS = 10                         # HTTP timeout

results = []

def fire_stress_requests(thread_id):
    thread_results = []
    for i in range(REQUESTS_PER_THREAD):
        start_time = time.time()
        try:
            res = requests.get(TARGET_URL, timeout=TIMEOUT_SECONDS)
            latency = time.time() - start_time
            thread_results.append({
                'status': res.status_code,
                'latency': latency,
                'success': True
            })
        except Exception as e:
            latency = time.time() - start_time
            thread_results.append({
                'status': 'TIMEOUT/ERROR',
                'latency': latency,
                'success': False
            })
    results.extend(thread_results)

if __name__ == '__main__':
    print(f"=== [⚡ Starting Web Server Stress Test] ===")
    print(f"Target URL: {TARGET_URL}")
    print(f"Concurrency: {CONCURRENT_THREADS} Threads")
    print(f"Total Target Requests: {CONCURRENT_THREADS * REQUESTS_PER_THREAD}")
    print("Executing concurrent requests. Please wait...")
    
    start_test_time = time.time()
    
    threads = []
    for t in range(CONCURRENT_THREADS):
        thread = threading.Thread(target=fire_stress_requests, args=(t,))
        threads.append(thread)
        thread.start()
        
    for thread in threads:
        thread.join()
        
    total_test_duration = time.time() - start_test_time
    
    # Analyze metrics
    total_requests = len(results)
    success_requests = sum(1 for r in results if r['success'])
    failed_requests = total_requests - success_requests
    
    latencies = [r['latency'] for r in results if r['success']]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    
    status_codes = Counter(r['status'] for r in results)
    qps = total_requests / total_test_duration
    
    print("\n" + "="*40)
    print("📊 STRESS TEST REPORT (压测结果报告)")
    print("="*40)
    print(f"Total Run Time     : {total_test_duration:.3f} seconds")
    print(f"Total Requests Sent: {total_requests}")
    print(f"Successful Requests: {success_requests} ({success_requests/total_requests*100:.1f}%)")
    print(f"Failed/Timeouts    : {failed_requests}")
    print(f"Throughput (QPS)   : {qps:.2f} requests/sec")
    print("-" * 40)
    print(f"Min Latency        : {min_latency:.3f} seconds")
    print(f"Avg Latency        : {avg_latency:.3f} seconds")
    print(f"Max Latency        : {max_latency:.3f} seconds")
    print("-" * 40)
    print("Response Status Breakdown:")
    for status, count in status_codes.items():
        print(f"  HTTP [{status}]: {count} occurrences")
    print("="*40)
