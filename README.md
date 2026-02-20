# Production Data Hub

생산 데이터 분석 및 AI 챗봇 시스템

## 주요 기능

- **Dashboard**: Streamlit 기반 데이터 시각화 (다크 모드 지원)
- **API Server**: FastAPI REST API (Rate Limiting 적용)
- **AI Chat**: Google Gemini 기반 자연어 쿼리
- **Manager**: 통합 서버 관리 GUI

---

## 설치 (Windows)

### 1. 저장소 클론
```bash
git clone https://github.com/ykh00046/new_calculator.git
cd new_calculator
```

### 2. 가상환경 생성 및 활성화
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -U pip
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일 생성:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DASHBOARD_PORT=8501
API_PORT=8000
```

---

## 실행

### 방법 1: Manager GUI (권장)
```bash
python manager.py
```

### 방법 2: 개별 실행
```bash
# API 서버
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Dashboard
python -m streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501
```

---

## 접속 정보

| 서비스 | URL | 설명 |
|--------|-----|------|
| Dashboard | http://localhost:8501 | 데이터 시각화 |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health Check | http://localhost:8000/healthz | 상태 확인 |

---

## API 요약

### Rate Limiting
| 엔드포인트 | 제한 | 헤더 |
|-----------|------|------|
| `/chat/` | 20 req/min | `Retry-After` |
| 기타 API | 60 req/min | `X-RateLimit-Remaining` |

### 주요 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/records` | 생산 레코드 조회 |
| GET | `/items` | 제품 목록 |
| GET | `/summary/monthly_total` | 월별 집계 |
| GET | `/summary/by_item` | 제품별 집계 |
| POST | `/chat/` | AI 자연어 쿼리 |

### 새로운 필터 파라미터

```
GET /records?lot_number=LT2026&min_quantity=100&max_quantity=500
```

| 파라미터 | 설명 |
|----------|------|
| `lot_number` | 로트 번호 (prefix 매칭) |
| `min_quantity` | 최소 생산량 |
| `max_quantity` | 최대 생산량 |

---

## Dashboard 기능

### UI Enhancement (v1.0.2)
- 다크/라이트 모드 토글
- KPI 대시보드 카드 (총생산량, 건수, 일평균, 최다제품)
- 제품 비교 탭 (Top 10 차트, 파이차트, 트렌드)
- 일별/주별/월별 집계 선택
- 필터 프리셋 저장 (최대 10개)
- 반응형 레이아웃

---

## 프로젝트 구조

```
Server_API/
├── api/                    # FastAPI 백엔드
│   ├── main.py            # API 엔드포인트
│   ├── chat.py            # AI 채팅 (멀티턴)
│   └── tools.py           # AI 도구 함수
├── dashboard/             # Streamlit 프론트엔드
│   ├── app.py             # 메인 대시보드
│   └── components/        # UI 컴포넌트
│       ├── theme.py       # 다크 모드
│       ├── kpi_cards.py   # KPI 카드
│       ├── charts.py      # 차트
│       └── presets.py     # 필터 프리셋
├── shared/                # 공유 모듈
│   ├── config.py          # 설정 상수
│   ├── database.py        # DB 라우팅
│   ├── cache.py           # API 캐싱
│   └── rate_limiter.py    # 속도 제한
├── tests/                 # 테스트 코드
├── manager.py             # 통합 관리자
└── requirements.txt       # 의존성
```

---

## 테스트

```bash
pytest tests/ -v
```

| 테스트 파일 | 케이스 수 | 설명 |
|-------------|:---------:|------|
| test_sql_validation.py | 16 | SQL 인젝션 방지 |
| test_rate_limiter.py | 16 | 속도 제한 |
| test_input_validation.py | 19 | 입력 검증 |

---

## 버전 이력

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| 1.0.2 | 2026-02-20 | UI Enhancement, Rate Limiting, Manager 개선 |
| 1.0.1 | 2026-02-13 | 성능 및 필터 강화 |
| 1.0.0 | 2026-02-12 | Initial Release |

---

## 문서

- [API 통합 가이드](docs/api_integration_guide.md)
- [변경 로그](docs/reports/changelog.md)
- [시스템 아키텍처](docs/specs/system_architecture.md)
