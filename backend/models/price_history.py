from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_id: Mapped[int] = mapped_column(Integer, ForeignKey("cars.id", ondelete="CASCADE"))
    price: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    car = relationship("Car", backref="price_history")

    __table_args__ = (
        Index("ix_price_history_car_id", "car_id"),
        Index("ix_price_history_recorded_at", "recorded_at"),
    )
