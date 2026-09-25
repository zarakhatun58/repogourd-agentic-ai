from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page


@dataclass
class ExtractionResult:
    """
    Result returned after processing a page.
    """

    data: dict[str, Any]
    blocked: bool = False
    challenge_detected: bool = False
    challenge_type: str | None = None


class PageExtractor:
    """
    Extracts structured information from rendered pages.

    The extractor supports:
    - CSS selectors
    - text extraction
    - HTML extraction
    - attributes
    - page metadata
    - basic anti-bot/challenge detection
    """

    def __init__(
        self,
        selector_map: dict[str, str] | None = None,
    ):
        self.selector_map = selector_map or {}

    async def extract(
        self,
        page: Page,
    ) -> ExtractionResult:
        """
        Extract configured fields from the current page.
        """

        blocked, challenge_detected, challenge_type = (
            await self.detect_challenge(page)
        )

        if blocked or challenge_detected:
            return ExtractionResult(
                data={},
                blocked=blocked,
                challenge_detected=challenge_detected,
                challenge_type=challenge_type,
            )

        data: dict[str, Any] = {}

        for key, selector in self.selector_map.items():
            data[key] = await self._extract_selector(
                page,
                selector,
            )

        metadata = await self.extract_metadata(page)

        if metadata:
            data["_metadata"] = metadata

        return ExtractionResult(
            data=data,
            blocked=False,
            challenge_detected=False,
        )

    async def _extract_selector(
        self,
        page: Page,
        selector: str,
    ) -> Any:
        """
        Extract the first matching element.

        Supported selector formats:

        text:
            "h1"

        attribute:
            "@href:a"

        html:
            "html:.description"

        text:
            "text:.description"
        """

        selector = selector.strip()

        if not selector:
            return None

        try:
            # Explicit attribute syntax:
            # @href:a
            if selector.startswith("@"):
                attribute_expression = selector[1:]

                attribute, css_selector = self._split_attribute_selector(
                    attribute_expression
                )

                locator = page.locator(css_selector).first

                if await locator.count() == 0:
                    return None

                return await locator.get_attribute(attribute)

            # Explicit HTML syntax:
            # html:.description
            if selector.startswith("html:"):
                css_selector = selector[5:].strip()

                locator = page.locator(css_selector).first

                if await locator.count() == 0:
                    return None

                return await locator.inner_html()

            # Explicit text syntax:
            # text:.description
            if selector.startswith("text:"):
                css_selector = selector[5:].strip()

                locator = page.locator(css_selector).first

                if await locator.count() == 0:
                    return None

                return (await locator.inner_text()).strip()

            # Default behavior: text extraction
            locator = page.locator(selector).first

            if await locator.count() == 0:
                return None

            return (await locator.inner_text()).strip()

        except Exception:
            return None

    @staticmethod
    def _split_attribute_selector(
        expression: str,
    ) -> tuple[str, str]:
        """
        Convert:

            href:a

        into:

            ("href", "a")
        """

        if ":" not in expression:
            raise ValueError(
                "Attribute selector must use format @attribute:selector"
            )

        attribute, selector = expression.split(
            ":",
            1,
        )

        attribute = attribute.strip()
        selector = selector.strip()

        if not attribute or not selector:
            raise ValueError(
                "Invalid attribute selector"
            )

        return attribute, selector

    async def extract_metadata(
        self,
        page: Page,
    ) -> dict[str, Any]:
        """
        Extract common page metadata.
        """

        metadata: dict[str, Any] = {}

        try:
            metadata["title"] = await page.title()
        except Exception:
            metadata["title"] = None

        try:
            description = page.locator(
                'meta[name="description"]'
            ).first

            if await description.count() > 0:
                metadata["description"] = await description.get_attribute(
                    "content"
                )
        except Exception:
            metadata["description"] = None

        try:
            canonical = page.locator(
                'link[rel="canonical"]'
            ).first

            if await canonical.count() > 0:
                metadata["canonical"] = await canonical.get_attribute(
                    "href"
                )
        except Exception:
            metadata["canonical"] = None

        metadata["url"] = page.url

        return metadata

    async def detect_challenge(
        self,
        page: Page,
    ) -> tuple[bool, bool, str | None]:
        """
        Detect common access-control/challenge indicators.

        This function only detects and records challenge pages.
        It does not attempt to bypass them.
        """

        try:
            title = (
                await page.title()
            ).lower()

        except Exception:
            title = ""

        try:
            body_text = (
                await page.locator("body").inner_text()
            ).lower()

        except Exception:
            body_text = ""

        combined = f"{title}\n{body_text}"

        # Cloudflare indicators
        cloudflare_markers = [
            "cloudflare",
            "checking your browser",
            "just a moment",
            "verify you are human",
        ]

        if any(
            marker in combined
            for marker in cloudflare_markers
        ):
            return (
                False,
                True,
                "cloudflare",
            )

        # CAPTCHA indicators
        captcha_markers = [
            "captcha",
            "recaptcha",
            "hcaptcha",
            "verify that you are human",
        ]

        if any(
            marker in combined
            for marker in captcha_markers
        ):
            return (
                False,
                True,
                "captcha",
            )

        # Generic access-denied indicators
        blocked_markers = [
            "access denied",
            "request blocked",
            "forbidden",
        ]

        if any(
            marker in combined
            for marker in blocked_markers
        ):
            return (
                True,
                False,
                "access_denied",
            )

        return (
            False,
            False,
            None,
        )


async def extract_page(
    page: Page,
    selector_map: dict[str, str],
) -> ExtractionResult:
    """
    Convenience function for one-off extraction.
    """

    extractor = PageExtractor(
        selector_map=selector_map,
    )

    return await extractor.extract(page)