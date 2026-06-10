"""routers/cars.py의 순수 헬퍼 함수(_score_summary, _resolve_sort) 단위 테스트.

DB 세션 없이 동작을 검증할 수 있는 함수만 대상으로 한다.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from models import Score
from routers.cars import GRADE_ORDER, SORT_OPTIONS, _apply_grade_filter, _resolve_sort, _score_summary


def _make_score(no_insurance_data=False, accident_history=None, grade="B", owner_change_count=1):
    return Score(
        no_insurance_data=no_insurance_data,
        accident_history=accident_history,
        grade=grade,
        owner_change_count=owner_change_count,
    )


def test_score_summary_returns_none_when_no_insurance_data_unknown():
    score = _make_score(no_insurance_data=True, accident_history=None)

    summary = _score_summary(score)

    assert summary["accident_free"] is None
    assert summary["grade"] == "B"


def test_score_summary_accident_free_true_when_history_empty():
    score = _make_score(no_insurance_data=False, accident_history=[])

    summary = _score_summary(score)

    assert summary["accident_free"] is True


def test_score_summary_accident_free_false_when_history_present():
    score = _make_score(no_insurance_data=False, accident_history=[{"date": "2020-01"}])

    summary = _score_summary(score)

    assert summary["accident_free"] is False


def test_score_summary_returns_none_when_score_missing():
    assert _score_summary(None) is None


def test_resolve_sort_returns_known_option():
    for sort_key in SORT_OPTIONS:
        assert _resolve_sort(sort_key) is SORT_OPTIONS[sort_key]


def test_resolve_sort_raises_422_for_unknown_value():
    with pytest.raises(HTTPException) as exc_info:
        _resolve_sort("not_a_real_sort")

    assert exc_info.value.status_code == 422


def test_apply_grade_filter_allows_grade_and_better():
    stmt = _apply_grade_filter(select(Score), "B")

    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))

    for grade in GRADE_ORDER[:GRADE_ORDER.index("B") + 1]:
        assert f"'{grade}'" in compiled
    for grade in GRADE_ORDER[GRADE_ORDER.index("B") + 1:]:
        assert f"'{grade}'" not in compiled


def test_apply_grade_filter_noop_when_not_set():
    stmt = select(Score)

    assert _apply_grade_filter(stmt, None) is stmt


def test_apply_grade_filter_noop_for_unknown_grade():
    stmt = select(Score)

    assert _apply_grade_filter(stmt, "Z") is stmt
