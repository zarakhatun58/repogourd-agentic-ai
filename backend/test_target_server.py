
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn


app = FastAPI(
    title="RepoGuard Scraper Test Target",
    version="1.0.0",
)


ITEM_COUNT = 50

# Local:
#   http://127.0.0.1:8100
#
# Render:
#   Set TARGET_BASE_URL=https://your-render-target.onrender.com
BASE_URL = os.getenv(
    "TARGET_BASE_URL",
    "http://127.0.0.1:8100",
)


def item_page(item_id: int) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>RepoGuard Test Item {item_id}</title>

    <meta
        name="description"
        content="Controlled RepoGuard scraping test item {item_id}"
    >

    <link
        rel="canonical"
        href="{BASE_URL}/item/{item_id}"
    >

    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
        }}

        .item {{
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 24px;
        }}

        .price {{
            font-size: 24px;
            font-weight: bold;
        }}

        .category {{
            display: inline-block;
            margin-top: 8px;
            padding: 6px 10px;
            border-radius: 6px;
            background: #eee;
        }}
    </style>
</head>

<body>
    <main class="item" data-testid="product-card">

        <h1 class="item-title">
            RepoGuard Test Product {item_id}
        </h1>

        <p class="item-description">
            Controlled test product used to validate
            RepoGuard Agentic AI web scraping.
        </p>

        <div class="price">
            ${item_id * 10 + 99}.99
        </div>

        <div class="category">
            Category {((item_id - 1) % 5) + 1}
        </div>

        <p class="item-id">
            Item ID: {item_id}
        </p>

        <p class="timestamp">
            Generated:
            {datetime.now(timezone.utc).isoformat()}
        </p>

    </main>
</body>
</html>
"""


@app.get(
    "/",
    response_class=HTMLResponse,
)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>RepoGuard Test Target</title>
</head>

<body>
    <h1>RepoGuard Scraper Test Target</h1>

    <p>
        Controlled website for RepoGuard scraper integration testing.
    </p>

    <p>
        Available items: /item/1 through /item/50
    </p>
</body>
</html>
"""


@app.get(
    "/item/{item_id}",
    response_class=HTMLResponse,
)
async def item(item_id: int):
    if item_id < 1 or item_id > ITEM_COUNT:
        return HTMLResponse(
            content="<h1>Item not found</h1>",
            status_code=404,
        )

    # Small artificial delay makes concurrency measurable.
    await asyncio.sleep(0.05)

    return HTMLResponse(
        content=item_page(item_id),
        status_code=200,
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "repoguard-test-target",
        "items": ITEM_COUNT,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8100"))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
    )

