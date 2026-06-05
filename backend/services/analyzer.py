import httpx

API_BASE = "https://api.encar.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://car.encar.com/",
}


async def _get(url: str) -> dict:
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as c:
        try:
            r = await c.get(url)
            return r.json() if r.status_code == 200 else {}
        except Exception:
            return {}


async def _fetch_encar_detail(external_id: str) -> dict:
    vehicle, record, inspection = await _get_all_encar(external_id)
    return _normalize_encar(external_id, vehicle, record, inspection)


async def _get_all_encar(external_id: str):
    import asyncio
    return await asyncio.gather(
        _get(f"{API_BASE}/v1/readside/vehicle/{external_id}"),
        _get(f"{API_BASE}/v1/readside/record/vehicle/{external_id}/open"),
        _get(f"{API_BASE}/v1/readside/inspection/vehicle/{external_id}"),
    )


def _normalize_encar(external_id: str, vehicle: dict, record: dict, inspection: dict) -> dict:
    category = vehicle.get("category", {})
    ad = vehicle.get("advertisement", {})
    spec = vehicle.get("spec", {})

    return {
        "external_id": external_id,
        "origin_price": category.get("originPrice", 0),
        "mileage": spec.get("mileage", 0),
        "year_month": category.get("yearMonth", ""),
        "has_record_data": bool(record.get("openData")),
        "is_insurance_private": record.get("openData") == "N",
        "my_accident_cnt": record.get("myAccidentCnt", 0),
        "my_accident_cost": record.get("myAccidentCost", 0),
        "other_accident_cnt": record.get("otherAccidentCnt", 0),
        "other_accident_cost": record.get("otherAccidentCost", 0),
        "owner_change_cnt": record.get("ownerChangeCnt", 0),
        "accidents": record.get("accidents", []),
        "not_join_days": _calc_not_join_days(record),
        "inspection_data": inspection,
        "has_rental": _has_rental(record),
        "usage_change": _has_usage_change(record),
        "ad_price": ad.get("price", 0),
        "is_diagnosis": ad.get("diagnosisCar", False),
    }


def _calc_not_join_days(record: dict) -> int:
    fields = ["notJoinDate1", "notJoinDate2", "notJoinDate3", "notJoinDate4", "notJoinDate5"]
    return sum(record.get(f, 0) or 0 for f in fields)


def _has_rental(record: dict) -> bool:
    for change in record.get("carInfoUse1s", []):
        if "렌트" in str(change.get("useType", "")):
            return True
    return False


def _has_usage_change(record: dict) -> bool:
    return bool(record.get("carInfoUse1s"))


def _score_stub(car_data: dict) -> dict:
    """채점 로직 포팅 전 임시 — 항목별 50% 기본값"""
    return {
        "total": 70,
        "grade": "B",
        "accident": 12.5,
        "mileage": 7.5,
        "price": 7.5,
        "inspection": 10.0,
        "rental": 15.0,
        "owner_changes": 8.0,
        "penalty": 0,
        "no_insurance_data": not car_data.get("has_record_data", True),
    }


async def fetch_and_score(platform: str, external_id: str) -> dict:
    if platform == "encar":
        car_data = await _fetch_encar_detail(external_id)
    else:
        car_data = {"external_id": external_id}

    return _score_stub(car_data)
