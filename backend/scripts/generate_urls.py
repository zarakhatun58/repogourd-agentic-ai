from pathlib import Path

count = 100
path = Path("scripts/demo_urls.txt")
path.write_text("\n".join(f"http://127.0.0.1:8100/item/{i}" for i in range(1, count + 1)), encoding="utf-8")
print(f"Wrote {count} authorized local demo URLs to {path}")
