"""scoring/mileage.py의 score_mileage() 입력→출력 케이스 테스트."""

from scoring.mileage import score_mileage

MAX_POINTS = 15


def test_score_mileage_returns_default_when_year_or_mileage_missing():
    result = score_mileage({"mileage": 0, "year": 0}, MAX_POINTS)

    assert result == round(MAX_POINTS * 0.6 * 10) / 10


def test_score_mileage_no_deduction_when_within_expected_range():
    # 22년식, 2025년 기준 약 3년 -> 예상 주행거리 45,000km 근처
    # mileage가 expected_mileage의 1.0배 -> ratio<=1.15 -> deduction 0
    result = score_mileage({"mileage": 45000, "year": 22, "month": 1}, MAX_POINTS)

    assert result == MAX_POINTS


def test_score_mileage_deducts_for_excessive_mileage():
    result = score_mileage({"mileage": 300000, "year": 22, "month": 1}, MAX_POINTS)

    assert result < MAX_POINTS
    assert result >= 0
