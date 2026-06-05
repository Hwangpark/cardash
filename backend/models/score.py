from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_id: Mapped[int] = mapped_column(Integer, ForeignKey("cars.id", ondelete="CASCADE"), unique=True)

    total: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(3))    # S, A+, A, B, C, D, F

    accident: Mapped[float] = mapped_column(Float, default=0)
    mileage: Mapped[float] = mapped_column(Float, default=0)
    price: Mapped[float] = mapped_column(Float, default=0)
    inspection: Mapped[float] = mapped_column(Float, default=0)
    rental: Mapped[float] = mapped_column(Float, default=0)
    owner_changes: Mapped[float] = mapped_column(Float, default=0)

    penalty: Mapped[int] = mapped_column(Integer, default=0)
    no_insurance_data: Mapped[bool] = mapped_column(default=False)

    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    car = relationship("Car", backref="score")
