import asyncio
import re
from typing import Any

from crawlers.base import BaseCrawler

BASE_URL = "https://www.kcar.com"
LIST_URL = f"{BASE_URL}/bc/stockCar/list"
PAGE_SIZE = 20


class KcarCrawler(BaseCrawler):
    PLATFORM = "kcar"
    DELAY_MIN = 4.0
    DELAY_MAX = 7.0

    async def fetch_list(self, page: int, category: dict[str, Any] | None = None) -> list[dict]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("[kcar] playwright not installed")
            return []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=self.HEADERS["User-Agent"],
                locale="ko-KR",
            )
            results = await self._collect(ctx, page)
            await browser.close()
            return results

    async def _collect(self, ctx, page: int) -> list[dict]:
        page_obj = await ctx.new_page()
        captured: list[dict] = []

        async def on_response(response):
            url = response.url
            # K Car API 패턴 탐지
            if any(kw in url for kw in ["/car/list", "/stock/list", "/search/list", "stockCar"]):
                ct = response.headers.get("content-type", "")
                if "json" in ct:
                    try:
                        body = await response.json()
                        captured.append({"url": url, "data": body})
                    except Exception:
                        pass

        page_obj.on("response", on_response)

        target = f"{LIST_URL}?page={page}"
        await page_obj.goto(target, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        if captured:
            results = []
            for item in captured:
                results.extend(self._extract_from_api(item["data"]))
            await page_obj.close()
            return results

        # DOM 파싱 폴백
        html = await page_obj.content()
        await page_obj.close()
        return self._parse_dom(html)

    def _extract_from_api(self, body: dict) -> list[dict]:
        # K Car API 응답 구조 탐지
        for key in ("list", "data", "contents", "stockList", "cars"):
            cars = body.get(key)
            if isinstance(cars, list):
                return [self._normalize_api_item(c) for c in cars if isinstance(c, dict)]
        return []

    def _normalize_api_item(self, c: dict) -> dict:
        return {
            "external_id": str(c.get("stockNo") or c.get("carId") or c.get("id") or ""),
            "brand": c.get("makerName") or c.get("brandName") or c.get("make"),
            "model": c.get("modelName") or c.get("gradeName") or c.get("model"),
            "year": self._to_int(c.get("modelYear") or c.get("year")),
            "trim": c.get("gradeName") or c.get("trim"),
            "price": self._to_int(c.get("price") or c.get("salePrice")),
            "mileage": self._to_int(c.get("mileage") or c.get("kmMeter")),
            "fuel": c.get("fuelName") or c.get("fuel"),
            "color": c.get("colorName") or c.get("color"),
            "region": c.get("regionName") or c.get("region"),
            "images": self._extract_images(c),
            "url": self._car_url(c),
        }

    def _parse_dom(self, html: str) -> list[dict]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        results = []

        for item in soup.select("[class*=car-item], [class*=stockCar], [class*=CarItem]"):
            car_no = item.get("data-stock-no") or item.get("data-car-id") or item.get("data-id")
            if not car_no:
                link = item.find("a", href=re.compile(r"/(bc/)?car/\d+"))
                if link:
                    m = re.search(r"/(\d+)", link["href"])
                    car_no = m.group(1) if m else None
            if not car_no:
                continue

            text = item.get_text(" ", strip=True)
            results.append({
                "external_id": str(car_no),
                "brand": None,
                "model": self._extract_title(item),
                "price": self._parse_price(text),
                "mileage": self._parse_mileage(text),
                "year": self._parse_year(text),
                "region": None,
                "fuel": None,
                "images": [],
                "url": f"{BASE_URL}/bc/car/{car_no}",
            })

        return results

    def _to_int(self, v) -> int | None:
        try:
            return int(str(v).replace(",", "")) if v else None
        except (ValueError, TypeError):
            return None

    def _extract_images(self, c: dict) -> list[str]:
        for key in ("imgPath", "imageUrl", "carImg", "repImg"):
            img = c.get(key, "")
            if img:
                return [img if img.startswith("http") else f"https:{img}"]
        return []

    def _car_url(self, c: dict) -> str:
        stock_no = c.get("stockNo") or c.get("carId") or ""
        return f"{BASE_URL}/bc/car/{stock_no}"

    def _extract_title(self, el) -> str | None:
        for tag in ("h3", "h4", "strong", "p"):
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
            "trim": raw.get("trim"),
            "price": raw.get("price"),
            "mileage": raw.get("mileage"),
            "fuel": raw.get("fuel"),
            "color": raw.get("color"),
            "region": raw.get("region"),
            "transmission": None,
            "seller_type": "dealer",
            "images": raw.get("images", []),
            "url": raw.get("url"),
            "raw_data": raw,
        }
