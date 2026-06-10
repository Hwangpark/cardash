# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

---

## 프로젝트 개요

**중고차 통합 대시보드** — 국내 주요 중고차 플랫폼(엔카, 케이카, KB차차차, 보배드림)의 매물을 주기적으로 수집·채점하여 하나의 웹 인터페이스에서 비교 조회하는 풀스택 서비스.

- **GitHub**: https://github.com/Hwangpark/cardash
- **기본 브랜치**: `main`
- **브랜치 네이밍**: `feature/기능명`, `fix/버그명`, `chore/작업명`

---

## 모노레포 구조

```
cardash/
├── docker-compose.yml
├── .env
├── backend/                    # FastAPI (Python)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py               # pydantic Settings
│   ├── database.py             # SQLAlchemy 비동기 엔진·세션
│   ├── models/
│   │   ├── car.py
│   │   ├── score.py
│   │   └── price_history.py
│   ├── schemas/
│   ├── routers/
│   │   ├── cars.py             # GET /cars, GET /cars/{id}
│   │   └── admin.py            # POST /admin/crawl
│   ├── crawlers/
│   │   ├── base.py             # BaseCrawler ABC
│   │   ├── encar.py            # api.encar.com JSON 직접 호출
│   │   ├── kcar.py             # Playwright (CSR)
│   │   ├── kbchachacha.py      # Playwright (CSR)
│   │   └── bobaedream.py       # BeautifulSoup (SSR)
│   ├── scoring/                # C:\Project\car JS 로직 → Python 포팅
│   │   ├── accident.py
│   │   ├── mileage.py
│   │   ├── price.py
│   │   ├── inspection.py
│   │   ├── rental.py
│   │   ├── owner.py
│   │   ├── grade.py
│   │   └── calculator.py       # calculate_score() 오케스트레이터
│   └── scheduler.py
└── frontend/                   # React + Vite + TypeScript
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── main.tsx
        ├── api/                # TanStack Query 훅 + axios
        ├── pages/
        │   ├── ListPage.tsx
        │   └── DetailPage.tsx
        └── components/
            ├── ScoreBadge.tsx
            ├── ScoreBreakdown.tsx
            ├── CarCard.tsx
            └── FilterPanel.tsx
```

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프론트엔드 | React 18 + Vite + TypeScript |
| 서버 상태 | TanStack Query v5 |
| 백엔드 | FastAPI 0.115+ (Python) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| DB | PostgreSQL 16 on Docker |
| 크롤러 | Playwright async + BeautifulSoup4 |
| 스케줄러 | APScheduler 3.x |
| 캐시 | Redis 7 on Docker |
| 컨테이너 | Docker Compose v2 |

---

## 주요 명령어

```bash
# 전체 실행
docker-compose up --build

# 개발 시 — 인프라만 Docker, 앱은 로컬
docker-compose up -d postgres redis
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# DB 마이그레이션
cd backend
alembic revision --autogenerate -m "설명"
alembic upgrade head

# 타입 체크 / 린트
cd frontend && npm run type-check
cd frontend && npm run lint

# Playwright 브라우저 설치 (최초 1회)
playwright install chromium
```

---

## Docker Compose 서비스

```
postgres  → 5432
redis     → 6379
backend   → 8000  (postgres, redis 의존)
frontend  → 3000  (backend 의존)
```

---

## DB 스키마 핵심

### `cars`
- `platform`: encar | kcar | kbchachacha | bobaedream
- `UNIQUE(platform, external_id)` — 중복 수집 방지
- `raw_data jsonb` — 원본 응답 보존 (API 구조 변경 대비)

### `scores`
- `car_id` FK → cars
- 항목별: accident, mileage, price, inspection, rental, owner_changes
- `total`, `grade` (S/A+/A/B/C/D/F)

### `price_history`
- 크롤링마다 가격 기록 → 가격 추이 차트 및 하락 알림용

---

## 채점 로직 (scoring/)

`C:\Project\car` Chrome Extension JS의 Python 1:1 포팅.
진입점: `calculator.py` → `calculate_score(car_data, weights)`

**기본 가중치** (합계 100):
accident 25 / inspection 20 / mileage 15 / price 15 / rental 15 / owner_changes 10

**패널티**: 보험이력·성능점검 비공개 시 −40점.
보험이력 미제공 시 사고 항목 40% 추정 → 최대 A등급 제한.

**등급**: S≥95 / A+≥90 / A≥80 / B≥70 / C≥60 / D≥41 / F≤40

---

## 크롤러 설계

### BaseCrawler 인터페이스

```python
class BaseCrawler(ABC):
    async def fetch_list(self, page: int) -> list[dict]
    async def fetch_detail(self, external_id: str) -> dict
    async def normalize(self, raw: dict) -> CarCreate
```

### 플랫폼별 접근

| 플랫폼 | 방식 |
|--------|------|
| 엔카 | `api.encar.com` REST JSON (Playwright 불필요) |
| 케이카 | Playwright async (CSR) |
| KB차차차 | Playwright async (CSR) |
| 보배드림 | httpx + BeautifulSoup (SSR) |

**수집 정책**: 요청 간격 3~5초 랜덤, 새벽 2~4시 전체 갱신, robots.txt 준수.

---

## API 엔드포인트

```
GET  /cars                 # platform, brand, model, year, price, mileage, grade, region 필터
GET  /cars/{id}            # 상세 + 점수 breakdown
GET  /cars/{id}/history    # 가격 이력
POST /admin/crawl          # 수동 크롤 트리거
GET  /health
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

## 코딩 규칙 (항상 준수)

### 함수 길이
- **함수 하나는 30줄 이하**. 초과하면 반드시 분리한다.
- 역할이 하나인 함수만 작성한다. 여러 일을 하면 쪼갠다.

### 불필요한 코드 제거
- 사용하지 않는 함수, import, 변수는 즉시 삭제한다.
- 주석으로 막아둔 dead code는 남기지 않는다.
- TODO/FIXME는 실제로 처리하거나 이슈로 등록한다.

### 폴더 & 파일 구조
- **기능(feature)/API 단위로 폴더를 나눈다.**
- 백엔드: `routers/`, `crawlers/`, `scoring/` 각 파일은 단일 도메인만 담당.
- 프론트엔드: 페이지별 폴더 아래 컴포넌트·훅·타입을 함께 둔다.
  ```
  pages/
    ListPage/
      index.tsx
      useCarList.ts
      CarCard.tsx
  ```
- 파일 하나가 200줄을 넘으면 분리를 검토한다.

### 네이밍
- 함수명은 동사로 시작 (`fetchCars`, `scoreAccident`, `normalizeRaw`).
- 불린 변수/함수는 `is`, `has`, `can` 접두사 (`isDealer`, `hasInsurance`).
- 상수는 UPPER_SNAKE_CASE.

---

## Git 워크플로우 & 코드 리뷰

### PR 전 체크리스트

PR 전에 `/pre-pr` 커맨드를 실행한다.

1. `git diff main...HEAD` — 변경 내용 자기검토
2. `cd frontend && npm run type-check`
3. `cd frontend && npm run lint`
4. `cd backend && python -m pytest`
5. `/code-review` 스킬 실행 후 지적 사항 반영
6. PR 설명에 **Why / What / 테스트 방법** 작성

### 코드 리뷰 방식

- **빠른 리뷰**: `/code-review`
- **심층 리뷰**: `/code-review ultra` (중요 PR에만 사용, 비용 발생)
- **PR 번호 지정**: `/code-review ultra 42`

### 커밋 메시지 (Conventional Commits)

```
feat: 새 기능
fix: 버그 수정
chore: 빌드/설정 변경
refactor: 리팩토링
docs: 문서 수정
```

---

## MCP 서버

`~/.Codex/settings.json` (글로벌)에 추가 필요.

### GitHub MCP
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "<GitHub PAT>" }
    }
  }
}
```
→ PR 생성/조회, 이슈 관리 자동화.

### PostgreSQL MCP
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres",
               "postgresql://cardash:password@localhost:5432/cardash"]
    }
  }
}
```
→ 개발 중 DB 직접 쿼리 (차량 데이터 확인, 채점 결과 검증).

---

## 훅 & 스킬

**훅** (`.Codex/settings.json` 프로젝트 레벨 설정됨):
- `PostToolUse[Bash → git commit]` → 커밋 후 type-check 리마인더
- `PreToolUse[Bash → git push]` → PR 체크리스트 출력

**주요 스킬**:
- `/pre-pr` — PR 전 자기검토 체크리스트 실행 (`.Codex/commands/pre-pr.md`)
- `/code-review` — 현재 브랜치 코드 리뷰
- `/code-review ultra` — 심층 멀티 에이전트 리뷰
- `/verify` — 기능 동작 확인

---

## 참고 소스

- 채점 로직 원본 (JS): `C:\Project\car\scoring\`
- 엔카 API 구조 문서: `C:\Project\car\detail-parser.js` 상단 주석
- 엔카 검색 API: `api.encar.com/search/car/list/mobile`
