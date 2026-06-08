def score_owner(data: dict, max_points: float) -> float:
    count = data.get("ownerChangeCount", 0) or 0

    if count == 0: return max_points
    if count == 1: ratio = 0.35
    elif count == 2: ratio = 0.60
    elif count == 3: ratio = 0.82
    else: ratio = 1.0

    return max(0, round(max_points * (1 - ratio) * 10) / 10)
