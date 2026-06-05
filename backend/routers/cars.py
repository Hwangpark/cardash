from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Car, PriceHistory, Score

router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("")
async def list_cars(
    platform: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    price_min: Optional[int] = Query(None),
    price_max: Optional[int] = Query(None),
    mileage_max: Optional[int] = Query(None),
    grade: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Car)
    if platform:
        stmt = stmt.where(Car.platform == platform)
    if brand:
        stmt = stmt.where(Car.brand == brand)
    if model:
        stmt = stmt.where(Car.model.ilike(f"%{model}%"))
    if year_min:
        stmt = stmt.where(Car.year >= year_min)
    if year_max:
        stmt = stmt.where(Car.year <= year_max)
    if price_min:
        stmt = stmt.where(Car.price >= price_min)
    if price_max:
        stmt = stmt.where(Car.price <= price_max)
    if mileage_max:
        stmt = stmt.where(Car.mileage <= mileage_max)
    if region:
        stmt = stmt.where(Car.region.ilike(f"%{region}%"))

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    cars = result.scalars().all()
    return {"items": cars, "page": page, "size": size}


@router.get("/{car_id}")
async def get_car(car_id: int, db: AsyncSession = Depends(get_db)):
    car = await db.get(Car, car_id)
    score = await db.execute(select(Score).where(Score.car_id == car_id))
    return {"car": car, "score": score.scalar_one_or_none()}


@router.get("/{car_id}/history")
async def get_price_history(car_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.car_id == car_id)
        .order_by(PriceHistory.recorded_at)
    )
    return result.scalars().all()
