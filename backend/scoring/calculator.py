from scoring.accident import score_accident
from scoring.grade import get_grade
from scoring.inspection import score_inspection
from scoring.mileage import score_mileage
from scoring.owner import score_owner
from scoring.price import score_price
from scoring.rental import score_rental

DEFAULT_WEIGHTS = {
    "accident":     25,
    "inspection":   20,
    "mileage":      15,
    "price":        15,
    "rental":       15,
    "owner_changes": 10,
}


def calculate_score(car_data: dict, weights: dict | None = None) -> dict:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    no_insurance = (
        not car_data.get("hasRecordData")
        and car_data.get("insuranceStatus") != "private"
    )

    scores = {
        "accident":     None if no_insurance else score_accident(car_data, w["accident"]),
        "mileage":      score_mileage(car_data, w["mileage"]),
        "price":        score_price(car_data, w["price"]),
        "inspection":   score_inspection(car_data, w["inspection"]),
        "rental":       score_rental(car_data, w["rental"]),
        "owner_changes": score_owner(car_data, w["owner_changes"]),
    }

    if no_insurance:
        estimated_accident = w["accident"] * 0.40
        rest = sum(v for k, v in scores.items() if k != "accident" and v is not None)
        total = round(estimated_accident + rest)
    else:
        total = round(sum(v for v in scores.values() if v is not None))

    penalty = 0
    if car_data.get("isInsurancePrivate") or car_data.get("isInspectionPrivate"):
        penalty = 40
        total -= penalty

    total = max(0, min(100, total))

    return {
        "total":            total,
        "grade":            get_grade(total),
        "accident":         scores["accident"] or 0,
        "mileage":          scores["mileage"],
        "price":            scores["price"],
        "inspection":       scores["inspection"],
        "rental":           scores["rental"],
        "owner_changes":    scores["owner_changes"],
        "penalty":          penalty,
        "no_insurance_data": no_insurance,
    }
