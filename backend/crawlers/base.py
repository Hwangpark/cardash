import asyncio
import random
from abc import ABC, abstractmethod

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
    }

    @abstractmethod
    async def fetch_list(self, page: int) -> list[dict]:
        ...

    @abstractmethod
    async def fetch_detail(self, external_id: str) -> dict:
        ...

    @abstractmethod
    async def normalize(self, raw: dict) -> dict:
        """플랫폼별 raw 데이터를 공통 CarCreate 딕셔너리로 변환"""
        ...

    async def run(self, max_pages: int = 50):
        from database import AsyncSessionLocal
        from models import Car, PriceHistory
        from sqlalchemy.dialects.postgresql import insert

        async with AsyncSessionLocal() as db:
            for page in range(1, max_pages + 1):
                items = await self.fetch_list(page)
                if not items:
                    break

                for raw in items:
                    try:
                        data = await self.normalize(raw)
                        if not data:
                            continue

                        stmt = insert(Car).values(**data).on_conflict_do_update(
                            constraint="uq_platform_external_id",
                            set_={k: v for k, v in data.items() if k not in ("platform", "external_id")},
                        ).returning(Car.id, Car.price)

                        result = await db.execute(stmt)
                        row = result.fetchone()
                        if row and data.get("price"):
                            await db.execute(
                                insert(PriceHistory).values(car_id=row.id, price=data["price"])
                            )
                    except Exception as e:
                        print(f"[{self.PLATFORM}] normalize error: {e}")

                await db.commit()
                await asyncio.sleep(random.uniform(self.DELAY_MIN, self.DELAY_MAX))

    async def get(self, url: str, **kwargs) -> dict | None:
        async with httpx.AsyncClient(headers=self.HEADERS, timeout=15) as client:
            try:
                r = await client.get(url, **kwargs)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                print(f"[{self.PLATFORM}] GET {url} error: {e}")
                return None
