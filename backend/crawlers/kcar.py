"""케이카 크롤러 — api.kcar.com JSON API 직접 호출 (Playwright 불필요)"""
from typing import Any

from crawlers.base import BaseCrawler

API_BASE = "https://api.kcar.com"
LIST_URL = f"{API_BASE}/bc/stockCar/list"
IMG_BASE = "https://img.kcar.com"
PAGE_SIZE = 100


class KcarCrawler(BaseCrawler):
    PLATFORM = "kcar"
    DELAY_MIN = 2.0
    DELAY_MAX = 4.0

    async def fetch_list(self, page: int, category: dict[str, Any] | None = None) -> list[dict]:
        params = self._build_params(page, category)
        data = await self.get(LIST_URL, params=params,
                              headers={**self.HEADERS, "Referer": "https://www.kcar.com/"})
        if not data:
            return []
        return self._extract_cars(data)

    def _build_params(self, page: int, category: dict[str, Any] | None) -> dict:
        params: dict = {
            "currentPage": page,
            "pageSize": PAGE_SIZE,
            "creatYn": "Y",
            "sIndex": (page - 1) * PAGE_SIZE + 1,
            "eIndex": page * PAGE_SIZE,
        }
        if category:
            if category.get("make_code"):
                params["mnuftrNm"] = category["make_code"]
            if category.get("model_group_code"):
                params["modelGrpNm"] = category["model_group_code"]
        return params

    def _extract_cars(self, data: dict) -> list[dict]:
        inner = data.get("data") or {}
        # allStockCarList → 전체 목록, list → 페이지 슬라이스
        cars = inner.get("allStockCarList") or inner.get("list") or []
        return [c for c in cars if isinstance(c, dict)]

    async def fetch_detail(self, external_id: str) -> dict:
        url = f"{API_BASE}/bc/stockCar/detail?carCd={external_id}"
        return await self.get(url, headers={**self.HEADERS, "Referer": "https://www.kcar.com/"}) or {}

    async def normalize(self, raw: dict, category: dict[str, Any] | None = None) -> dict:
        car_cd = raw.get("carCd", "")
        if not car_cd:
            return {}

        return {
            "platform": self.PLATFORM,
            "external_id": car_cd,
            "brand": raw.get("mnuftrNm"),
            "model_group": raw.get("modelGrpCd"),
            "model": raw.get("modelNm"),
            "year": self._parse_year(raw.get("prdcnYr") or raw.get("mfgDt")),
            "trim": raw.get("grdNm") or raw.get("grdDtlNm"),
            "price": self._to_int(raw.get("prc") or raw.get("dcPrc")),
            "mileage": self._to_int(raw.get("milg")),
            "fuel": raw.get("fuelNm"),
            "transmission": raw.get("trnsmsnNm"),
            "color": raw.get("extrColorNm") or raw.get("colorNm"),
            "region": raw.get("cntrNm"),
            "seller_type": "dealer",
            "images": self._extract_images(raw),
            "url": f"https://www.kcar.com/bc/car/{car_cd}",
            "raw_data": raw,
        }

    def _parse_year(self, v) -> int | None:
        if not v:
            return None
        try:
            s = str(v)[:4]
            yr = int(s)
            return yr if 1990 <= yr <= 2030 else None
        except (ValueError, TypeError):
            return None

    def _to_int(self, v) -> int | None:
        try:
            return int(str(v).replace(",", "")) if v else None
        except (ValueError, TypeError):
            return None

    def _extract_images(self, raw: dict) -> list[str]:
        for key in ("lsizeImgPath", "msizeImgPath"):
            img = raw.get(key, "")
            if img:
                return [img if img.startswith("http") else f"{IMG_BASE}{img}"]
        return []
