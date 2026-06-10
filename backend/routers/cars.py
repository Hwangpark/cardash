from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Car, PriceHistory, Score
from schemas.car import CarDetailResponse, CarListItem, CarListResponse, CarOut

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

GRADE_ORDER = ["S", "A+", "A", "B", "C", "D", "F"]


def _apply_grade_filter(stmt, grade_min):
    if not grade_min or grade_min not in GRADE_ORDER:
        return stmt
    allowed = GRADE_ORDER[:GRADE_ORDER.index(grade_min) + 1]
    return stmt.where(Score.grade.in_(allowed))


INSURANCE_FETCHED_STATUSES = ("available", "private")


def _apply_score_filters(stmt, accident_free, owner_changes_max, has_insurance_data):
    if accident_free:
        stmt = stmt.where(
            Score.no_insurance_data.is_(False),
            func.jsonb_array_length(Score.accident_history) == 0,
        )
    if owner_changes_max is not None:
        stmt = stmt.where(Score.owner_change_count <= owner_changes_max)
    if has_insurance_data:
        stmt = stmt.where(Score.insurance_fetch_status.in_(INSURANCE_FETCHED_STATUSES))
    return stmt


SORT_OPTIONS = {
    "crawled_at_desc": Car.crawled_at.desc(),
    "price_asc": Car.price.asc(),
    "price_desc": Car.price.desc(),
    "mileage_asc": Car.mileage.asc(),
    "year_desc": Car.year.desc(),
}


def _resolve_sort(sort: str):
    try:
        return SORT_OPTIONS[sort]
    except KeyError:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported sort: {sort}. Available: {list(SORT_OPTIONS.keys())}",
        )


def _score_summary(score: Optional[Score]) -> Optional[dict]:
    if not score:
        return None
    if score.no_insurance_data:
        accident_free = None          # 보험 데이터 없음 — 미지 상태
    else:
        accident_free = not (score.accident_history or [])
    return {
        "grade": score.grade,
        "accident_free": accident_free,
        "owner_change_count": score.owner_change_count,
    }


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


@router.get("", response_model=CarListResponse)
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
    grade_min: Optional[str] = Query(None),
    accident_free: Optional[bool] = Query(None),
    owner_changes_max: Optional[int] = Query(None),
    has_insurance_data: Optional[bool] = Query(None),
    sort: str = Query("crawled_at_desc"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    order_by = _resolve_sort(sort)

    base_stmt = select(Car, Score).outerjoin(Score, Score.car_id == Car.id)
    base_stmt = _apply_platform(base_stmt, platform)
    base_stmt = _apply_identity(base_stmt, brand, model_group, model)
    base_stmt = _apply_ranges(base_stmt, year_min, year_max, price_min, price_max, mileage_max)
    base_stmt = _apply_region(base_stmt, region)
    base_stmt = _apply_grade_filter(base_stmt, grade_min)
    base_stmt = _apply_score_filters(base_stmt, accident_free, owner_changes_max, has_insurance_data)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = base_stmt.order_by(order_by).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)

    items = [
        CarListItem(
            **CarOut.model_validate(car, from_attributes=True).model_dump(),
            score_summary=_score_summary(score),
        )
        for car, score in result.all()
    ]
    has_next = (page * size) < total
    return CarListResponse(items=items, page=page, size=size, total=total, has_next=has_next)


@router.get("/{car_id}", response_model=CarDetailResponse)
async def get_car(car_id: int, db: AsyncSession = Depends(get_db)):
    car = await db.get(Car, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    result = await db.execute(select(Score).where(Score.car_id == car_id))
    return {"car": car, "score": result.scalar_one_or_none()}


@router.post("/{car_id}/analyze", response_model=CarDetailResponse)
async def analyze_car(car_id: int, db: AsyncSession = Depends(get_db)):
    """클릭 시 on-demand로 상세 API 호출 → 채점 → 저장"""
    car = await db.get(Car, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    from services.analyzer import fetch_and_score
    score_data = await fetch_and_score(car.platform, car.external_id, car=car)

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
