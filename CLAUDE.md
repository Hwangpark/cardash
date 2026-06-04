# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 프로젝트 개요

**중고차 통합 대시보드** — 국내 주요 중고차 플랫폼(엔카, 케이카, KB차차차, 보배드림)의 매물을 주기적으로 수집·채점하여 하나의 웹 인터페이스에서 비교 조회할 수 있는 풀스택 서비스.

---

## 모노레포 구조

```
cardash/
├── docker-compose.yml          # 전체 서비스 오케스트레이션
├── .env                        # 공통 환경변수 (DB 접속 정보 등)
├── backend/                    # FastAPI (Python)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # 앱 진입점, 라우터 등록
│   ├── config.py               # 환경변수 파싱 (pydantic Settings)
│   ├── database.py             # SQLAlchemy 엔진·세션
│   ├── models/                 # SQLAlchemy ORM 모델
│   │   ├── car.py
│   │   ├── score.py
│   │   └── price_history.py
│   ├── schemas/                # Pydantic 요청/응답 스키마
│   ├── routers/
│   │   ├── cars.py             # GET /cars, GET /cars/{id}
│   │   └── admin.py            # POST /admin/crawl (수동 트리거)
│   ├── crawlers/               # 플랫폼별 수집기
│   │   ├── base.py             # 공통 인터페이스 (BaseCrawler ABC)
│   │   ├── encar.py            # api.encar.com JSON API 직접 호출
│   │   ├── kcar.py             # Playwright (CSR)
│   │   ├── kbchachacha.py      # Playwright (CSR)
│   │   └── bobaedream.py       # BeautifulSoup (SSR)
│   ├── scoring/                # C:\Project\car 의 JS 채점 로직 Python 포팅
│   │   ├── accident.py
│   │   ├── mileage.py
│   │   ├── price.py
│   │   ├── inspection.py
│   │   ├── rental.py
│   │   ├── owner.py
│   │   ├── grade.py
│   │   └── calculator.py       # calculateScore() 오케스트레이터
│   └── scheduler.py            # APScheduler 크론 작업 정의
└── frontend/                   # React + Vite + TypeScript
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── main.tsx
        ├── api/                # TanStack Query 훅 + axios 클라이언트
        ├── pages/
        │   ├── ListPage.tsx    # 매물 목록, 필터, 정렬
        │   └── DetailPage.tsx  # 상세 정보 + 점수 분석 패널
        └── components/
            ├── ScoreBadge.tsx  # S/A+/A/B/C/D/F 등급 배지
            ├── ScoreBreakdown.tsx
            ├── CarCard.tsx
            └── FilterPanel.tsx
```

---

## 기술 스택

| 레이어 | 기술 | 버전 목표 |
|--------|------|----------|
| 프론트엔드 | React + Vite + TypeScript | React 18 |
| 상태/데이터 | TanStack Query v5 | - |
| 백엔드 | FastAPI | 0.115+ |
| ORM | SQLAlchemy 2.0 + Alembic | async 모드 |
| DB | PostgreSQL 16 | Docker |
| 크롤러 | Playwright (async) + BeautifulSoup4 | - |
| 스케줄러 | APScheduler 3.x | AsyncScheduler |
| 캐시 | Redis 7 | Docker |
| 컨테이너 | Docker Compose v2 | - |

---

## Docker Compose 서비스 구성

```yaml
services:
  postgres:   # 포트 5432
  redis:      # 포트 6379
  backend:    # 포트 8000, postgres/redis 의존
  frontend:   # 포트 3000, backend 의존
```

개발 시 `docker-compose up -d postgres redis` 로 인프라만 올리고 backend/frontend는 로컬에서 실행 가능.

---

## 주요 명령어

```bash
# 전체 스택 실행
docker-compose up --build

# 인프라(DB+Redis)만 실행
docker-compose up -d postgres redis

# 백엔드 로컬 실행
cd backend
uvicorn main:app --reload --port 8000

# DB 마이그레이션
cd backend
alembic revision --autogenerate -m "설명"
alembic upgrade head

# 프론트엔드 로컬 실행
cd frontend
npm install
npm run dev

# Playwright 브라우저 설치 (최초 1회)
playwright install chromium
```

---

## DB 스키마 핵심 설계

### `cars` 테이블
- `platform` (encar | kcar | kbchachacha | bobaedream)
- `external_id` — 플랫폼 자체 ID
- `UNIQUE(platform, external_id)` — 중복 수집 방지
- `raw_data jsonb` — 원본 API 응답 보존 (스키마 변경에 대비)

### `scores` 테이블
- `car_id` FK → cars
- 항목별 점수: `accident`, `mileage`, `price`, `inspection`, `rental`, `owner_changes`
- `total`, `grade` (S/A+/A/B/C/D/F)

### `price_history` 테이블
- 크롤링 시마다 가격 기록 → 가격 추이 차트·하락 알림용

---

## 채점 로직 (scoring/)

`C:\Project\car` 의 Chrome Extension JS 로직을 Python으로 1:1 포팅.
`calculator.py` 의 `calculate_score(car_data, weights)` 가 진입점.

기본 가중치 (합계 100):
- `accident`: 25, `inspection`: 20, `mileage`: 15, `price`: 15, `rental`: 15, `owner_changes`: 10

보험이력 비공개 시 −40점 패널티. 보험이력 미제공 시 사고 항목 40% 추정 적용 (최대 A등급 제한).

등급 기준: S≥95, A+≥90, A≥80, B≥70, C≥60, D≥41, F≤40

---

## 크롤러 설계 원칙

### BaseCrawler 인터페이스
```python
class BaseCrawler(ABC):
    async def fetch_list(self, page: int) -> list[dict]
    async def fetch_detail(self, external_id: str) -> dict
    async def normalize(self, raw: dict) -> CarCreate  # 공통 스키마로 변환
```

### 플랫폼별 접근 방식
- **엔카**: `api.encar.com` REST JSON API 직접 호출 (Playwright 불필요)
- **케이카**: Playwright async (CSR, JS 렌더링 필요)
- **KB차차차**: Playwright async (CSR)
- **보배드림**: httpx + BeautifulSoup (SSR, 가장 단순)

### 수집 정책
- 요청 간격: 플랫폼당 3~5초 랜덤 딜레이
- User-Agent: 실제 Chrome 브라우저 헤더
- 스케줄: 새벽 2~4시 전체 갱신, robots.txt 준수
- Redis로 중복 수집 방지 (최근 크롤링 시각 캐싱)

---

## API 엔드포인트 (backend)

```
GET  /cars                # 목록 조회 (필터: platform, brand, model, year_min/max,
                          #            price_min/max, mileage_max, grade, region)
GET  /cars/{id}           # 상세 + 점수 breakdown
GET  /cars/{id}/history   # 가격 이력
POST /admin/crawl         # 수동 크롤 트리거 (플랫폼 지정 가능)
GET  /health              # 헬스체크
```

---

## 환경변수 (.env)

```
POSTGRES_USER=cardash
POSTGRES_PASSWORD=...
POSTGRES_DB=cardash
DATABASE_URL=postgresql+asyncpg://cardash:...@postgres:5432/cardash
REDIS_URL=redis://redis:6379/0
CRAWL_INTERVAL_HOURS=6
```

---

## 참고 소스

- 채점 로직 원본: `C:\Project\car\scoring\` (JS)
- 엔카 API 구조: `C:\Project\car\detail-parser.js` 상단 주석 참고
- 엔카 검색 API: `api.encar.com/search/car/list/mobile`
