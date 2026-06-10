"""calculate_score()의 '보험이력 미제공 → 최대 A등급(89점) 제한' 로직 테스트.

하위 채점 함수(score_mileage, score_price 등)는 mock으로 대체하여
calculator.py의 집계/캡/페널티 로직만 격리 테스트한다.
"""

from unittest.mock import patch

from scoring.calculator import NO_INSURANCE_MAX_TOTAL, calculate_score

# accident를 제외한 5개 항목(가중치 합 75)의 mock 반환값.
# HIGH: 5*30=150 -> 원점수 160 (90 이상). LOW: 5*5=25 -> 원점수 35 (80 미만).
HIGH_SUB_SCORE = 30
LOW_SUB_SCORE = 5


def _no_insurance_car():
    return {"hasRecordData": False, "insuranceStatus": "public"}


def _patch_sub_scores(value):
    return patch.multiple(
        "scoring.calculator",
        score_mileage=lambda *a, **k: value,
        score_price=lambda *a, **k: value,
        score_inspection=lambda *a, **k: value,
        score_rental=lambda *a, **k: value,
        score_owner=lambda *a, **k: value,
    )


def test_no_insurance_with_high_raw_score_is_capped_at_89():
    car = _no_insurance_car()

    with _patch_sub_scores(HIGH_SUB_SCORE):
        result = calculate_score(car)

    # 원점수 = accident 추정치(25*0.4=10) + 150 = 160 -> clamp 100 -> 캡 89
    assert result["total"] == NO_INSURANCE_MAX_TOTAL
    assert result["total"] == 89
    assert result["grade"] == "A"
    assert result["no_insurance_data"] is True


def test_insurance_fetch_status_is_passed_through_from_car_data():
    car = {**_no_insurance_car(), "insuranceFetchStatus": "viewable_unfetched"}

    with _patch_sub_scores(HIGH_SUB_SCORE):
        result = calculate_score(car)

    assert result["insurance_fetch_status"] == "viewable_unfetched"


def test_insurance_fetch_status_defaults_to_not_applicable():
    car = _no_insurance_car()

    with _patch_sub_scores(HIGH_SUB_SCORE):
        result = calculate_score(car)

    assert result["insurance_fetch_status"] == "not_applicable"


def test_no_insurance_with_low_raw_score_is_unaffected_by_cap():
    car = _no_insurance_car()

    with _patch_sub_scores(LOW_SUB_SCORE):
        result = calculate_score(car)

    # accident 추정치(25 * 0.4 = 10) + (5*5) = 35, 80 미만이라 캡 영향 없음
    assert result["total"] == 35
    assert result["total"] < NO_INSURANCE_MAX_TOTAL
    assert result["grade"] == "F"


def test_insurance_private_penalty_only_no_cap():
    # insuranceStatus == "private" → no_insurance은 자동으로 False
    car = {"hasRecordData": False, "insuranceStatus": "private", "isInsurancePrivate": True}

    with patch.multiple(
        "scoring.calculator",
        score_accident=lambda *a, **k: 25,
        score_mileage=lambda *a, **k: 30,
        score_price=lambda *a, **k: 30,
        score_inspection=lambda *a, **k: 30,
        score_rental=lambda *a, **k: 30,
        score_owner=lambda *a, **k: 30,
    ):
        result = calculate_score(car)

    # 원점수 175 -> -40 페널티 -> 135 -> min(100,135)=100, 89 캡은 적용 안 됨
    assert result["total"] == 100
    assert result["penalty"] == 40
    assert result["no_insurance_data"] is False
    assert result["grade"] == "S"


def test_no_insurance_and_inspection_private_combines_penalty_and_cap():
    car = {
        "hasRecordData": False,
        "insuranceStatus": "public",
        "isInspectionPrivate": True,
    }

    with _patch_sub_scores(HIGH_SUB_SCORE):
        result = calculate_score(car)

    # 원점수 160 -> -40 페널티 -> 120 -> min(100,120)=100 -> no_insurance 캡(89) 적용 -> 89
    assert result["total"] == NO_INSURANCE_MAX_TOTAL
    assert result["total"] <= NO_INSURANCE_MAX_TOTAL
    assert result["penalty"] == 40
    assert result["no_insurance_data"] is True
    assert result["grade"] == "A"
