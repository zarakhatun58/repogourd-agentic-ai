from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.services.scraper.models import BrowserProfile, ProxyConfig
from app.services.scraper.proxy import ProxyEntry, ProxyPool


@dataclass
class BrowserSession:
    """
    Represents one isolated Playwright browser context and page.
    """

    context: BrowserContext
    page: Page
    proxy_id: str | None = None


class BrowserManager:
    """
    Manages Playwright browsers used by scraping workers.

    Supports:
    - One fixed proxy
    - Optional ProxyPool-based proxy selection
    - Isolated browser contexts
    - Browser profiles
    - Session/storage state
    - Per-proxy browser instances

    A ProxyPool is optional. When no proxy is configured,
    the browser behaves exactly like the direct-connection mode.
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        browser_profile: BrowserProfile | None = None,
        proxy: ProxyConfig | None = None,
        proxy_pool: ProxyPool | None = None,
    ):
        self.headless = headless
        self.browser_profile = browser_profile or BrowserProfile()

        self.proxy = proxy
        self.proxy_pool = proxy_pool

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

        self._proxy_browsers: dict[str, Browser] = {}

    async def start(self) -> None:
        """
        Start Playwright.

        Chromium is launched lazily:
        - immediately for direct/fixed-proxy mode
        - per proxy for ProxyPool mode
        """

        if self._playwright is not None:
            return

        self._playwright = await async_playwright().start()

        if self.proxy_pool is None:
            self._browser = await self._launch_browser(
                proxy=self.proxy,
            )

    async def _launch_browser(
        self,
        *,
        proxy: ProxyConfig | None = None,
    ) -> Browser:
        if self._playwright is None:
            raise RuntimeError(
                "Playwright has not been started. "
                "Call await manager.start() first."
            )

        launch_options: dict[str, Any] = {
            "headless": self.headless,
        }

        if proxy:
            launch_options["proxy"] = proxy.as_playwright_config()

        return await self._playwright.chromium.launch(
            **launch_options
        )

    async def _get_browser_for_proxy(
        self,
        proxy_entry: ProxyEntry,
    ) -> Browser:
        """
        Get or create a Chromium instance dedicated to one proxy.

        Playwright proxy configuration is a browser-launch option,
        so proxy rotation is implemented by maintaining isolated
        browser instances per proxy.
        """

        existing = self._proxy_browsers.get(
            proxy_entry.proxy_id
        )

        if existing is not None:
            return existing

        browser = await self._launch_browser(
            proxy=proxy_entry.proxy,
        )

        self._proxy_browsers[
            proxy_entry.proxy_id
        ] = browser

        return browser

    async def stop(self) -> None:
        """
        Close all browsers and the Playwright runtime.
        """

        for browser in list(
            self._proxy_browsers.values()
        ):
            try:
                await browser.close()
            except Exception:
                pass

        self._proxy_browsers.clear()

        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass

            self._browser = None

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def create_context(
        self,
        *,
        profile: BrowserProfile | None = None,
        storage_state: dict | str | None = None,
        proxy_entry: ProxyEntry | None = None,
    ) -> BrowserContext:
        """
        Create an isolated browser context.

        If proxy_entry is supplied, the context is created inside
        that proxy's dedicated browser instance.

        Otherwise:
        - ProxyPool mode acquires the next proxy automatically.
        - Fixed proxy mode uses the configured browser.
        - Direct mode uses the direct browser.
        """

        if self._playwright is None:
            raise RuntimeError(
                "BrowserManager has not been started. "
                "Call await manager.start() first."
            )

        active_profile = (
            profile or self.browser_profile
        )

        active_proxy_entry = proxy_entry

        if (
            active_proxy_entry is None
            and self.proxy_pool is not None
        ):
            active_proxy_entry = (
                await self.proxy_pool.acquire()
            )

            if active_proxy_entry is None:
                raise RuntimeError(
                    "No healthy proxy is currently available."
                )

        if active_proxy_entry is not None:
            browser = await self._get_browser_for_proxy(
                active_proxy_entry
            )
        else:
            if self._browser is None:
                self._browser = await self._launch_browser(
                    proxy=self.proxy,
                )

            browser = self._browser

        options: dict[str, Any] = {
            "viewport": {
                "width": active_profile.viewport_width,
                "height": active_profile.viewport_height,
            },
            "locale": active_profile.locale,
            "timezone_id": active_profile.timezone_id,
            "is_mobile": active_profile.is_mobile,
            "has_touch": active_profile.has_touch,
            "device_scale_factor": (
                active_profile.device_scale_factor
            ),
            "color_scheme": active_profile.color_scheme,
        }

        if active_profile.user_agent:
            options["user_agent"] = (
                active_profile.user_agent
            )

        if storage_state is not None:
            options["storage_state"] = storage_state

        context = await browser.new_context(
            **options
        )

        return context

    async def create_session(
        self,
        *,
        profile: BrowserProfile | None = None,
        storage_state: dict | str | None = None,
        proxy_entry: ProxyEntry | None = None,
    ) -> BrowserSession:
        """
        Create an isolated browser context and page.
        """

        active_proxy_entry = proxy_entry

        if (
            active_proxy_entry is None
            and self.proxy_pool is not None
        ):
            active_proxy_entry = (
                await self.proxy_pool.acquire()
            )

            if active_proxy_entry is None:
                raise RuntimeError(
                    "No healthy proxy is currently available."
                )

        context = await self.create_context(
            profile=profile,
            storage_state=storage_state,
            proxy_entry=active_proxy_entry,
        )

        page = await context.new_page()

        return BrowserSession(
            context=context,
            page=page,
            proxy_id=(
                active_proxy_entry.proxy_id
                if active_proxy_entry
                else None
            ),
        )

    async def close_session(
        self,
        session: BrowserSession,
    ) -> None:
        """
        Close a browser session and all pages belonging to it.
        """

        await session.context.close()

    @property
    def browser(self) -> Browser | None:
        return self._browser

    @property
    def is_running(self) -> bool:
        return (
            self._playwright is not None
        )

    @property
    def proxy_pool_enabled(self) -> bool:
        return self.proxy_pool is not None

    @property
    def proxy_browser_count(self) -> int:
        return len(self._proxy_browsers)

    async def __aenter__(self) -> "BrowserManager":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        await self.stop()