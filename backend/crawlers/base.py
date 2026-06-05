import asyncio
import random
from abc import ABC, abstractmethod
from typing import Any

import httpx


class BaseCrawler(ABC):
    PLATFORM: str = ""
    DELAY_MIN: float = 3.0
    DELAY_MAX: float = 5.0
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Accept": "text/html,application/json,*/*",
    }

    @abstractmethod
    async def fetch_list(self, page: int, category: dict[str, Any] | None = None) -> list[dict]:
        ...

    @abstractmethod
    async def fetch_detail(self, external_id: str) -> dict:
        ...

    @abstractmethod
    async def normalize(self, raw: dict, category: dict[str, Any] | None = None) -> dict:
        ...

    async def run(self, max_pages: int = 50, category: dict[str, Any] | None = None):
        from database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            for page in range(1, max_pages + 1):
                items = await self.fetch_list(page, category)
                if not items:
                    break

                await self._run_page(db, items, category)
                await db.commit()
                await asyncio.sleep(random.uniform(self.DELAY_MIN, self.DELAY_MAX))

    async def _run_page(self, db, items: list[dict], category: dict[str, Any] | None):
        for raw in items:
            try:
                data = await self.normalize(raw, category)
                if data:
                    await self._persist_item(db, data)
            except Exception as e:
                print(f"[{self.PLATFORM}] error: {e}")

    async def _persist_item(self, db, data: dict):
        row = await self._upsert_car(db, data)
        if row and data.get("price"):
            await self._record_price(db, row.id, data["price"])

    async def _upsert_car(self, db, data: dict):
        from models import Car
        from sqlalchemy.dialects.postgresql import insert

        stmt = (
            insert(Car)
            .values(**data)
            .on_conflict_do_update(
                constraint="uq_platform_external_id",
                set_={k: v for k, v in data.items() if k not in ("platform", "external_id")},
            )
            .returning(Car.id, Car.price)
        )
        result = await db.execute(stmt)
        return result.fetchone()

    async def _record_price(self, db, car_id: int, price: int):
        from models import PriceHistory
        from sqlalchemy.dialects.postgresql import insert

        await db.execute(insert(PriceHistory).values(car_id=car_id, price=price))

    async def get(self, url: str, **kwargs) -> dict | None:
        """JSON API 호출"""
        async with httpx.AsyncClient(headers=self.HEADERS, timeout=15) as client:
            try:
                r = await client.get(url, **kwargs)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                print(f"[{self.PLATFORM}] GET JSON {url}: {e}")
                return None

    async def get_html(self, url: str, **kwargs) -> str | None:
        """HTML 페이지 호출 (SSR 크롤링용)"""
        headers = {**self.HEADERS, "Referer": url}
        async with httpx.AsyncClient(headers=headers, timeout=15, follow_redirects=True) as client:
            try:
                r = await client.get(url, **kwargs)
                r.raise_for_status()
                return r.text
            except Exception as e:
                print(f"[{self.PLATFORM}] GET HTML {url}: {e}")
                return None
