# Cardash 방향성 메모

작성일: 2026-06-10

## 1. 프로젝트 정의

Cardash는 엔카, 케이카, KB차차차, 보배드림의 중고차 매물을 한곳에 모으고, 가격/사고/보험/성능점검/주행거리/소유이력 기준으로 사용자가 비교 판단할 수 있게 만드는 중고차 의사결정 대시보드다.

핵심은 "매물을 많이 보여주는 서비스"가 아니라 "살 만한 매물인지 빠르게 판단하게 해주는 서비스"다. 따라서 단순 목록보다 신뢰도, 가격 적정성, 위험 신호, 비교 가능성이 제품의 중심이 되어야 한다.

## 2. 현재 코드 파악

### 백엔드

- FastAPI 앱은 `backend/main.py`에서 시작하고, `/cars`, `/admin`, `/health` 라우터가 연결되어 있다.
- DB는 SQLAlchemy async 기반이며 `cars`, `scores`, `price_history`, `vehicle_categories` 모델이 있다.
- `cars`는 `platform + external_id` 유니크 제약으로 중복 수집을 막고, 원본 응답은 `raw_data`에 보존한다.
- 크롤러는 `BaseCrawler`를 중심으로 엔카, 케이카, KB차차차, 보배드림으로 나뉘어 있다.
- 엔카는 목록/상세/카테고리 API 흐름이 가장 구체적이다.
- 케이카, KB차차차, 보배드림은 목록 수집은 있으나 상세 수집과 사고/성능/소유자 기반 채점은 아직 제한적이다.
- `backend/scoring/`은 사고, 주행거리, 가격, 성능점검, 렌트, 소유자, 등급 모듈로 분리되어 있고 `calculator.py`가 오케스트레이션한다.
- `backend/scheduler.py`와 `backend/services/scorer.py`는 미채점 차량을 10분마다 25개씩 백그라운드 채점한다.
- 최근 작업 흐름에는 `owner_change_count`, `accident_free` 기반 필터와 사고이력/소유주변경 신뢰 라벨이 포함되어 있다.
- 설정값 `CRAWL_INTERVAL_HOURS`를 쓰는 실제 크롤링 스케줄은 아직 없고, 현재 스케줄러의 역할은 크롤링이 아니라 채점 보강이다.
- 케이카 크롤러는 이번 작업 흐름에서 재작성/개선 중이며, 수집량이 768대에서 880대 수준으로 늘어난 상태다. 플랫폼 확장은 로드맵상 후순위 항목이지만 실제 작업 순서는 필요에 따라 앞당겨질 수 있다.

### 프론트엔드

- React + Vite + TypeScript 구조이며 `frontend/src/main.tsx`에서 목록과 상세 라우트를 구성한다.
- 목록 페이지는 `frontend/src/pages/ListPage/` 아래에 `index.tsx`, `FilterPanel.tsx`, `CarCard.tsx`, `useCarList.ts`, `useCarCategories.ts`로 나뉘어 있다.
- 상세 페이지는 `frontend/src/pages/DetailPage/` 아래에서 갤러리, 기본 정보, 점수 패널, 사고 이력을 보여준다.
- URL query string을 목록 필터 상태의 원본으로 사용하는 점은 좋다.
- 현재 첫 방문 기본 필터는 개인 테스트용 임시 기본값으로 제네시스 G70에 맞춰져 있다. 완전 제거보다 "추천: G70 매물" 같은 칩/탭으로 분리하는 방향이 자연스럽다.
- 플랫폼을 바꿔도 필터 옵션 조회가 기본 `encar`에 머무를 수 있다.
- `/cars` 응답에 `total`이 없어 다음 페이지 여부를 `items.length >= size`로 추정한다.
- 클릭 가능한 카드가 `div`라 접근성과 키보드 조작이 약하다.

## 3. 우선 리스크

### P0: 데이터 계약 안정화

- `backend/schemas/`가 비어 있고 라우터가 `response_model` 없이 ORM/딕셔너리를 직접 반환한다.
- `Car.images`는 모델 타입이 `dict`지만 실제 크롤러와 프론트는 `list[str]`로 사용한다.
- `Score.accident_history`도 모델 타입은 `dict`지만 실제로는 사고 이력 배열을 저장한다.
- `Score.owner_change_count`와 `ScoreSummary.owner_change_count`는 `int | null` 계약으로 고정해야 한다.
- `ScoreSummary.accident_free`는 `boolean | null` 계약으로 두되, `no_insurance_data == true`인 차량은 "무사고 확인"이 아니라 `null`인 "확인불가"로 표시해야 한다.
- 먼저 Pydantic 스키마를 만들고, 백엔드 모델/응답/프론트 타입을 하나의 계약으로 맞춰야 한다.

### P2: 마이그레이션 체계

- `alembic` 의존성은 있지만 `alembic.ini`, migration env, versions가 없다.
- 현재는 앱 시작 시 `Base.metadata.create_all()`에 의존한다.
- 다만 지금은 `owner_change_count`, `vehicle_categories`처럼 모델이 계속 바뀌는 빠른 탐색 단계다.
- 이 시점에 Alembic을 P0로 두면 매번 migration 파일 작성 비용이 커질 수 있다.
- 당장은 `create_all()` 기반 빠른 이터레이션을 유지하고, 스키마가 어느 정도 안정되는 2~3단계 이후 Alembic으로 전환한다.

### P1: 채점 신뢰도

- AGENTS.md 요구사항에는 보험이력 미제공 시 최대 A등급 제한이 있지만, 현재 계산기는 사고점수 추정 후 `get_grade(total)`을 그대로 호출한다.
- 성능점검에서 렌트 이력 추정값을 만들지만 최종 `hasRentalHistory`에 반영되지 않는 흐름이 있다.
- 엔카 외 플랫폼은 상세 이력 데이터가 부족해 점수 신뢰도가 낮다.
- 메인 화면에 점수를 노출하려면 점수 옆에 "데이터 충분", "보험이력 미확인", "목록 기반 부분점수" 같은 신뢰도 라벨이 필요하다.
- 특히 보험이력 미제공 시 최대 A등급 제한은 점수 정확성에 직접 영향을 주는 버그성 이슈다. 스키마 작업과 별개로 `calculator.py`에서 빠르게 고치는 것이 좋다.
- A등급 제한은 `no_insurance == true`인 경우에만 적용한다. `isInsurancePrivate` 또는 `isInspectionPrivate`로 -40점 페널티를 받는 비공개 케이스와 섞지 않는다.
- 구현은 `total = max(0, min(100, total))` 이후 `total = min(total, NO_INSURANCE_MAX_TOTAL)` 순서가 적합하다.
- `NO_INSURANCE_MAX_TOTAL = 89`는 `grade.py`의 A+ 임계값 90 미만을 의미하는 상수로 둔다.

### P1: 테스트 부재

- 현재 백엔드 테스트 파일과 `pytest` 의존성이 없다.
- 최소 테스트는 `scoring` 순수 함수, 엔카 카테고리 파서, 크롤러 normalize 샘플, `/cars` 라우터 smoke test부터 시작하는 것이 효율적이다.

### P2: 크롤링 운영성

- 크롤링과 채점 스케줄을 분리해야 한다.
- 플랫폼별 실패가 전체 배치를 막지 않도록 실패 기록, 재시도, 마지막 성공 시각, 수집량 통계를 저장해야 한다.
- robots.txt와 요청 간격 정책은 계속 지켜야 한다.

## 4. 중고차 사용자가 우선적으로 보는 항목

조사 자료와 주요 서비스 UX를 종합하면 사용자는 다음 순서로 판단한다.

1. 가격: 예산 안에 들어오는지, 동급 매물 대비 싼지 비싼지, 최근 가격이 내려갔는지.
2. 사고/보험 이력: 무사고 여부, 단순교환인지 골격 사고인지, 보험처리 금액이 큰지.
3. 주행거리와 연식: 같은 가격이면 연식과 주행거리의 균형을 본다.
4. 성능점검/정비 상태: 누유, 침수, 교환/판금/용접, 주요 골격 손상 여부.
5. 소유자/용도 이력: 렌트, 영업용, 소유자 변경 횟수.
6. 판매 신뢰: 플랫폼, 딜러/개인, 보증/환불/홈서비스 가능 여부.
7. 지역/실매물 확인: 방문 가능 거리, 허위·미끼 매물 가능성.
8. 옵션/색상/트림: 가격과 상태가 납득된 뒤 비교하는 보조 조건.

한국소비자원 조사에서는 중고차 구입 시 중요 고려 항목이 구매가격, 사고이력, 주행거리 순으로 높게 나타났다. 또한 성능·상태점검기록부 용어를 소비자가 충분히 이해하지 못하는 문제가 반복적으로 지적된다. 즉 Cardash는 원문 기록을 그대로 보여주는 것보다 "이 기록이 좋은지/나쁜지/모호한지"를 번역해주는 역할을 해야 한다.

## 5. 메인 화면에 우선 띄울 것

### 카드에서 바로 보여줄 정보

카드 한 장에서 사용자가 3초 안에 판단해야 하는 정보는 다음이다.

- 차량 사진
- 브랜드/모델/트림
- 가격
- 연식
- 주행거리
- 지역
- 플랫폼
- Cardash 점수와 등급
- 가격 적정성 라벨: 저렴, 적정, 비쌈, 판단불가
- 사고/보험 라벨: 무사고 확인, 사고 이력 있음, 보험이력 미확인
- 성능점검 라벨: 점검 확인, 주요 손상 있음, 점검 미확인
- 소유/용도 라벨: 1인 소유 추정, 소유자 변경 n회, 렌트/영업 이력
- 최근 가격 변동: 하락, 상승, 변동 없음

카드에서 모든 세부 수치를 다 보여주기보다, 신뢰 판단에 필요한 라벨을 짧게 보여주고 상세에서 근거를 풀어야 한다.

### 목록 상단에 둘 영역

첫 화면은 특정 모델 하드코딩보다 "사용자가 바로 고를 수 있는 탐색 허브"가 낫다.

- 빠른 검색: 제조사, 모델, 예산, 주행거리
- 추천 탭:
  - 가성비 좋은 매물
  - 사고/보험 확인 매물
  - 가격 하락 매물
  - 낮은 주행거리
  - 최근 등록 매물
  - 데이터 신뢰도 높은 매물
- 현재 필터 요약: 예산, 연식, 주행거리, 지역, 플랫폼
- 수집 현황: 플랫폼별 매물 수, 마지막 갱신 시각

추천 탭은 초보 사용자의 진입 장벽을 낮춘다. 필터를 처음부터 다 조작하게 하는 것보다 "가성비", "안심", "가격하락" 같은 목적 기반 진입이 더 적합하다.

### 상세 화면에서 강화할 정보

- 총점뿐 아니라 항목별 근거를 보여준다.
- 보험이력/성능점검 미확인일 때 점수의 한계를 명확히 표시한다.
- 사고 이력은 금액, 횟수, 부위, 골격 여부를 분리해 보여준다.
- 가격은 동급 매물 중앙값, 감가 기준, 최근 가격 추이를 함께 보여준다.
- "사도 되는 이유"와 "확인해야 할 위험"을 분리한다.

## 6. 제품 방향성

### 포지셔닝

Cardash는 중고차 초보자가 여러 플랫폼을 오가며 놓치기 쉬운 정보를 압축해주는 비교 도구다. 경쟁 서비스처럼 자체 매매/금융/보증을 전면에 세우기보다, 데이터 기반 선별과 위험 설명에 집중한다.

### 핵심 가치

- 한곳에서 비교: 플랫폼별 매물을 같은 기준으로 정렬한다.
- 위험 신호 번역: 보험/성능/소유/렌트 이력을 쉬운 라벨로 바꾼다.
- 가격 판단: 절대 가격보다 동급 대비 적정성을 보여준다.
- 근거 있는 점수: 총점만 보여주지 않고 어떤 데이터로 계산됐는지 공개한다.
- 신뢰도 표시: 모르는 것을 아는 척하지 않는다.

### 피해야 할 방향

- 점수만 크게 보여주고 근거가 부족한 UI
- 엔카 데이터 품질을 다른 플랫폼에도 동일하게 적용하는 것
- "무사고"를 단일 boolean으로만 취급하는 것
- 성능점검기록부 원문을 사용자가 직접 해석하게 방치하는 것
- 크롤링 수량 확대를 품질 안정화보다 먼저 하는 것

## 7. 개발 로드맵 제안

### 1a: 즉시 버그픽스

- 보험이력 미제공 시 최대 A등급 제한 반영
- `NO_INSURANCE_MAX_TOTAL = 89` 상수 추가
- `no_insurance == true` 케이스에만 캡 적용
- `isInsurancePrivate`/`isInspectionPrivate` 비공개 페널티 케이스에는 A캡 미적용
- 최소 테스트:
  - `no_insurance == true`, 원점수 90 이상이면 `total == 89`, `grade == "A"`
  - `no_insurance == true`, 원점수 80 미만이면 캡 영향 없음
  - `isInsurancePrivate == true`이면 기존 -40 페널티만 적용 (이 경우 `no_insurance`는 항상 `false`)
  - `no_insurance == true` AND `isInspectionPrivate == true` (보험이력 미제공 + 성능점검 비공개 동시 발생)이면 -40 페널티와 89 캡이 함께 적용되어 `total <= 89`, `grade`는 `"A"` 이하

### 1b: API 계약 정리

- Pydantic schema 추가
- 모델/스키마/프론트 타입 계약 정리
- `Car.images: list[str] | null` 계약 확정
- `Score.accident_history: list[AccidentRecord] | null` 계약 확정
- `Score.owner_change_count: int | null` 계약 확정
- `ScoreSummary.owner_change_count: int | null` 계약 확정
- `ScoreSummary.accident_free: boolean | null` 계약 확정
- `no_insurance_data == true`인 차량은 `accident_free == null`로 표시

### 1c: 목록 API 품질

- `/cars`에 `total`, `has_next`, 정렬 옵션 추가
- 관리자 API 보호 방식 추가
- scoring 핵심 테스트 추가

### 2단계: 목록 UX 개선

- 기본 G70 고정 검색을 "추천: G70 매물" 같은 명시적 추천 시작점으로 분리
- 플랫폼 변경 시 필터 옵션 재조회
- 서버의 `years`, `regions`를 실제 필터 옵션에 반영
- 카드에 가격 적정성, 사고/보험, 성능점검, 점수 신뢰도 라벨 추가
- 목적 기반 추천 탭 추가
- 카드/썸네일을 button/link semantic으로 변경

### 3단계: 채점 품질 강화

- 성능점검 기반 렌트/용도 이력 반영
- 가격 점수에 동급 매물 중앙값/분위수 반영
- 점수 신뢰도 필드 추가: `full`, `partial`, `insufficient`
- non-Encar 플랫폼의 부분점수 정책 문서화

### 백로그: 수집 확장

- 플랫폼별 상세 수집 전략 정리
- 크롤링 스케줄과 채점 스케줄 분리
- 수집 실패/성공 통계 저장
- 플랫폼별 마지막 갱신 시각 API 추가
- 가격 이력 기반 가격하락 알림 준비

### 백로그: 신뢰 기능

- 실매물/허위매물 위험 라벨
- 보험/성능 원문 비교
- 카히스토리/자동차365 확인 가이드 링크
- 정비/소모품 체크리스트
- 사용자가 관심 매물을 저장하고 가격 변동을 추적하는 기능

## 8. 문서와 코드의 불일치

- AGENTS.md는 React 18을 말하지만 실제 `frontend/package.json`은 React 19 계열이다.
- AGENTS.md는 Alembic 사용을 전제로 하지만 실제 migration 파일은 없다.
- AGENTS.md는 `schemas/`를 전제로 하지만 실제 폴더는 비어 있다.
- 최근 `Score.owner_change_count`가 추가되었으므로, schema 작업 시 `images`, `accident_history`와 함께 응답 타입을 고정해야 한다.
- README와 docker-compose의 포트 설명이 일부 다르다. 실제 compose는 frontend 3001, Vite config는 로컬 dev 5173이다.
- AGENTS.md의 함수 30줄 규칙 기준으로 일부 프론트 컴포넌트와 백엔드 라우터 함수는 분리 대상이다.

## 9. 참고 자료

- 한국소비자원 중고차 거래 실태조사: 구매가격, 사고이력, 주행거리의 중요도와 성능점검기록부 이해도 이슈를 확인했다.  
  https://www.kca.go.kr/smartconsumer/board/download.do?bid=00000146&did=1003306249&fno=10033823&menukey=7301
- Kelley Blue Book, Vehicle History Report: 사고, 정비, 주행거리 정확성, 타이틀 상태를 확인하되 정비사 점검을 대체하지 못한다는 관점이 유용하다.  
  https://www.kbb.com/car-advice/vehicle-history-report/
- Edmunds, 10 Steps to Buying a Used Car: 예산, 목표 차량, 가격 확인, 이력 보고서, 시승, 점검, 협상 흐름을 확인했다.  
  https://www.edmunds.com/car-buying/10-steps-to-buying-a-used-car.html
- CarGurus Best Used Car Websites: 가격 기준으로 매물을 등급화해 좋은 거래/비싼 거래를 빠르게 판단하게 하는 UX 참고.  
  https://www.cargurus.com/research/articles/best-used-car-websites
- 엔카 앱 설명: 시세, 진단, 보증, 환불, 홈서비스가 사용자 신뢰 요소로 제시된다.  
  https://apps.apple.com/kr/app/id404512755
- KB차차차 앱 설명: AI 시세, 홈배송, 인증중고차, 보증, 실매물 확인성의 방향을 확인했다.  
  https://play.google.com/store/apps/details?id=kr.co.kbc.cha.android&hl=ko
- K Car 웹사이트: 직영, 환불, 보증, 테마 기획전, 온라인 구매 흐름이 주요 신뢰 장치로 제시된다.  
  https://www.kcar.com/
