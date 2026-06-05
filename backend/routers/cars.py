from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Car, PriceHistory, Score

router = APIRouter(prefix="/cars", tags=["cars"])


# ── 필터 헬퍼 ──────────────────────────────────────────

def _apply_platform(stmt, platform):
    return stmt.where(Car.platform == platform) if platform else stmt

def _apply_identity(stmt, brand, model_group, model):
    if brand:       stmt = stmt.where(Car.brand == brand)
    if model_group: stmt = stmt.where(Car.model_group == model_group)
    if model:       stmt = stmt.where(Car.model.ilike(f"%{model}%"))
    return stmt

def _apply_ranges(stmt, year_min, year_max, price_min, price_max, mileage_max):
    if year_min:    stmt = stmt.where(Car.year >= year_min)
    if year_max:    stmt = stmt.where(Car.year <= year_max)
    if price_min:   stmt = stmt.where(Car.price >= price_min)
    if price_max:   stmt = stmt.where(Car.price <= price_max)
    if mileage_max: stmt = stmt.where(Car.mileage <= mileage_max)
    return stmt

def _apply_region(stmt, region):
    return stmt.where(Car.region.ilike(f"%{region}%")) if region else stmt


# ── 엔드포인트 ──────────────────────────────────────────

@router.get("/filter-options")
async def get_filter_options(
    platform: str = Query("encar"),
    db: AsyncSession = Depends(get_db),
):
    """리스트 필터 드롭다운용 — cars 테이블에서 distinct 값 반환"""
    base = select(Car).where(Car.platform == platform)

    brands_r = await db.execute(
        select(distinct(Car.brand)).where(Car.platform == platform, Car.brand.is_not(None)).order_by(Car.brand)
    )
    mg_r = await db.execute(
        select(Car.brand, Car.model_group)
        .where(Car.platform == platform, Car.brand.is_not(None), Car.model_group.is_not(None))
        .distinct().order_by(Car.brand, Car.model_group)
    )
    years_r = await db.execute(
        select(distinct(Car.year)).where(Car.platform == platform, Car.year.is_not(None)).order_by(Car.year.desc())
    )
    regions_r = await db.execute(
        select(distinct(Car.region)).where(Car.platform == platform, Car.region.is_not(None)).order_by(Car.region)
    )

    model_groups: dict[str, list[str]] = {}
    for brand, mg in mg_r.all():
        model_groups.setdefault(brand, []).append(mg)

    return {
        "brands":       [r[0] for r in brands_r.all()],
        "model_groups": model_groups,
        "years":        [r[0] for r in years_r.all()],
        "regions":      [r[0] for r in regions_r.all()],
    }


@router.get("")
async def list_cars(
    platform: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    model_group: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    price_min: Optional[int] = Query(None),
    price_max: Optional[int] = Query(None),
    mileage_max: Optional[int] = Query(None),
    region: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Car)
    stmt = _apply_platform(stmt, platform)
    stmt = _apply_identity(stmt, brand, model_group, model)
    stmt = _apply_ranges(stmt, year_min, year_max, price_min, price_max, mileage_max)
    stmt = _apply_region(stmt, region)
    stmt = stmt.order_by(Car.crawled_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return {"items": result.scalars().all(), "page": page, "size": size}


@router.get("/{car_id}")
async def get_car(car_id: int, db: AsyncSession = Depends(get_db)):
    car = await db.get(Car, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    result = await db.execute(select(Score).where(Score.car_id == car_id))
    return {"car": car, "score": result.scalar_one_or_none()}


@router.post("/{car_id}/analyze")
async def analyze_car(car_id: int, db: AsyncSession = Depends(get_db)):
    """클릭 시 on-demand로 상세 API 호출 → 채점 → 저장"""
    car = await db.get(Car, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    from services.analyzer import fetch_and_score
    score_data = await fetch_and_score(car.platform, car.external_id)

    result = await db.execute(select(Score).where(Score.car_id == car_id))
    score = result.scalar_one_or_none()
    if score:
        for k, v in score_data.items():
            setattr(score, k, v)
    else:
        score = Score(car_id=car_id, **score_data)
        db.add(score)

    await db.commit()
    await db.refresh(score)
    return {"car": car, "score": score}


@router.get("/{car_id}/history")
async def get_price_history(car_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.car_id == car_id)
        .order_by(PriceHistory.recorded_at)
    )
    return result.scalars().all()
