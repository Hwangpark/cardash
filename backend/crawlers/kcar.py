"""케이카 크롤러 — Playwright로 검색 결과 API 가로채기"""
import asyncio
import random
import re
from typing import Any

from crawlers.base import BaseCrawler

SEARCH_URL = "https://www.kcar.com/bc/search"
SEARCH_API = "bc/search/list/drct"
IMG_BASE = "https://img.kcar.com"

REGION_MAP = {
    "SEOUL": "서울", "GYEONGGI": "경기", "INCHEON": "인천",
    "BUSAN": "부산", "DAEGU": "대구", "GWANGJU": "광주",
    "DAEJEON": "대전", "ULSAN": "울산", "SEJONG": "세종",
    "GANGWON": "강원", "CHUNGBUK": "충북", "CHUNGNAM": "충남",
    "JEONBUK": "전북", "JEONNAM": "전남", "GYEONGBUK": "경북",
    "GYEONGNAM": "경남", "JEJU": "제주", "MEGA": "전국",
}


class KcarCrawler(BaseCrawler):
    PLATFORM = "kcar"
    DELAY_MIN = 3.0
    DELAY_MAX = 5.0

    async def run(self, max_pages: int = 50, category: dict[str, Any] | None = None):
        """더보기 버튼 클릭으로 페이지네이션 — 한 세션에서 max_pages페이지 수집.
        Windows SelectorEventLoop에서 subprocess 불가 → 별도 스레드+루프로 우회.
        """
        import asyncio as _asyncio

        def collect_in_thread() -> list[dict]:
            import sys
            if sys.platform == "win32":
                loop = _asyncio.ProactorEventLoop()
            else:
                loop = _asyncio.new_event_loop()
            _asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._collect_via_playwright(max_pages, category))
            finally:
                loop.close()

        loop = _asyncio.get_running_loop()
        all_raws: list[dict] = await loop.run_in_executor(None, collect_in_thread)

        if not all_raws:
            return

        from database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            saved = 0
            for raw in all_raws:
                try:
                    data = await self.normalize(raw, category)
                    if data:
                        await self._persist_item(db, data)
                        saved += 1
                except Exception as e:
                    print(f"[kcar] normalize error: {e}")
            await db.commit()
        print(f"[kcar] done: {saved} / {len(all_raws)} saved")

    async def _collect_via_playwright(self, max_pages: int, category: dict[str, Any] | None = None) -> list[dict]:
        from playwright.async_api import async_playwright

        all_raws: list[dict] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = await browser.new_context(
                user_agent=self.HEADERS["User-Agent"],
                locale="ko-KR",
                viewport={"width": 1280, "height": 900},
            )
            pw_page = await ctx.new_page()

            async def on_response(resp):
                if SEARCH_API in resp.url:
                    try:
                        data = (await resp.json()).get("data", {})
                        all_raws.extend(data.get("rows", []))
                    except Exception:
                        pass

            pw_page.on("response", on_response)

            await pw_page.goto(SEARCH_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            await self._apply_category_filter(pw_page, category, all_raws)

            # 첫 번째 페이지네이션 그룹 (직영 목록)
            paging = pw_page.locator(".pagination").first

            for page_idx in range(1, max_pages):
                next_item = await self._find_next_page_item(paging)
                if not next_item:
                    break
                await next_item.scroll_into_view_if_needed()
                await next_item.click()
                await asyncio.sleep(random.uniform(self.DELAY_MIN, self.DELAY_MAX))

            await browser.close()

        print(f"[kcar] collected {len(all_raws)} cars over ~{max_pages} pages")
        return all_raws

    async def _apply_category_filter(self, pw_page, category: dict[str, Any] | None, all_raws: list[dict]):
        """좌측 제조사/모델 체크박스를 클릭해 검색 결과를 필터링한다.
        클릭 시 결과가 갱신되며 on_response로 누적되므로, 직전 응답(필터 적용 전)은 비운다.
        """
        if not category:
            return
        brand = category.get("make_code")
        model_group = category.get("model_group_code")
        if not brand:
            return

        all_raws.clear()
        brand_li = pw_page.locator("li").filter(
            has=pw_page.locator("label.el-checkbox span.el-checkbox__label", has_text=brand)
        ).first
        await brand_li.locator("label.el-checkbox").first.click(force=True)
        await asyncio.sleep(2)

        if model_group:
            all_raws.clear()
            model_label = brand_li.locator("ul.depth3 label.el-checkbox", has_text=model_group).first
            await model_label.click(force=True)
            await asyncio.sleep(2)

    async def _find_next_page_item(self, paging):
        """현재 활성 페이지 다음 pagingNum 반환. 그룹 끝이면 next-group 버튼."""
        items = paging.locator(".pagingNum")
        count = await items.count()
        for i in range(count):
            item = items.nth(i)
            span = item.locator("span")
            cls = await span.get_attribute("class") or ""
            if "textRed" in cls and i + 1 < count:
                return items.nth(i + 1)
        # 현재 그룹에 다음 페이지가 없으면 ul의 마지막 li (다음 그룹 이동)
        last_li = paging.locator(".paging ul li").last
        txt = (await last_li.inner_text()).strip()
        return last_li if txt else None

    async def fetch_list(self, page: int, category: dict[str, Any] | None = None) -> list[dict]:
        # run()이 override되어 있어 직접 호출되지 않음
        return []

    async def fetch_detail(self, external_id: str) -> dict:
        return {}

    async def normalize(self, raw: dict, category: dict[str, Any] | None = None) -> dict:
        car_cd = str(raw.get("carCd") or "")
        if not car_cd:
            return {}

        img_path = raw.get("lsizeImgPath") or raw.get("msizeImgPath") or ""
        image_url = img_path if img_path.startswith("http") else (IMG_BASE + img_path if img_path else None)

        return {
            "platform": self.PLATFORM,
            "external_id": car_cd,
            "brand": raw.get("mnuftrNm"),
            "model_group": raw.get("modelGrpNm") or raw.get("modelNm"),
            "model": raw.get("modelNm"),
            "year": self._parse_year(raw.get("prdcnYr") or raw.get("mfgDt")),
            "trim": raw.get("grdNm"),
            "price": self._to_int(raw.get("prc")),
            "mileage": self._to_int(raw.get("milg")),
            "fuel": raw.get("fuelNm"),
            "transmission": raw.get("trnsmsnNm"),
            "color": raw.get("extrColorNm"),
            "region": self._parse_region(raw),
            "seller_type": "dealer",
            "images": [image_url] if image_url else [],
            "url": f"https://www.kcar.com/bc/car/{car_cd}",
            "raw_data": raw,
        }

    def _parse_region(self, raw: dict) -> str | None:
        rcd = raw.get("cntrRgnCd", "")
        if rcd in REGION_MAP:
            return REGION_MAP[rcd]
        # cntrRgnNm에서 첫 단어 추출
        nm = raw.get("cntrRgnNm", "")
        if nm:
            return nm.split()[0] if nm else None
        return None

    def _parse_year(self, v) -> int | None:
        if not v:
            return None
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
            return int(str(v).replace(",", "").strip()) if v else None
        except (ValueError, TypeError):
            return None
