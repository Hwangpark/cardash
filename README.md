# 중고차 통합 대시보드

국내 주요 중고차 플랫폼(엔카, 케이카, 보배드림)의 매물을 수집하고, 0~100점으로 채점해서 한 곳에서 비교하는 풀스택 웹 서비스.

---

## 실행 전 준비

### 필수 설치
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (PostgreSQL + Redis 컨테이너)
- Python 3.11+
- Node.js 18+

### 최초 1회 설정

```powershell
# 1. 리포 클론
git clone https://github.com/Hwangpark/cardash.git
cd cardash

# 2. 백엔드 가상환경 생성 및 패키지 설치
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
playwright install chromium       # 케이카/보배드림 크롤러용

# 3. 프론트엔드 패키지 설치
cd ..\frontend
npm install
```

---

## 개발 서버 실행

### 1단계 — DB + Redis 올리기 (Docker)

```powershell
# 프로젝트 루트(cardash/)에서
docker compose up -d postgres redis
```

> 포트 충돌 주의: postgres → **5433**, redis → **6379**
> (기존 billain DB가 5432를 쓰므로 분리)

---

### 2단계 — 백엔드 실행

```powershell
cd backend
$env:DATABASE_URL = "postgresql+asyncpg://cardash:cardash1234@localhost:5433/cardash"
$env:REDIS_URL    = "redis://localhost:6379/0"
.\.venv\Scripts\uvicorn main:app --reload --port 8000
```

접속: http://localhost:8000  
API 문서: http://localhost:8000/docs

---

### 3단계 — 프론트엔드 실행

```powershell
cd frontend
npm run dev
```

접속: http://localhost:5173

> Vite proxy가 `/cars`, `/admin`, `/health` 요청을 백엔드(8000)로 자동 포워딩.  
> 백엔드가 먼저 실행 중이어야 합니다.

---

## 매물 수집 (크롤링)

백엔드가 실행 중인 상태에서 아래 API를 호출합니다.

### 전체 수집 (엔카 기준)

```powershell
# 엔카 — 50페이지 (약 2,000개)
Invoke-WebRequest "http://localhost:8000/admin/crawl?platform=encar&max_pages=50" -Method POST

# 케이카 — JSON API 직접 호출 (빠름)
Invoke-WebRequest "http://localhost:8000/admin/crawl?platform=kcar&max_pages=10" -Method POST

# 보배드림 — HTML 파싱
Invoke-WebRequest "http://localhost:8000/admin/crawl?platform=bobaedream&max_pages=10" -Method POST
```

### 특정 차종만 수집 (예: 제네시스 G70)

```powershell
# G70
Invoke-WebRequest "http://localhost:8000/admin/crawl?platform=encar&make=제네시스&model_group=G70&max_pages=20" -Method POST

# 더 뉴 G70
Invoke-WebRequest "http://localhost:8000/admin/crawl?platform=encar&make=제네시스&model_group=더+뉴+G70&max_pages=20" -Method POST
```

### 수집 현황 확인

```powershell
docker exec cardash-postgres psql -U cardash -d cardash -c "SELECT platform, COUNT(*) FROM cars GROUP BY platform ORDER BY COUNT(*) DESC;"
```

---

## 채점 (분석하기)

프론트에서 차량 카드 클릭 → **"지금 분석하기"** 버튼을 누르면:

1. 엔카 API 3개 (vehicle / record / inspection) 병렬 호출
2. JS 채점 로직(Chrome Extension) Python 1:1 포팅 버전으로 채점
3. 결과 DB 저장 → 다음 방문 시 캐시 사용

> 현재 엔카 매물만 실채점 지원. 케이카/보배드림은 기본 점수 반환.

---

## 프로젝트 구조

```
cardash/
├── docker-compose.yml      # postgres:5433, redis:6379, backend:8000, frontend:3001
├── .env                    # DB 접속 정보 (git 제외)
├── backend/
│   ├── main.py             # FastAPI 앱 진입점
│   ├── crawlers/           # 플랫폼별 크롤러 (encar/kcar/bobaedream/kbchachacha)
│   ├── scoring/            # 채점 모듈 (JS → Python 포팅)
│   ├── services/           # analyzer.py — on-demand 채점 서비스
│   ├── routers/            # cars.py, admin.py
│   ├── models/             # SQLAlchemy ORM (Car, Score, PriceHistory)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── ListPage/   # 매물 목록 + 필터
    │   │   └── DetailPage/ # 상세 + 점수 패널
    │   ├── api/            # axios 클라이언트
    │   └── utils/images.ts # 플랫폼별 이미지 CDN 처리
    └── vite.config.ts      # proxy: /cars → localhost:8000
```

---

## 지원 플랫폼

| 플랫폼 | 방식 | 이미지 CDN |
|--------|------|-----------|
| 엔카 | `api.encar.com` JSON API | `ci.encar.com/carpicture` |
| 케이카 | `api.kcar.com` JSON API | `img.kcar.com` |
| 보배드림 | HTML 파싱 (httpx + BS4) | `file2.bobaedream.co.kr` |
| KB차차차 | Playwright (봇 감지 이슈 해결 중) | `img.kbchachacha.com` |

---

## 등급 기준

| 등급 | 점수 | 의미 |
|------|------|------|
| S | 95점 이상 | 최상급 |
| A+ | 90~94점 | 매우 우수 |
| A | 80~89점 | 우수 |
| B | 70~79점 | 양호 |
| C | 60~69점 | 보통 |
| D | 41~59점 | 미흡 |
| F | 40점 이하 | 불량 |

채점 항목: 사고/보험(25) · 성능점검(20) · 주행거리(15) · 가격(15) · 렌트이력(15) · 소유주변경(10)

---

## 자주 쓰는 명령

```powershell
# 컨테이너 상태 확인
docker ps

# DB 접속
docker exec -it cardash-postgres psql -U cardash -d cardash

# DB 내 차량 수 확인
docker exec cardash-postgres psql -U cardash -d cardash -c "SELECT platform, COUNT(*) FROM cars GROUP BY platform;"

# 백엔드 의존성 추가 후
cd backend && .\.venv\Scripts\pip install 패키지명

# 프론트 빌드 확인 (TypeScript 에러 체크)
cd frontend && npm run build
```
