"""_parse_record() / _parse_vehicle()의 보험이력 조회 가능 여부 분기 테스트.

404(data is None)는 "비공개"가 아닌 "정보 없음"으로 처리하되, 다음 세 가지로 구분한다:
- reregistered_listing: 재등록된 더미 매물(manage.dummy && manage.reRegistered)이라
  이 vehicleId로는 원본에서도 조회 불가능할 가능성이 높음
- viewable_unfetched: 엔카에서 조회 가능(recordView/resumeView=true)인데 우리만 못 가져옴
- unavailable: 엔카에서도 조회 불가(recordView/resumeView=false)
openData:false(명시적 비공개)만 -40 페널티 대상으로 분류되어야 한다.
"""

from services.analyzer import _parse_record, _parse_vehicle


def test_record_404_with_viewable_record_is_viewable_unfetched():
    result = _parse_record(None, record_viewable=True)

    assert result["insuranceStatus"] == "unknown"
    assert result["isInsurancePrivate"] is False
    assert result["hasRecordData"] is False
    assert result["insuranceFetchStatus"] == "viewable_unfetched"


def test_record_404_without_viewable_record_is_unavailable():
    result = _parse_record(None, record_viewable=False)

    assert result["insuranceStatus"] == "unknown"
    assert result["isInsurancePrivate"] is False
    assert result["hasRecordData"] is False
    assert result["insuranceFetchStatus"] == "unavailable"


def test_record_404_on_reregistered_listing_is_reregistered_listing():
    # dummy/재등록 매물은 recordView/resumeView=true(과거에 박제된 값)여도
    # viewable_unfetched가 아니라 reregistered_listing으로 구분한다.
    result = _parse_record(None, record_viewable=True, is_reregistered_listing=True)

    assert result["insuranceStatus"] == "unknown"
    assert result["isInsurancePrivate"] is False
    assert result["hasRecordData"] is False
    assert result["insuranceFetchStatus"] == "reregistered_listing"


def test_record_open_data_false_is_treated_as_private():
    result = _parse_record({"openData": False}, record_viewable=True)

    assert result["insuranceStatus"] == "private"
    assert result["isInsurancePrivate"] is True
    assert result["hasRecordData"] is False
    assert result["insuranceFetchStatus"] == "private"


def test_record_available_data_is_parsed():
    result = _parse_record({"openData": True, "myAccidentCnt": 0, "accidents": []}, record_viewable=True)

    assert result["insuranceStatus"] == "available"
    assert result["isInsurancePrivate"] is False
    assert result["hasRecordData"] is True
    assert result["insuranceFetchStatus"] == "available"


def test_parse_vehicle_record_viewable_requires_both_flags():
    both_true = _parse_vehicle({"condition": {"accident": {"recordView": True, "resumeView": True}}})
    assert both_true["recordViewable"] is True

    one_false = _parse_vehicle({"condition": {"accident": {"recordView": True, "resumeView": False}}})
    assert one_false["recordViewable"] is False

    missing = _parse_vehicle({})
    assert missing["recordViewable"] is False


def test_parse_vehicle_reregistered_listing_requires_dummy_and_reregistered():
    both = _parse_vehicle({"manage": {"dummy": True, "reRegistered": True}})
    assert both["isReregisteredListing"] is True

    dummy_only = _parse_vehicle({"manage": {"dummy": True, "reRegistered": False}})
    assert dummy_only["isReregisteredListing"] is False

    missing = _parse_vehicle({})
    assert missing["isReregisteredListing"] is False
