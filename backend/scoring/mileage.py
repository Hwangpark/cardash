from datetime import datetime


def score_mileage(data: dict, max_points: float) -> float:
    mileage = data.get("mileage", 0) or 0
    year    = data.get("year", 0) or 0      # 2자리 연도 (예: 22 = 2022)
    month   = data.get("month", 0) or 0

    if not year or not mileage:
        return round(max_points * 0.6 * 10) / 10

    now = datetime.now()
    full_year = 2000 + year if year < 100 else year

    if month > 0:
        age_months = max(1, (now.year - full_year) * 12 + (now.month - month))
    else:
        age_months = max(6, (now.year - full_year) * 12)

    age_years       = age_months / 12
    expected_mileage = max(8000, age_years * 15000)
    ratio            = mileage / expected_mileage if expected_mileage > 0 else 0

    if   ratio <= 0.45: deduction = 2.5
    elif ratio <= 0.65: deduction = 1.2
    elif ratio <= 1.15: deduction = 0.0
    elif ratio <= 1.35: deduction = 1.2
    elif ratio <= 1.60: deduction = 2.5
    elif ratio <= 1.90: deduction = 4.2
    elif ratio <= 2.30: deduction = 6.2
    else:               deduction = 8.3

    if mileage >= 250_000: deduction += 2.0
    if mileage >= 200_000: deduction += 2.0
    if mileage >= 160_000: deduction += 1.4
    if mileage >= 120_000: deduction += 0.8

    return max(0, round((max_points - deduction) * 10) / 10)
