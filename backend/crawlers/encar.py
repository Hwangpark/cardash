from crawlers.base import BaseCrawler

API_BASE = "https://api.encar.com"
SEARCH_URL = f"{API_BASE}/search/car/list/mobile"


class EncarCrawler(BaseCrawler):
    PLATFORM = "encar"

    async def fetch_list(self, page: int) -> list[dict]:
        params = {
            "count": "true",
            "q": "(And.Hidden.N._.CarType.A.)",
            "sr": f"|ModifiedDate|{(page - 1) * 40}|40",
        }
        data = await self.get(SEARCH_URL, params=params)
        return (data or {}).get("SearchResults", [])

    async def fetch_detail(self, external_id: str) -> dict:
        url = f"{API_BASE}/v1/readside/vehicle/{external_id}"
        return await self.get(url) or {}

    def _parse_year(self, raw_year) -> int | None:
        # API가 202312 같은 연월 숫자로 반환 → 앞 4자리만 사용
        try:
            return int(str(int(raw_year))[:4])
        except (TypeError, ValueError):
            return None

    def _parse_seller_type(self, raw: dict) -> str:
        sell_type = raw.get("SellType", "")
        return "dealer" if sell_type in ("딜러", "상사") else "private"

    async def normalize(self, raw: dict) -> dict:
        car_id = str(raw.get("Id", ""))
        if not car_id:
            return {}

        return {
            "platform": self.PLATFORM,
            "external_id": car_id,
            "brand": raw.get("Manufacturer"),
            "model": raw.get("Model"),
            "year": self._parse_year(raw.get("Year")),
            "trim": raw.get("Badge"),
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
