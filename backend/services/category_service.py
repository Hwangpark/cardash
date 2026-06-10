from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crawlers.encar import EncarCrawler
from models import VehicleCategory

SUPPORTED_PLATFORMS = {"encar"}


async def refresh_categories(platform: str, db: AsyncSession) -> dict:
    _validate_platform(platform)
    crawler = EncarCrawler()
    stats = {"make": 0, "model_group": 0, "model": 0}

    for make in await crawler.fetch_make_categories():
        make_row = await upsert_category(db, platform, make)
        stats["make"] += 1
        await _refresh_model_groups(db, crawler, platform, make, make_row, stats)

    await db.commit()
    return {"platform": platform, "counts": stats}


async def list_categories(
    db: AsyncSession, platform: str, level: str, parent_id: int | None
) -> list[VehicleCategory]:
    stmt = select(VehicleCategory).where(
        VehicleCategory.platform == platform,
        VehicleCategory.level == level,
    )
    stmt = _apply_parent_filter(stmt, parent_id)
    result = await db.execute(stmt.order_by(VehicleCategory.count.desc(), VehicleCategory.name))
    return list(result.scalars().all())


async def build_category_context(db: AsyncSession, category_id: int | None) -> dict | None:
    if category_id is None:
        return None

    chain = await _load_category_chain(db, category_id)
    if not chain:
        return None

    return _build_context(chain)


async def upsert_category(
    db: AsyncSession, platform: str, payload: dict, parent_id: int | None = None
) -> VehicleCategory:
    category = await _find_category(db, platform, payload, parent_id)
    if not category:
        category = VehicleCategory(platform=platform, parent_id=parent_id, **payload)
        db.add(category)

    _update_category(category, payload)
    await db.flush()
    return category


def serialize_category(category: VehicleCategory) -> dict:
    return {
        "id": category.id,
        "platform": category.platform,
        "level": category.level,
        "name": category.name,
        "code": category.code,
        "parent_id": category.parent_id,
        "count": category.count,
        "last_seen_at": category.last_seen_at,
    }


async def _refresh_model_groups(db, crawler, platform, make, make_row, stats):
    for model_group in await crawler.fetch_model_group_categories(make):
        group_row = await upsert_category(db, platform, model_group, make_row.id)
        stats["model_group"] += 1
        await _refresh_models(db, crawler, platform, make, model_group, group_row, stats)


async def _refresh_models(db, crawler, platform, make, model_group, group_row, stats):
    for model in await crawler.fetch_model_categories(make, model_group):
        await upsert_category(db, platform, model, group_row.id)
        stats["model"] += 1


async def _find_category(db, platform, payload, parent_id):
    stmt = select(VehicleCategory).where(
        VehicleCategory.platform == platform,
        VehicleCategory.level == payload["level"],
        VehicleCategory.code == payload["code"],
    )
    stmt = _apply_parent_filter(stmt, parent_id)
    result = await db.execute(stmt.limit(1))
    return result.scalar_one_or_none()


def _update_category(category: VehicleCategory, payload: dict):
    category.name = payload["name"]
    category.count = payload.get("count") or 0
    category.raw_data = payload.get("raw_data")
    category.last_seen_at = datetime.now(timezone.utc)


def _apply_parent_filter(stmt, parent_id: int | None):
    if parent_id is None:
        return stmt.where(VehicleCategory.parent_id.is_(None))
    return stmt.where(VehicleCategory.parent_id == parent_id)


async def _load_category_chain(db, category_id: int) -> list[VehicleCategory]:
    chain = []
    current = await db.get(VehicleCategory, category_id)
    while current:
        chain.append(current)
        current = await db.get(VehicleCategory, current.parent_id) if current.parent_id else None
    return list(reversed(chain))


def _build_context(chain: list[VehicleCategory]) -> dict[str, Any]:
    context = {"platform": chain[-1].platform, "category_id": chain[-1].id}
    for category in chain:
        context[f"{category.level}_code"] = category.code
        context[f"{category.level}_name"] = category.name
    return context


def _validate_platform(platform: str):
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")
