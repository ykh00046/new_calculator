# 변경 로그

> Production Data Hub (Server API) - 모든 주요 변경사항 기록

---

## [2026-02-13] - 성능 및 필터 강화 완료

### 추가 (Added)

- `shared/config.py`에 `SLOW_QUERY_THRESHOLD_MS = 500` 상수 추가
- `shared/logging_config.py`에 Slow Query 감지 로직 추가
  - 500ms 이상 쿼리 자동 WARNING 레벨 로깅
  - 3단계 분기: error → [Query Failed], slow → [Slow Query], ok → [Query OK]
- `api/main.py`에 `_summary_by_item_cached()` 함수 추가
  - `/summary/by_item` 엔드포인트 캐싱
  - `@api_cache("summary_by_item")` 데코레이터 적용
- `api/main.py`에 `_monthly_by_item_cached()` 함수 추가
  - `/summary/monthly_by_item` 엔드포인트 캐싱
  - `@api_cache("monthly_by_item")` 데코레이터 적용
- `api/main.py`의 `get_records()` 필터 파라미터 확대
  - `lot_number`: 로트 번호 prefix 필터 (예: `lot_number=LT2026`)
  - `min_quantity`: 최소 생산량 필터 (예: `min_quantity=100`)
  - `max_quantity`: 최대 생산량 필터 (예: `max_quantity=500`)

### 변경 (Changed)

- `api/main.py` - `summary_by_item()` 라우트
  - 날짜 정규화 로직을 라우트 함수에서 수행
  - 캐시 함수 `_summary_by_item_cached()`에 정규화된 값 위임
- `api/main.py` - `monthly_by_item()` 라우트
  - 파라미터 검증을 라우트 함수에서 수행
  - 캐시 함수 `_monthly_by_item_cached()`에 위임
- `api/main.py` - `get_records()` WHERE 절 빌드 로직
  - `lot_number LIKE ?` (prefix match) 조건 추가
  - `good_quantity >= ?` 및 `good_quantity <= ?` 범위 조건 추가
  - 기존 필터와 AND 결합으로 복합 필터 지원

### 수정 (Fixed)

- **S1**: Slow Query 감지 메커니즘 부재
  - 해결: `QueryLogger.__exit__`에 임계값 분기 추가
  - 기대 효과: 성능 병목 자동 감지, 로그 모니터링 가능
- **P1**: `/summary/by_item` 엔드포인트 성능
  - 이전: 매 요청마다 전체 테이블 집계 (캐싱 미적용)
  - 해결: `@api_cache` 데코레이터 적용
  - 기대 효과: 응답 시간 50%+ 단축, 캐시 적중 시 <10ms
- **P2**: `/summary/monthly_by_item` 엔드포인트 성능
  - 이전: 매 요청마다 전체 테이블 집계 (캐싱 미적용)
  - 해결: `@api_cache` 데코레이터 적용
  - 기대 효과: 응답 시간 50%+ 단축
- **F1**: `lot_number` 전용 필터 부재
  - 이전: `q` 파라미터로 3개 컬럼 동시 검색 (중간 매칭)
  - 해결: `lot_number` 파라미터 추가 (prefix 매칭, 인덱스 활용)
  - 기대 효과: 정확한 로트 검색, 성능 향상
- **F2**: `good_quantity` 범위 필터 부재
  - 이전: 수량 기반 필터 없음
  - 해결: `min_quantity` / `max_quantity` 파라미터 추가
  - 기대 효과: 소량/대량 배치 구분, 품질 분석 개선

### 성능 개선

| 항목 | 개선 내용 | 기대 효과 |
|------|----------|----------|
| P1 캐싱 | `/summary/by_item` @api_cache 적용 | 응답 시간 50%+ 단축 |
| P2 캐싱 | `/summary/monthly_by_item` @api_cache 적용 | 응답 시간 50%+ 단축 |
| S1 모니터링 | Slow Query 자동 감지 (500ms 임계값) | 성능 병목 즉시 파악 |

### 필터 기능 확대

| 기능 | 추가 내용 | 활용 사례 |
|------|----------|----------|
| F1 lot_number | 로트 번호 prefix 필터 | `?lot_number=LT2026` - LT2026으로 시작하는 로트만 조회 |
| F2 quantity 범위 | 최소/최대 생산량 필터 | `?min_quantity=1000` - 대량 배치, `?max_quantity=50` - 소량/불량 의심 배치 |
| 복합 필터 | 여러 필터 AND 결합 | `?lot_number=LT2026&min_quantity=100&max_quantity=500&item_code=BW0021` |

### 설계 일치율

- **Overall Match Rate: 100%**
- S1 (Slow Query): 100% PASS
- P1 (by_item 캐싱): 100% PASS
- P2 (monthly_by_item 캐싱): 100% PASS
- F1 (lot_number 필터): 100% PASS
- F2 (quantity 필터): 100% PASS
- 총 21/21개 설계 항목 완벽 구현

### 관련 파일

- 계획: `docs/01-plan/features/performance-and-filter-enhancement.plan.md`
- 설계: `docs/02-design/features/performance-and-filter-enhancement.design.md`
- 완료: `docs/reports/performance-and-filter-enhancement.report.md`

---

## [2026-02-12] - 4개 Critical 이슈 완료

### 추가 (Added)

- `.gitignore` 파일: 민감한 파일(`.env`, `__pycache__`, `*.db`, `logs/`, `.venv/`) 제외
- `.env.example` 파일: 개발자 온보딩용 환경 변수 템플릿
- `api/tools.py`에 `_strip_sql_comments()` 함수: SQL 주석 제거 정규식 처리
- `execute_custom_query()` 타임아웃 리소스 정리: `conn.interrupt()` + `thread.join()` + `conn.close()`
- SQL 검증 5단계 강화: 주석 제거 → 세미콜론 → SELECT → 금지어 (13개) → 테이블 참조

### 변경 (Changed)

- `api/tools.py` - `execute_custom_query()` 함수 리팩토링
  - 전용 연결 생성 (캐시되지 않음)
  - 읽기 전용 모드 (`?mode=ro`) 적용
  - 검증 로직 5단계로 확대
- `shared/database.py` - `get_connection()` 함수에 `row_factory` 초기화 추가
  - `conn.row_factory = sqlite3.Row` 통일 설정

### 수정 (Fixed)

- **C1**: API 키 노출 (`.env` 파일에 실제 키 포함)
  - 해결: `.gitignore`로 제외 + `.env.example` 제공
- **C2**: SQL Injection 검증 우회 가능성 (주석/세미콜론)
  - 해결: 주석 제거 후 검증 + 13개 금지어 추가
- **C3**: 쿼리 타임아웃 후 리소스 누수 (쿼리 계속 실행)
  - 해결: `conn.interrupt()` 호출로 즉시 중단
- **C4**: 캐시된 연결 상태 충돌 (row_factory 중복 설정)
  - 해결: `get_connection()` 한 곳에서만 설정

### 보안 개선

| 카테고리 | 이전 | 이후 |
|---------|------|------|
| API 키 노출 | ⚠️ HIGH | ✅ NONE |
| SQL Injection | ⚠️ MEDIUM | ✅ LOW |
| 리소스 누수 | ⚠️ YES | ✅ NO |
| 상태 경쟁 조건 | ⚠️ YES | ✅ NO |

### 설계 일치율

- **Overall Match Rate: 97%**
- C1: 100% PASS
- C2: 100% PASS
- C3: 100% PASS
- C4: 90% PARTIAL (전용 연결 row_factory 아키텍처 선택)

### 관련 파일

- 계획: `docs/reports/4-critical-issues-fix.plan.md`
- 설계: `docs/reports/4-critical-issues-fix.design.md`
- 분석: `docs/reports/4-critical-issues-fix.analysis.md`
- 완료: `docs/reports/4-critical-issues-fix.report.md`

---

## 버전 관리

| 버전 | 일자 | 설명 | 상태 |
|------|------|------|------|
| 1.0.1 | 2026-02-13 | 성능 및 필터 강화 완료 | ✅ Released |
| 1.0.0 | 2026-02-12 | 4개 Critical 이슈 수정 완료 | ✅ Released |

