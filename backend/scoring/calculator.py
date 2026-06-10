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

NO_INSURANCE_MAX_TOTAL = 89  # grade.py A+ 임계값(90) 미만으로 유지


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
        scores["accident"] = w["accident"] * 0.40

    total = round(sum(v for v in scores.values() if v is not None))

    penalty = 0
    if car_data.get("isInsurancePrivate") or car_data.get("isInspectionPrivate"):
        penalty = 40
        total -= penalty

    total = max(0, min(100, total))

    if no_insurance:
        total = min(total, NO_INSURANCE_MAX_TOTAL)

    grade = get_grade(total)

    return {
        "total":            total,
        "grade":            grade,
        "accident":         scores["accident"] or 0,
        "mileage":          scores["mileage"],
        "price":            scores["price"],
        "inspection":       scores["inspection"],
        "rental":           scores["rental"],
        "owner_changes":    scores["owner_changes"],
        "penalty":          penalty,
        "no_insurance_data": no_insurance,
        "insurance_fetch_status": car_data.get("insuranceFetchStatus", "not_applicable"),
    }
