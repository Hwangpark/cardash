from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from schemas.score import ScoreOut, ScoreSummary


class CarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    external_id: str
    brand: Optional[str] = None
    model_group: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    trim: Optional[str] = None
    price: Optional[int] = None
    mileage: Optional[int] = None
    fuel: Optional[str] = None
    transmission: Optional[str] = None
    color: Optional[str] = None
    region: Optional[str] = None
    seller_type: Optional[str] = None
    images: Optional[list[str]] = None
    url: Optional[str] = None
    crawled_at: datetime


class CarListItem(CarOut):
    score_summary: Optional[ScoreSummary] = None


class CarListResponse(BaseModel):
    items: list[CarListItem]
    page: int
    size: int
    total: int
    has_next: bool


class CarDetailResponse(BaseModel):
    car: CarOut
    score: Optional[ScoreOut] = None
