"""KB차차차 크롤러 — Playwright 내부 fetch로 세션 자동 처리"""
import asyncio
import json
import re
from typing import Any

from crawlers.base import BaseCrawler

BASE_URL = "https://www.kbchachacha.com"
LIST_API = f"{BASE_URL}/public/car/common/recent/car/list.json"
MAKER_API = f"{BASE_URL}/public/search/carMaker.json"
IMG_BASE = "https://img.kbchachacha.com"
PAGE_SIZE = 30


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
            results = await self._fetch_with_session(ctx, page, category)
            await browser.close()
            return results

    async def _fetch_with_session(self, ctx, page: int, category: dict | None) -> list[dict]:
        """브라우저 세션 생성 후 내부 fetch로 차량 목록 요청"""
        pw_page = await ctx.new_page()

        # 세션 쿠키 생성을 위해 메인 페이지 방문
        await pw_page.goto(f"{BASE_URL}/public/car/list.kbc",
                           wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(1)

        body_params = self._build_post_body(page, category)

        # 브라우저 내부에서 fetch → 세션/쿠키 자동 포함
        result = await pw_page.evaluate(f"""
            async () => {{
                const resp = await fetch('{LIST_API}', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json, */*',
                    }},
                    body: '{body_params}',
                    credentials: 'include',
                }});
                return await resp.json();
            }}
        """)

        await pw_page.close()

        if not result or not isinstance(result, dict):
            return []

        items = result.get("list") or []
        img_host = result.get("IMAGE_HOST") or IMG_BASE
        print(f"[kbchachacha] page={page} totalCount={result.get('totalCount', 0)} got={len(items)}")
        return [{"_img_host": img_host, **item} for item in items if isinstance(item, dict)]

    def _build_post_body(self, page: int, category: dict | None) -> str:
        params = [
            f"gotoPage={page}",
            f"pageSize={PAGE_SIZE}",
            "carSeqVal=",
            "order=R",
        ]
        if category:
            if category.get("make_code"):
                params.append(f"makerCode={category['make_code']}")
            if category.get("model_group_code"):
                params.append(f"classCode={category['model_group_code']}")
        return "&".join(params)

    async def fetch_detail(self, external_id: str) -> dict:
        return {}

    async def normalize(self, raw: dict, category: dict[str, Any] | None = None) -> dict:
        car_no = str(raw.get("carNo") or raw.get("carId") or raw.get("id") or "")
        if not car_no:
            return {}

        img_host = raw.get("_img_host") or IMG_BASE
        img_path = raw.get("carImgPath") or raw.get("imgPath") or ""
        image_url = f"{img_host}{img_path}" if img_path else None

        year_raw = raw.get("modelYear") or raw.get("year") or ""
        year = self._parse_year(year_raw)

        return {
            "platform": self.PLATFORM,
            "external_id": car_no,
            "brand": raw.get("makerName") or raw.get("brandName"),
            "model_group": raw.get("className") or raw.get("modelGroup"),
            "model": raw.get("carName") or raw.get("modelName"),
            "year": year,
            "trim": raw.get("gradeName") or raw.get("trim"),
            "price": self._to_int(raw.get("sellAmt") or raw.get("price")),
            "mileage": self._to_int(raw.get("drveDist") or raw.get("mileage")),
            "fuel": raw.get("fuelName") or raw.get("fuel"),
            "transmission": raw.get("missionName") or raw.get("transmission"),
            "color": raw.get("colorName") or raw.get("color"),
            "region": raw.get("locNm") or raw.get("region"),
            "seller_type": "dealer",
            "images": [image_url] if image_url else [],
            "url": f"{BASE_URL}/public/car/detail.kbc?carNo={car_no}",
            "raw_data": {k: v for k, v in raw.items() if k != "_img_host"},
        }

    def _parse_year(self, v) -> int | None:
        s = str(v)
        m = re.search(r"(20\d{2}|19\d{2})", s)
        if m:
            return int(m.group(1))
        try:
            yr = int(s[:4])
            return yr if 1990 <= yr <= 2030 else None
        except (ValueError, TypeError):
            return None

    def _to_int(self, v) -> int | None:
        try:
            return int(str(v).replace(",", "").replace("만원", "").strip()) if v else None
        except (ValueError, TypeError):
            return None
