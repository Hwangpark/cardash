"""미채점 차량을 백그라운드로 점진 채점 — 스케줄러에서 주기 호출"""
import asyncio
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crawlers.base import BaseCrawler
from models import Car, Score
from services.analyzer import fetch_and_score


async def score_unscored_batch(db: AsyncSession, limit: int = 25) -> int:
    """Score.id가 없는 차량을 최근 크롤된 순으로 limit개 채점한다."""
    cars = await _fetch_unscored_cars(db, limit)
    for car in cars:
        await _score_one(db, car)
        await asyncio.sleep(random.uniform(BaseCrawler.DELAY_MIN, BaseCrawler.DELAY_MAX))

    if cars:
        await db.commit()
    return len(cars)


async def _fetch_unscored_cars(db: AsyncSession, limit: int) -> list[Car]:
    stmt = (
        select(Car)
        .outerjoin(Score, Score.car_id == Car.id)
        .where(Score.id.is_(None))
        .order_by(Car.crawled_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _score_one(db: AsyncSession, car: Car):
    try:
        score_data = await fetch_and_score(car.platform, car.external_id, car=car)
        db.add(Score(car_id=car.id, **score_data))
    except Exception as e:
        print(f"[scorer] car_id={car.id} error: {e}")
