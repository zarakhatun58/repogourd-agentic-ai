import asyncio

from playwright.async_api import async_playwright


async def main():
    print("Starting Playwright...")

    async with async_playwright() as p:
        print("Playwright connected")

        browser = await p.chromium.launch(
            headless=True
        )

        print("Chromium launched")

        page = await browser.new_page()

        await page.goto(
            "http://127.0.0.1:8100/item/1",
            wait_until="domcontentloaded",
            timeout=15000,
        )

        print("Page loaded:", await page.title())
        print("URL:", page.url)

        title = await page.locator(
            ".item-title"
        ).inner_text()

        print("Product title:", title)

        await browser.close()

        print("Browser closed")


if __name__ == "__main__":
    asyncio.run(main())