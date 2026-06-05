import asyncio
import json
import re
from typing import Any

from crawlers.base import BaseCrawler

BASE_URL = "https://www.kbchachacha.com"
SEARCH_URL = f"{BASE_URL}/public/search/main.kbc"
PAGE_SIZE = 20


class KbchachachaCrawler(BaseCrawler):
    PLATFORM = "kbchachacha"
    DELAY_MIN = 4.0
    DELAY_MAX = 7.0

    async def fetch_list(self, page: int, category: dict[str, Any] | None = None) -> list[dict]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("[kbchachacha] playwright not installed")
            return []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=self.HEADERS["User-Agent"],
                locale="ko-KR",
            )
            results, api_url = await self._intercept_and_collect(ctx, page)
            await browser.close()
            return results

    async def _intercept_and_collect(self, ctx, page: int) -> tuple[list[dict], str | None]:
        """페이지를 로드하고 실제 API 요청을 인터셉트"""
        results: list[dict] = []
        api_url_found = None

        page_obj = await ctx.new_page()

        captured: list[dict] = []

        async def on_response(response):
            url = response.url
            if "carList" in url or ("car" in url and "list" in url.lower()):
                try:
                    body = await response.json()
                    if isinstance(body, dict) and ("list" in body or "data" in body or "cars" in body):
                        captured.append({"url": url, "data": body})
                except Exception:
                    pass

        page_obj.on("response", on_response)

        target_url = f"{SEARCH_URL}?page={page}"
        await page_obj.goto(target_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        # 인터셉트된 API 응답 처리
        if captured:
            for item in captured:
                results.extend(self._extract_from_api(item["data"]))
            return results, captured[0]["url"]

        # API 인터셉트 실패 → DOM에서 직접 파싱
        html = await page_obj.content()
        await page_obj.close()
        return self._parse_dom(html), None

    def _extract_from_api(self, body: dict) -> list[dict]:
        cars = body.get("list") or body.get("data") or body.get("cars") or []
        if not isinstance(cars, list):
            return []
        return [self._normalize_api_item(c) for c in cars if isinstance(c, dict)]

    def _normalize_api_item(self, c: dict) -> dict:
        return {
            "external_id": str(c.get("carId") or c.get("id") or ""),
            "brand": c.get("makerName") or c.get("brandName") or c.get("make"),
            "model": c.get("modelName") or c.get("model"),
            "year": self._to_int(c.get("modelYear") or c.get("year")),
            "price": self._to_int(c.get("carPrice") or c.get("price")),
            "mileage": self._to_int(c.get("kmMeter") or c.get("mileage")),
            "fuel": c.get("fuelName") or c.get("fuel"),
            "region": c.get("cityName") or c.get("region"),
            "images": self._extract_images(c),
            "url": self._car_url(c),
        }

    def _parse_dom(self, html: str) -> list[dict]:
        """API 인터셉트 실패 시 DOM 파싱 폴백"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        results = []

        # KB차차차 DOM 구조 시도
        for item in soup.select(".car-item, .mycar-item, [class*=car-list] li, [class*=carItem]"):
            car_id = item.get("data-id") or item.get("data-car-id")
            if not car_id:
                link = item.find("a", href=re.compile(r"/car/"))
                if link:
                    m = re.search(r"/car/(\d+)", link["href"])
                    car_id = m.group(1) if m else None
            if not car_id:
                continue

            text = item.get_text(" ", strip=True)
            price = self._parse_price(text)
            results.append({
                "external_id": str(car_id),
                "brand": None,
                "model": self._extract_title(item),
                "price": price,
                "mileage": self._parse_mileage(text),
                "year": self._parse_year(text),
                "region": None,
                "fuel": None,
                "images": [],
                "url": f"{BASE_URL}/public/car/detail.kbc?carId={car_id}",
            })

        return results

    def _to_int(self, v) -> int | None:
        try:
            return int(str(v).replace(",", "")) if v else None
        except (ValueError, TypeError):
            return None

    def _extract_images(self, c: dict) -> list[str]:
        img = c.get("carImg") or c.get("imageUrl") or c.get("img") or ""
        if img:
            return [img if img.startswith("http") else f"https:{img}"]
        return []

    def _car_url(self, c: dict) -> str:
        car_id = c.get("carId") or c.get("id") or ""
        return f"{BASE_URL}/public/car/detail.kbc?carId={car_id}"

    def _extract_title(self, el) -> str | None:
        for tag in ("h3", "h4", "strong"):
            node = el.find(tag)
            if node:
                t = node.get_text(strip=True)
                if len(t) > 2:
                    return t
        return None

    def _parse_price(self, text: str) -> int | None:
        m = re.search(r"([\d,]+)\s*만", text)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    def _parse_mileage(self, text: str) -> int | None:
        m = re.search(r"([\d.]+)\s*만\s*km", text, re.IGNORECASE)
        if m:
            try:
                return int(float(m.group(1)) * 10000)
            except ValueError:
                return None
        return None

    def _parse_year(self, text: str) -> int | None:
        m = re.search(r"\b(20\d{2})\b", text)
        return int(m.group(1)) if m else None

    async def fetch_detail(self, external_id: str) -> dict:
        return {}

    async def normalize(self, raw: dict, category: dict[str, Any] | None = None) -> dict:
        if not raw.get("external_id"):
            return {}
        return {
            "platform": self.PLATFORM,
            "external_id": raw["external_id"],
            "brand": raw.get("brand"),
            "model": raw.get("model"),
            "year": raw.get("year"),
            "price": raw.get("price"),
            "mileage": raw.get("mileage"),
            "fuel": raw.get("fuel"),
            "region": raw.get("region"),
            "color": None,
            "transmission": None,
            "seller_type": "dealer",
            "images": raw.get("images", []),
            "url": raw.get("url"),
            "raw_data": raw,
        }
