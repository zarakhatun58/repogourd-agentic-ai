"""Local benchmark target for the RepoGuard browser-automation demo.

Run:
    uvicorn scripts.demo_target:app --host 127.0.0.1 --port 8100

This target is intentionally local so the Loom can demonstrate concurrency
without sending a high-volume batch at a third-party site.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="RepoGuard Authorized Demo Target")


@app.get("/item/{item_id}", response_class=HTMLResponse)
def item(item_id: int):
    return f"""
    <!doctype html>
    <html>
      <head><title>Demo Item {item_id}</title></head>
      <body>
        <main>
          <h1 class="title">Demo Product {item_id}</h1>
          <p class="category">Engineering Demo</p>
          <p class="price">${(item_id % 97) + 10}.00</p>
          <p class="status">available</p>
        </main>
      </body>
    </html>
    """


@app.get("/health")
def health():
    return {"status": "ok"}
