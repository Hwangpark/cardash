"""엔카 상세 API 호출 → carData 파싱 → 채점"""
import asyncio
import logging
import re

import httpx

from scoring import calculate_score

API_BASE = "https://api.encar.com"
logger = logging.getLogger(__name__)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://car.encar.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


async def fetch_and_score(platform: str, external_id: str, *, car=None) -> dict:
    """플랫폼에 따라 채점 방식을 분기한다.
    encar: 보험이력·성능점검 API 3개 병렬 호출 후 완전 채점
    기타:  크롤 데이터(주행거리·연식·가격)로 부분 채점 (car 인자 필요)
    """
    if platform == "encar":
        return await _score_encar(external_id)
    if car is not None:
        return _score_partial(car)
    return _default_score()


async def _score_encar(external_id: str) -> dict:
    vehicle, record, inspection = await _fetch_all(external_id)
    _log_record_gap(external_id, vehicle, record)
    car_data = _build_car_data(vehicle, record, inspection)
    score = calculate_score(car_data)
    score["accident_history"] = car_data.get("accidentHistory") or []
    score["owner_change_count"] = car_data.get("ownerChangeCount")
    return score


def _score_partial(car) -> dict:
    """보험이력/성능점검 API 없이 크롤 데이터만으로 부분 채점"""
    car_data = _build_partial_car_data(car)
    score = calculate_score(car_data)
    score["accident_history"] = []
    score["owner_change_count"] = None
    return score


def _build_partial_car_data(car) -> dict:
    """비엔카 플랫폼용 car_data 빌드 — 없는 항목은 중립 기본값으로"""
    raw = car.raw_data or {}
    return {
        "year":               _year_2digit(car.year),
        "month":              _extract_month(raw, car.platform),
        "mileage":            car.mileage or 0,
        "price":              car.price or 0,
        "originPrice":        0,
        "totalOriginPrice":   0,
        "hasDiagnosis":       False,
        # 보험이력 미제공 — "private(비공개)"와 달리 페널티 없음
        "insuranceStatus":    "unknown",
        "isInsurancePrivate": False,
        "hasRecordData":      False,
        "insuranceFetchStatus": "not_applicable",
        # 성능점검 없음 (케이카 자체 점검 ≠ 표준 성능점검서)
        "isInspectionPrivate": False,
        "hasInspection":      False,
        # 렌트/소유주: 정보 없으면 낙관적 기본값
        "hasRentalHistory":   False,
        "hasUsageChange":     False,
        "ownerChangeCount":   0,
    }


def _year_2digit(year: int | None) -> int:
    if not year:
        return 0
    return year - 2000 if year > 2000 else year


def _extract_month(raw: dict, platform: str) -> int:
    """플랫폼별 제조월 파싱 — kcar: mfgDt "YYYYMM" 형식"""
    if platform == "kcar":
        mfg = str(raw.get("mfgDt", "") or "")
        return int(mfg[4:6]) if len(mfg) >= 6 else 0
    return 0


async def _fetch_all(external_id: str) -> tuple[dict, dict | None, dict | None]:
    vehicle = await _get("vehicle", f"{API_BASE}/v1/readside/vehicle/{external_id}") or {}
    record_id = _resolve_record_id(vehicle, external_id)

    requests = [
        ("record_open", f"{API_BASE}/v1/readside/record/vehicle/{record_id}/open"),
        ("inspection", f"{API_BASE}/v1/readside/inspection/vehicle/{record_id}"),
    ]
    record, inspection = await asyncio.gather(*[_get(label, url) for label, url in requests])
    return vehicle, record, inspection


def _resolve_record_id(vehicle: dict, external_id: str) -> str:
    """재등록(dummy) 매물은 vehicle 응답의 vehicleId가 현재 활성 매물의 ID를 가리킨다.
    record/inspection은 그 ID로 재호출해야 200을 받는다."""
    vehicle_id = vehicle.get("vehicleId")
    if vehicle_id and str(vehicle_id) != str(external_id):
        return str(vehicle_id)
    return external_id


async def _get(label: str, url: str) -> dict | None:
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as c:
        try:
            r = await c.get(url)
            if r.status_code == 200:
                return r.json()
            _log_fetch_failure(label, url, r)
            return None
        except Exception as exc:
            logger.warning("[encar:%s] request failed url=%s error=%r", label, url, exc)
            return None


def _log_fetch_failure(label: str, url: str, response: httpx.Response):
    logger.warning(
        "[encar:%s] non-200 status=%s url=%s headers=%s body=%s",
        label,
        response.status_code,
        url,
        dict(response.headers),
        _preview(response.text),
    )


def _preview(text: str, limit: int = 300) -> str:
    compact = " ".join((text or "").split())
    return compact[:limit]


def _log_record_gap(external_id: str, vehicle: dict, record: dict | None):
    condition = (vehicle.get("condition") or {}).get("accident") or {}
    is_viewable = bool(condition.get("recordView") and condition.get("resumeView"))
    if record is not None or not is_viewable:
        return
    logger.warning(
        "[encar:record] viewable but missing external_id=%s vehicle_no=%s condition=%s",
        external_id,
        vehicle.get("vehicleNo"),
        condition,
    )


def _build_car_data(vehicle: dict, record: dict | None, inspection: dict | None) -> dict:
    v = _parse_vehicle(vehicle)
    record_viewable = v.pop("recordViewable")
    is_reregistered = v.pop("isReregisteredListing")
    r = _parse_record(record, record_viewable, is_reregistered)
    i = _parse_inspection(inspection)
    return {**v, **r, **i}


def _parse_vehicle(data: dict) -> dict:
    cat    = data.get("category", {})
    adv    = data.get("advertisement", {})
    spec   = data.get("spec", {})
    manage = data.get("manage", {})
    accident = data.get("condition", {}).get("accident", {})

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
        "recordViewable":  bool(accident.get("recordView") and accident.get("resumeView")),
        # 매물이 재등록되며 새 vehicleId로 옮겨가면 이전 ID는 vehicle 정보만 남고
        # record/inspection은 더 이상 서빙되지 않는다 (manage.dummy && manage.reRegistered).
        "isReregisteredListing": bool(manage.get("dummy") and manage.get("reRegistered")),
    }


def _parse_accidents(accidents: list[dict]) -> tuple[list[int], list[dict]]:
    """보험 처리금액 목록(채점용)과 화면 표시용 사고별 상세 내역을 함께 만든다."""
    amounts: list[int] = []
    history: list[dict] = []
    for acc in accidents:
        benefit = _to_int(acc.get("insuranceBenefit", 0))
        if benefit > 0:
            amounts.append(benefit)
        history.append({
            "date":              acc.get("date"),
            "insurance_benefit": benefit,
            "part_cost":         _to_int(acc.get("partCost", 0)),
            "labor_cost":        _to_int(acc.get("laborCost", 0)),
            "painting_cost":     _to_int(acc.get("paintingCost", 0)),
        })
    return amounts, history


def _parse_record(data: dict | None, record_viewable: bool, is_reregistered_listing: bool = False) -> dict:
    # record API 404 (data is None)는 "비공개"가 아니라 "정보 없음" — 활성 매물의
    # 약 1/3이 recordView/resumeView=True(열람 가능)인데도 404를 반환한다.
    # -40 페널티 대신 no_insurance(40% 추정 + 89점 캡)로 처리하되, 셋 중 하나로 구분한다:
    # - reregistered_listing: 재등록된 더미 매물이라 이 ID로는 원본에서도 조회 불가능할 가능성
    # - viewable_unfetched: 엔카에서는 조회 가능(recordView/resumeView=true)인데 우리만 못 가져옴
    # - unavailable: 엔카에서도 조회 불가
    if data is None:
        if is_reregistered_listing:
            status = "reregistered_listing"
        elif record_viewable:
            status = "viewable_unfetched"
        else:
            status = "unavailable"
        return {
            "insuranceStatus": "unknown",
            "isInsurancePrivate": False,
            "hasRecordData": False,
            "insuranceFetchStatus": status,
        }

    if data.get("openData") is False:
        return {
            "insuranceStatus": "private",
            "isInsurancePrivate": True,
            "hasRecordData": False,
            "insuranceFetchStatus": "private",
        }

    my_cnt   = _to_int(data.get("myAccidentCnt", 0))
    my_cost  = _to_int(data.get("myAccidentCost", 0))
    amounts, history = _parse_accidents(data.get("accidents", []))

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
        "insuranceFetchStatus": "available",
        "accidentAmounts":    amounts,
        "accidentHistory":    history,
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
        "insurance_fetch_status": "not_applicable",
        "accident_history": [],
        "owner_change_count": None,
    }
