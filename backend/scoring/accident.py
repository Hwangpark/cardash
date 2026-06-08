import re


def _calc_unavailable_months(periods: list[str]) -> int:
    total = 0
    for period in periods or []:
        m = re.search(r"(\d{6})~(\d{6})", str(period))
        if not m:
            continue
        s, e = m.group(1), m.group(2)
        total += (int(e[:4]) - int(s[:4])) * 12 + (int(e[4:6]) - int(s[4:6])) + 1
    return total


def _unavailable_penalty(data: dict) -> float:
    if not data.get("hasUnavailablePeriod"):
        return 0
    months = _calc_unavailable_months(data.get("unavailablePeriods", []))
    if months <= 1:
        return 0
    return max(1, months // 12) * 2


def score_accident(data: dict, max_points: float) -> float:
    status     = data.get("insuranceStatus", "unknown")
    origin     = data.get("totalOriginPrice") or data.get("originPrice", 0)
    amounts    = data.get("accidentAmounts", [])
    my_cnt     = data.get("myDamageCount", 0)
    other_cnt  = data.get("otherDamageCount", 0)
    rank_b     = (data.get("rankCounts") or {}).get("B", {})

    if status == "private":
        return 0

    if status == "unknown" or not data.get("hasRecordData"):
        base = max_points * 0.55
        if rank_b.get("X", 0) > 0:
            base = max(0, base - max_points * 0.25)
        elif rank_b.get("W", 0) > 0:
            base = max(0, base - max_points * 0.12)
        if data.get("hasUnavailablePeriod"):
            base = max(0, base - 2)
        return base

    base = max_points
    rank_a = (data.get("rankCounts") or {}).get("A", {})

    if not amounts and not my_cnt and not other_cnt:
        bx = rank_b.get("X", 0)
        bw = rank_b.get("W", 0)
        ax = rank_a.get("X", 0)
        if bx > 0:   base = max_points * 0.42
        elif bw > 0: base = max_points * 0.62
        elif ax > 0: base = max_points * 0.75
    elif not amounts:
        base = max_points * 0.65
    elif origin > 0:
        origin_won = origin * 10000
        max_ratio  = max(amounts) / origin_won
        if   max_ratio <= 0.05: base = max_points * 0.75
        elif max_ratio <= 0.10: base = max_points * 0.50
        elif max_ratio <= 0.20: base = max_points * 0.25
        else:                   base = max_points * 0.08
    else:
        mx = max(amounts)
        if   mx < 300_000:   base = max_points * 0.82
        elif mx < 1_000_000: base = max_points * 0.62
        elif mx < 3_000_000: base = max_points * 0.38
        elif mx < 7_000_000: base = max_points * 0.18
        else:                base = max_points * 0.05

    if   len(amounts) >= 3: base = max(0, base - 5)
    elif len(amounts) >= 2: base = max(0, base - 3)

    if data.get("hasUnavailablePeriod"):
        base = max(0, base - _unavailable_penalty(data))

    return round(base * 10) / 10
