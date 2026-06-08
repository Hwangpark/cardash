from datetime import datetime

RETENTION = [1.0, 0.85, 0.75, 0.66, 0.58, 0.52, 0.46, 0.41, 0.37, 0.33, 0.30]


def _ratio_to_score(ratio: float, max_points: float) -> float:
    if   ratio <= 0.90: return max_points
    if   ratio <= 0.97: return max_points * 0.95
    if   ratio <= 1.03: return max_points * 0.88
    if   ratio <= 1.08: return max_points * 0.80
    if   ratio <= 1.15: return max_points * 0.70
    if   ratio <= 1.25: return max_points * 0.55
    if   ratio <= 1.35: return max_points * 0.40
    return max_points * 0.25


def _retention_reference(origin_price: float, year: int) -> float:
    if not origin_price or not year:
        return 0
    full_year = 2000 + year if year < 100 else year
    age = max(1, datetime.now().year - full_year)
    return origin_price * RETENTION[min(age, 10)]


def score_price(data: dict, max_points: float) -> float:
    price        = data.get("price", 0) or 0
    origin       = data.get("totalOriginPrice") or data.get("originPrice", 0)
    year         = data.get("year", 0) or 0
    market       = data.get("marketPriceData") or {}

    if not price:
        return round(max_points * 0.5 * 10) / 10

    sample_count = market.get("sampleCount") or market.get("count") or 0
    market_ref   = market.get("median", 0) if sample_count >= 3 else 0
    origin_ref   = _retention_reference(origin, year)

    ref = market_ref or origin_ref
    if not ref:
        return round(max_points * 0.5 * 10) / 10

    return round(_ratio_to_score(price / ref, max_points) * 10) / 10
