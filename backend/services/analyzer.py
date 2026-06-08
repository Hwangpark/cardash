"""엔카 상세 API 호출 → carData 파싱 → 채점"""
import asyncio
import re

import httpx

from scoring import calculate_score

API_BASE = "https://api.encar.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://car.encar.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def fetch_and_score(platform: str, external_id: str) -> dict:
    if platform != "encar":
        return _default_score()

    vehicle, record, inspection = await _fetch_all(external_id)
    car_data = _build_car_data(vehicle, record, inspection)
    return calculate_score(car_data)


async def _fetch_all(external_id: str) -> tuple[dict, dict | None, dict | None]:
    urls = [
        f"{API_BASE}/v1/readside/vehicle/{external_id}",
        f"{API_BASE}/v1/readside/record/vehicle/{external_id}/open",
        f"{API_BASE}/v1/readside/inspection/vehicle/{external_id}",
    ]
    results = await asyncio.gather(*[_get(u) for u in urls])
    return results[0] or {}, results[1], results[2]


async def _get(url: str) -> dict | None:
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as c:
        try:
            r = await c.get(url)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None


def _build_car_data(vehicle: dict, record: dict | None, inspection: dict | None) -> dict:
    v = _parse_vehicle(vehicle)
    r = _parse_record(record)
    i = _parse_inspection(inspection)
    return {**v, **r, **i}


def _parse_vehicle(data: dict) -> dict:
    cat  = data.get("category", {})
    adv  = data.get("advertisement", {})
    spec = data.get("spec", {})

    ym = str(cat.get("yearMonth", ""))
    year  = int(cat["formYear"]) - 2000 if cat.get("formYear") else (int(ym[:4]) - 2000 if len(ym) >= 4 else 0)
    month = int(ym[4:6]) if len(ym) >= 6 else 0

    origin = _to_wan(cat.get("originPrice", 0))
    return {
        "year":            year,
        "month":           month,
        "mileage":         _to_int(spec.get("mileage", 0)),
        "price":           _to_wan(adv.get("price", 0)),
        "originPrice":     origin,
        "totalOriginPrice": origin,
        "hasDiagnosis":    bool(adv.get("diagnosisCar")),
    }


def _parse_record(data: dict | None) -> dict:
    if data is None:
        return {"insuranceStatus": "private", "isInsurancePrivate": True, "hasRecordData": False}

    if data.get("openData") is False:
        return {"insuranceStatus": "private", "isInsurancePrivate": True, "hasRecordData": False}

    my_cnt   = _to_int(data.get("myAccidentCnt", 0))
    my_cost  = _to_int(data.get("myAccidentCost", 0))
    amounts  = []

    for acc in data.get("accidents", []):
        benefit = _to_int(acc.get("insuranceBenefit", 0))
        if benefit > 0:
            amounts.append(benefit)

    if not amounts and my_cost > 0:
        per = my_cost // max(my_cnt, 1)
        amounts = [per] * max(my_cnt, 1)

    periods = []
    for i in range(1, 6):
        p = str(data.get(f"notJoinDate{i}", "") or "").strip()
        if p:
            periods.append(p)

    use_history = data.get("carInfoUse1s", []) or []
    has_rental  = any(str(u) == "3" for u in use_history)
    has_change  = len(set(str(u) for u in use_history)) > 1 if len(use_history) > 1 else False

    return {
        "insuranceStatus":    "available",
        "isInsurancePrivate": False,
        "hasRecordData":      True,
        "accidentAmounts":    amounts,
        "myDamageCount":      my_cnt,
        "otherDamageCount":   _to_int(data.get("otherAccidentCnt", 0)),
        "hasUnavailablePeriod": bool(periods),
        "unavailablePeriods": periods,
        "ownerChangeCount":   _to_int(data.get("ownerChangeCnt", 0)),
        "hasRentalHistory":   has_rental,
        "hasUsageChange":     has_change,
    }


def _parse_inspection(data: dict | None) -> dict:
    if not data:
        return {"isInspectionPrivate": False, "hasInspection": False}

    if not data.get("formats") and not data.get("master"):
        return {"isInspectionPrivate": False, "hasInspection": False}

    counts = {r: {"X": 0, "W": 0, "C": 0} for r in ("B", "A", "TWO", "ONE")}
    has_replacement = has_welding = has_corrosion = False

    for item in data.get("outers", []):
        attrs = item.get("attributes", [])
        rank = "ONE"
        if "RANK_B"   in attrs: rank = "B"
        elif "RANK_A" in attrs: rank = "A"
        elif "RANK_TWO" in attrs: rank = "TWO"

        for status in item.get("statusTypes", []):
            code = str(status.get("code", "")).upper()
            if   code == "X": counts[rank]["X"] += 1; has_replacement = True
            elif code == "W": counts[rank]["W"] += 1; has_welding = True
            elif code in ("C", "T"): counts[rank]["C"] += 1; has_corrosion = True

    has_any = any(counts[r][k] > 0 for r in counts for k in counts[r])

    master = data.get("master", {}) or {}
    usage_types = (master.get("detail", {}) or {}).get("usageChangeTypes", []) or []
    rental_from_inspection = any(
        str(t.get("code")) == "1" or t.get("title") == "렌트"
        for t in usage_types
    )

    return {
        "isInspectionPrivate": False,
        "hasInspection":       True,
        "hasReplacement":      has_replacement,
        "hasWelding":          has_welding,
        "hasCorrosion":        has_corrosion,
        "rankCounts":          counts if has_any else None,
        "_rentalFromInspection": rental_from_inspection,
    }


def _to_int(v) -> int:
    try:
        return int(v) if v else 0
    except (ValueError, TypeError):
        return 0


def _to_wan(v) -> int:
    """원 단위 또는 만원 단위를 만원으로 정규화"""
    amount = _to_int(v)
    if amount >= 100_000:
        return amount // 10_000
    return amount


def _default_score() -> dict:
    return {
        "total": 60, "grade": "C",
        "accident": 12.5, "mileage": 9.0, "price": 9.0,
        "inspection": 10.0, "rental": 15.0, "owner_changes": 8.0,
        "penalty": 0, "no_insurance_data": True,
    }
