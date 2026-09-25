"""Create a browser-automation benchmark through the API.

Start:
  1) PostgreSQL
  2) API: uvicorn app.main:app --reload
  3) Target: uvicorn scripts.demo_target:app --host 127.0.0.1 --port 8100

Then:
  python scripts/run_benchmark.py
"""
import json
import urllib.request

API = "http://127.0.0.1:8000"
urls = [f"http://127.0.0.1:8100/item/{i}" for i in range(1, 101)]

payload = {
    "name": "Searchlook Loom — Authorized Playwright Benchmark",
    "urls": urls,
    "selector_map": {
        "title": ".title",
        "category": ".category",
        "price": ".price",
        "status": ".status",
    },
    "max_concurrency": 5,
    "delay_ms": 100,
    "timeout_ms": 15000,
}

request = urllib.request.Request(
    f"{API}/scraping/jobs",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request) as response:
    print(response.read().decode())
