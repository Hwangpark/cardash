from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class VehicleCategory(Base):
    __tablename__ = "vehicle_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vehicle_categories.id", ondelete="CASCADE")
    )
    count: Mapped[int] = mapped_column(Integer, default=0)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent = relationship("VehicleCategory", remote_side=[id], backref="children")

    __table_args__ = (
        UniqueConstraint(
            "platform", "level", "code", "parent_id", name="uq_vehicle_category_path"
        ),
        Index("ix_vehicle_categories_platform_level", "platform", "level"),
        Index("ix_vehicle_categories_parent_id", "parent_id"),
    )
