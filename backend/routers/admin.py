from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from crawlers import CRAWLERS
from database import get_db
from services.category_service import build_category_context, refresh_categories

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/crawl")
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    platform: str = "encar",
    category_id: Optional[int] = None,
    make: Optional[str] = None,
    model_group: Optional[str] = None,
    max_pages: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """크롤 트리거.
    - platform: encar | kcar | kbchachacha | bobaedream
    - category_id: vehicle_categories 테이블 기반 필터 (엔카 전용)
    - make + model_group: 제조사/모델그룹 직접 지정 (엔카 전용)
    """
    _validate_platform(platform)
    category = await _resolve_category(db, platform, category_id, make, model_group)
    CrawlerClass = CRAWLERS[platform]

    async def run():
        crawler = CrawlerClass()
        await crawler.run(max_pages=max_pages, category=category)

    background_tasks.add_task(run)
    return {
        "status": "started",
        "platform": platform,
        "category": category,
        "max_pages": max_pages,
    }


@router.post("/categories/refresh")
async def refresh_platform_categories(
    platform: str = "encar",
    db: AsyncSession = Depends(get_db),
):
    _validate_platform(platform)
    try:
        return await refresh_categories(platform, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/platforms")
async def list_platforms():
    """지원 플랫폼 목록"""
    return {"platforms": list(CRAWLERS.keys())}


def _validate_platform(platform: str):
    if platform not in CRAWLERS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported platform: {platform}. Available: {list(CRAWLERS.keys())}",
        )


async def _resolve_category(
    db: AsyncSession,
    platform: str,
    category_id: int | None,
    make: str | None,
    model_group: str | None,
) -> dict | None:
    if category_id:
        category = await build_category_context(db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        if category["platform"] != platform:
            raise HTTPException(status_code=422, detail="Category platform mismatch")
        return category

    if make or model_group:
        return {"platform": platform, "make_code": make, "model_group_code": model_group}

    return None
