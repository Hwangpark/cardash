from typing import Any

from categories import build_encar_query, extract_encar_categories
from crawlers.base import BaseCrawler

API_BASE = "https://api.encar.com"
SEARCH_URL = f"{API_BASE}/search/car/list/mobile"
INAV_PARAM = "|Metadata|Sort"
PAGE_SIZE = 40
DOMESTIC_MAKES = {
    "현대", "제네시스", "기아", "쉐보레(GM대우)",
    "르노코리아(삼성)", "KG모빌리티(쌍용)", "기타 제조사",
}


class EncarCrawler(BaseCrawler):
    PLATFORM = "encar"

    async def fetch_list(self, page: int, category: dict[str, Any] | None = None) -> list[dict]:
        params = self._build_search_params(page, category)
        data = await self.get(SEARCH_URL, params=params)
        return (data or {}).get("SearchResults", [])

    async def fetch_detail(self, external_id: str) -> dict:
        url = f"{API_BASE}/v1/readside/vehicle/{external_id}"
        return await self.get(url) or {}

    async def fetch_make_categories(self) -> list[dict]:
        data = await self._fetch_category_data()
        return extract_encar_categories(data, "make")

    async def fetch_model_group_categories(self, make: dict) -> list[dict]:
        data = await self._fetch_category_data({"make_code": make["code"]})
        return extract_encar_categories(data, "model_group")

    async def fetch_model_categories(self, make: dict, model_group: dict) -> list[dict]:
        category = {"make_code": make["code"], "model_group_code": model_group["code"]}
        data = await self._fetch_category_data(category)
        return extract_encar_categories(data, "model")

    async def _fetch_category_data(self, category: dict[str, Any] | None = None) -> dict:
        params = {
            "count": "true",
            "q": build_encar_query(category),
            "sr": f"|ModifiedDate|0|1",
            "inav": INAV_PARAM,
            "cursor": "",
        }
        return await self.get(SEARCH_URL, params=params) or {}

    def _build_search_params(self, page: int, category: dict[str, Any] | None) -> dict:
        offset = (page - 1) * PAGE_SIZE
        return {
            "count": "true",
            "q": build_encar_query(category),
            "sr": f"|ModifiedDate|{offset}|{PAGE_SIZE}",
        }

    def _parse_year(self, raw_year) -> int | None:
        # API가 202312 같은 연월 숫자로 반환 → 앞 4자리만 사용
        try:
            return int(str(int(raw_year))[:4])
        except (TypeError, ValueError):
            return None

    def _parse_seller_type(self, raw: dict) -> str:
        sell_type = raw.get("SellType", "")
        return "dealer" if sell_type in ("딜러", "상사") else "private"

    async def normalize(self, raw: dict, category: dict[str, Any] | None = None) -> dict:
        car_id = str(raw.get("Id", ""))
        if not car_id:
            return {}

        data = {
            "platform": self.PLATFORM,
            "external_id": car_id,
            "brand": raw.get("Manufacturer"),
            "model_group": raw.get("ModelGroup"),
            "model": raw.get("Model"),
            "year": self._parse_year(raw.get("Year")),
            "trim": raw.get("BadgeDetail") or raw.get("Badge"),
            "body_type": raw.get("BodyType") or raw.get("BodyName"),
            "is_domestic": self._parse_domestic(raw),
            "price": int(raw["Price"]) if raw.get("Price") else None,
            "mileage": int(raw["Mileage"]) if raw.get("Mileage") else None,
            "fuel": raw.get("FuelType"),
            "transmission": raw.get("Transmission"),
            "color": raw.get("Color"),
            "region": raw.get("OfficeCityState"),
            "seller_type": self._parse_seller_type(raw),
            "images": [p["location"] for p in raw.get("Photos", [])],
            "url": f"https://fem.encar.com/cars/detail/{car_id}",
            "raw_data": raw,
        }
        data.update(self._category_codes(raw, category))
        return data

    def _parse_domestic(self, raw: dict) -> bool | None:
        if raw.get("Manufacturer") in DOMESTIC_MAKES:
            return True
        if raw.get("Manufacturer"):
            return False
        return None

    def _category_codes(self, raw: dict, category: dict[str, Any] | None) -> dict:
        return {
            "platform_make_code": self._code(category, "make_code", raw.get("Manufacturer")),
            "platform_model_group_code": self._code(
                category, "model_group_code", raw.get("ModelGroup")
            ),
            "platform_model_code": self._code(category, "model_code", raw.get("Model")),
            "platform_grade_code": raw.get("Badge"),
            "platform_grade_detail_code": raw.get("BadgeDetail"),
        }

    def _code(self, category: dict[str, Any] | None, key: str, fallback: Any) -> str | None:
        if category and category.get(key):
            return str(category[key])
        return str(fallback) if fallback else None
