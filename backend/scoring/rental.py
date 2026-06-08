def score_rental(data: dict, max_points: float) -> float:
    if data.get("hasRentalHistory"):  return 0
    if data.get("hasUsageChange"):    return round(max_points * 0.3 * 10) / 10
    return max_points
