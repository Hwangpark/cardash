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
        if not data:
            return []
        return data.get("SearchResults", [])

    async def fetch_detail(self, external_id: str) -> dict:
        url = f"{API_BASE}/v1/readside/vehicle/{external_id}"
        return await self.get(url) or {}

    async def normalize(self, raw: dict) -> dict:
        car_id = str(raw.get("Id", ""))
        if not car_id:
            return {}

        category = raw.get("Category", {})
        spec = raw.get("Spec", {})
        ad = raw.get("Advertisement", {})

        return {
            "platform": self.PLATFORM,
            "external_id": car_id,
            "brand": category.get("Manufacturer"),
            "model": category.get("Model"),
            "year": category.get("Year"),
            "trim": category.get("Grade"),
            "price": ad.get("Price"),
            "mileage": spec.get("Mileage"),
            "fuel": spec.get("FuelType"),
            "transmission": spec.get("Transmission"),
            "color": spec.get("Color"),
            "region": ad.get("Region"),
            "seller_type": "dealer" if raw.get("IsDealer") else "private",
            "url": f"https://fem.encar.com/cars/detail/{car_id}",
            "raw_data": raw,
        }
