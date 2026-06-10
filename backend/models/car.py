from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20))       # encar | kcar | kbchachacha | bobaedream
    external_id: Mapped[str] = mapped_column(String(50))    # 플랫폼 자체 ID

    brand: Mapped[Optional[str]] = mapped_column(String(50))
    model_group: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    trim: Mapped[Optional[str]] = mapped_column(String(100))
    body_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_domestic: Mapped[Optional[bool]] = mapped_column(Boolean)

    platform_make_code: Mapped[Optional[str]] = mapped_column(String(50))
    platform_model_group_code: Mapped[Optional[str]] = mapped_column(String(50))
    platform_model_code: Mapped[Optional[str]] = mapped_column(String(50))
    platform_grade_code: Mapped[Optional[str]] = mapped_column(String(50))
    platform_grade_detail_code: Mapped[Optional[str]] = mapped_column(String(50))

    price: Mapped[Optional[int]] = mapped_column(Integer)   # 만원 단위
    mileage: Mapped[Optional[int]] = mapped_column(Integer) # km
    fuel: Mapped[Optional[str]] = mapped_column(String(20))
    transmission: Mapped[Optional[str]] = mapped_column(String(20))
    color: Mapped[Optional[str]] = mapped_column(String(30))
    region: Mapped[Optional[str]] = mapped_column(String(50))
    seller_type: Mapped[Optional[str]] = mapped_column(String(10))  # dealer | private

    images: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)  # 원본 응답 보존
    url: Mapped[Optional[str]] = mapped_column(Text)

    listed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_platform_external_id"),
        Index("ix_cars_platform", "platform"),
        Index("ix_cars_brand_model", "brand", "model"),
        Index("ix_cars_model_group", "model_group"),
        Index("ix_cars_platform_make_code", "platform", "platform_make_code"),
        Index("ix_cars_platform_model_group_code", "platform", "platform_model_group_code"),
        Index("ix_cars_platform_model_code", "platform", "platform_model_code"),
        Index("ix_cars_price", "price"),
        Index("ix_cars_year", "year"),
    )
