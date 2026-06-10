from typing import Optional

from pydantic import BaseModel, ConfigDict


class AccidentRecord(BaseModel):
    date: Optional[str] = None
    insurance_benefit: int
    part_cost: int
    labor_cost: int
    painting_cost: int


class ScoreSummary(BaseModel):
    grade: str
    accident_free: Optional[bool] = None
    owner_change_count: Optional[int] = None


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    grade: str
    accident: float
    mileage: float
    price: float
    inspection: float
    rental: float
    owner_changes: float
    penalty: int
    no_insurance_data: bool
    insurance_fetch_status: str
    accident_history: Optional[list[AccidentRecord]] = None
    owner_change_count: Optional[int] = None
