# Production Analysis Dashboard - Development Plan

## 📋 프로젝트 개요

**목적**: 생산 데이터를 분석하고 시각화하는 인터랙티브 웹 대시보드
**기술 스택**: Streamlit, Pandas, Altair (SQLite DB)
**데이터 소스**: `C:\X\material_box\Raw_material_dashboard_v2\data\production_analysis.db`

---

## 🗄️ 데이터베이스 구조

### 테이블: `production_records`

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `id` | INTEGER | Primary Key |
| `production_date` | DATE | 생산 날짜 (한글 "오전/오후" 포함) |
| `lot_number` | VARCHAR(50) | LOT 번호 |
| `item_code` | VARCHAR(50) | 품목 코드 |
| `item_name` | VARCHAR(200) | 품목명 |
| `good_quantity` | DECIMAL(10,2) | 양품 수량 (kg) |
| `created_at` | TIMESTAMP | 생성 시각 |
| `updated_at` | TIMESTAMP | 수정 시각 |

### 제품 카테고리 분류 로직

Python 레이어에서 `item_code` 기반으로 자동 분류:

```python
def _categorize_product(item_code):
    if item_code.startswith('BC'):
        return 'Ink'          # 잉크 제품
    elif item_code.startswith('BW'):
        return 'Water'        # 수성 제품
    elif item_code.startswith('B') and item_code[1].isdigit():
        return 'Chemical'     # 화학 제품
    else:
        return 'Other'        # 기타
```

---

## 🎯 핵심 기능 요구사항

### 1. **사용자 인터페이스 (UI/UX)**

#### 초기 상태 (Skeleton UI)
- 대시보드 로드 시 빈 UI 프레임 표시
- "📌 Please select at least one product category from the sidebar to begin analysis" 안내 메시지
- 메트릭 카드에 "N/A" 플레이스홀더 표시
- 빠른 초기 로딩 경험 제공

#### 사이드바 필터
1. **날짜 범위 선택**
   - Start Date (기본값: 30일 전)
   - End Date (기본값: 오늘)
   - 날짜 유효성 검사 (종료일 > 시작일)

2. **제품 카테고리 멀티 셀렉트**
   - Ink, Water, Chemical, Other 등 동적 옵션
   - 기본값: 모든 카테고리 선택
   - 최소 1개 이상 선택 필요

#### 동적 대시보드 렌더링
- 선택된 카테고리에 따라 타이틀 자동 업데이트
  - 1개 선택: "Dashboard Summary - Ink"
  - 여러 개: "Dashboard Summary - Ink, Water +1 more"
  - 전체: "Dashboard Summary - All Categories"

### 2. **요약 메트릭 (Summary Metrics)**

4개의 주요 지표:
- 🏭 **Total Production**: 총 생산량 (kg)
- 📊 **Avg. Daily Production**: 일평균 생산량 (kg)
- 📝 **Records**: 총 레코드 수
- 🏷️ **Unique Products**: 고유 제품 수

추가 인사이트:
- 📅 Date Range: 분석 기간 (일수)
- 🥇 Top Product: 최다 생산 제품
- 📦 Categories: 카테고리별 레코드 수

### 3. **생산 트렌드 차트 (Multi-Line Chart)**

#### 기능
- **카테고리별 비교**: Altair `color` 인코딩으로 여러 카테고리 동시 표시
- **인터랙티브**: 줌, 팬, 호버 툴팁
- **범례**: 카테고리별 색상 구분 (우측 상단)
- **요약 통계**: 차트 하단 Expander에 카테고리별 Total/Average/Max/Min 표시

#### 색상 스키마
- Ink: 파랑 (`#1f77b4`)
- Water: 초록 (`#2ca02c`)
- Chemical: 주황 (`#ff7f0e`)
- Other: 빨강 (`#d62728`)

---

## 🛠️ 기술 구현 세부사항

### 파일 구조

```
production_analysis_dashboard/
├── app.py                       # 메인 애플리케이션 (UI 오케스트레이션)
├── requirements.txt             # streamlit, pandas, altair
├── PLAN.md                      # 이 문서
├── config/
│   └── settings.py              # DB 경로 설정
├── data_access/
│   └── db_connector.py          # DB 연결, 데이터 로드, 카테고리 분류
├── components/
│   ├── summary.py               # 요약 메트릭 컴포넌트
│   └── charts.py                # 차트 컴포넌트 (Altair)
└── utils/
    └── helpers.py               # 유틸리티 함수 (필요 시)
```

### 주요 파일별 책임

#### `app.py`
- **책임**: UI 레이아웃, 사용자 상호작용, 데이터 흐름 제어
- **구현**:
  - Streamlit 페이지 설정 (`st.set_page_config`)
  - 사이드바 필터 위젯 (날짜, 카테고리)
  - 데이터 로드 및 필터링
  - 빈 데이터 처리 (Skeleton UI)
  - 컴포넌트 호출 (`summary.display_summary_metrics`, `charts.create_production_trend_chart`)

#### `data_access/db_connector.py`
- **책임**: 데이터베이스 상호작용, 데이터 정제 및 변환
- **구현**:
  1. SQLite 연결 (`sqlite3.connect`)
  2. **한글 인코딩 처리**: `con.text_factory = lambda x: x.decode('cp949', errors='ignore')`
  3. 날짜 필터 쿼리 실행
  4. 한글 날짜 형식 변환 ("오전/오후" → "AM/PM")
  5. `production_date` 파싱 및 유효성 검사
  6. 제품 카테고리 컬럼 추가 (`_categorize_product`)
  7. 에러 처리 (logging + Streamlit UI 피드백)

#### `components/summary.py`
- **책임**: 요약 메트릭 계산 및 표시
- **구현**:
  - 빈 DataFrame 처리 (친화적인 안내 메시지)
  - 4개 주요 메트릭 계산
  - `st.metric()` 위젯으로 시각화
  - 추가 인사이트 (날짜 범위, 최다 생산 제품, 카테고리 분포)

#### `components/charts.py`
- **책임**: 데이터 시각화 (Altair 차트)
- **구현**:
  1. 빈 DataFrame 처리 (안내 메시지)
  2. 동적 타이틀 생성 (`selected_categories` 기반)
  3. 일별/카테고리별 데이터 그룹화
  4. Altair 멀티 라인 차트 생성:
     - `mark_line(point=True, strokeWidth=2.5)`
     - `color='product_category:N'` (카테고리별 색상)
     - 인터랙티브 툴팁
  5. 요약 통계 Expander

---

## 📝 5단계 개발 계획

### ✅ **Phase 1: 기본 인프라 구축** (완료)

**목표**: 프로젝트 구조 및 DB 연결 확립

**작업 항목**:
- [x] 프로젝트 폴더 구조 생성
- [x] `requirements.txt` 작성
- [x] `config/settings.py` DB 경로 설정
- [x] `data_access/db_connector.py` 기본 쿼리 함수 작성
- [x] DB 스키마 확인 (`inspect_db.py`)

**검증**:
- DB 연결 성공
- 샘플 데이터 조회 확인

---

### ✅ **Phase 2: 데이터 처리 및 한글 인코딩 해결** (완료)

**목표**: 데이터 정제 파이프라인 구축 및 인코딩 문제 해결

**작업 항목**:
- [x] 한글 인코딩 수정 (`text_factory` 설정)
- [x] 날짜 형식 변환 ("오전/오후" → "AM/PM")
- [x] `production_date` 파싱 로직 구현
- [x] 제품 카테고리 분류 함수 (`_categorize_product`)
- [x] 에러 처리 개선 (logging + `st.error()`)

**검증**:
- 한글 품목명 정상 표시
- 날짜 파싱 에러 0건
- 카테고리 자동 분류 확인

---

### ✅ **Phase 3: UI 컴포넌트 구현** (완료)

**목표**: Skeleton UI, 필터, 메트릭, 기본 차트 구현

**작업 항목**:
- [x] `app.py` 사이드바 필터 추가
  - [x] 날짜 범위 선택
  - [x] 카테고리 멀티 셀렉트
- [x] Skeleton UI 구현 (빈 데이터 상태)
- [x] `summary.py` 메트릭 카드 구현
- [x] 추가 인사이트 표시 (날짜 범위, 최다 생산 제품, 카테고리)
- [x] 동적 타이틀 업데이트

**검증**:
- 필터 선택 시 데이터 정상 필터링
- 빈 선택 시 Skeleton UI 표시
- 메트릭 정확성 확인

---

### ✅ **Phase 4: 멀티 라인 차트 구현** (완료)

**목표**: 카테고리별 비교 차트 완성

**작업 항목**:
- [x] `charts.py` Altair 멀티 라인 차트 구현
  - [x] `groupby(['date', 'product_category'])`
  - [x] `color='product_category:N'` 인코딩
  - [x] 색상 스키마 설정
  - [x] 범례 위치 조정 (우측 상단)
- [x] 인터랙티브 툴팁 추가
- [x] 요약 통계 Expander 추가

**검증**:
- 단일 카테고리 선택 시 1개 라인 표시
- 복수 카테고리 선택 시 멀티 라인 표시
- 색상 구분 명확
- 툴팁 정보 정확

---

### 🔄 **Phase 5: 테스트 및 최적화** (진행 중)

**목표**: 품질 보증, 성능 최적화, 문서화

**작업 항목**:
- [ ] 기능 테스트
  - [ ] 전체 워크플로우 테스트 (초기 로드 → 필터 → 차트)
  - [ ] 엣지 케이스 테스트 (빈 데이터, 단일 레코드, 날짜 역순)
  - [ ] 카테고리 조합 테스트 (1개, 전체, 일부)
- [ ] 성능 최적화
  - [ ] 쿼리 성능 확인 (19,147건 로드 시간)
  - [ ] Altair 차트 렌더링 최적화
  - [ ] 캐싱 고려 (`@st.cache_data`)
- [ ] 사용자 피드백 반영
  - [ ] UI 개선 사항 수집
  - [ ] 추가 메트릭 요구사항 확인
- [ ] 문서화
  - [ ] README.md 작성 (설치, 실행, 사용법)
  - [ ] 코드 주석 정리
  - [ ] 배포 가이드 작성 (Streamlit Cloud / Docker)

**검증 체크리스트**:
- [ ] 대시보드 초기 로딩 3초 이내
- [ ] 모든 필터 조합에서 에러 없음
- [ ] 차트 렌더링 지연 없음
- [ ] 한글 품목명 깨짐 0건
- [ ] 사용자 가이드 문서 완성

---

## 🐛 알려진 이슈 및 해결 방법

### ✅ 해결됨

1. **한글 인코딩 문제**
   - **증상**: 품목명이 "ƾĿ"로 표시
   - **해결**: `con.text_factory = lambda x: x.decode('cp949', errors='ignore')`

2. **날짜 파싱 실패**
   - **증상**: "오전/오후" 형식 파싱 불가
   - **해결**: `str.replace('오전', 'AM')` + `errors='coerce'`

3. **빈 데이터 UI**
   - **증상**: 선택 해제 시 에러 발생
   - **해결**: Skeleton UI + 친화적인 안내 메시지

4. **차트 단일 라인 문제**
   - **증상**: 카테고리별 비교 불가
   - **해결**: `color='product_category:N'` 인코딩 추가

---

## 🚀 향후 개선 계획 (Optional)

### 추가 기능 아이디어

1. **필터 확장**
   - 특정 제품 선택 (Multi-select)
   - LOT 번호 검색
   - 생산량 범위 슬라이더

2. **추가 차트**
   - 제품별 파이 차트 (Top 10)
   - 카테고리별 월간 히트맵
   - 생산 효율 추세 (불량률 포함 시)

3. **데이터 내보내기**
   - CSV 다운로드 버튼
   - PDF 보고서 생성
   - Excel 내보내기

4. **실시간 업데이트**
   - DB 변경 감지 (Watchdog)
   - 자동 새로고침 (WebSocket)

5. **알림 기능**
   - 목표 생산량 미달 알림
   - 특정 제품 생산 완료 알림

---

## 📊 데이터 통계 (2025-10-29 기준)

- **총 레코드 수**: 19,147건
- **날짜 범위**: 2025-01-07 ~ 2025-10-23 (약 10개월)
- **품목 카테고리**:
  - Water (BW): 대다수
  - Chemical (B[0-9]): 중간
  - Ink (BC): 소수
  - Other: 극소수

---

## 🔗 참고 자료

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Altair Gallery](https://altair-viz.github.io/gallery/)
- [Pandas API Reference](https://pandas.pydata.org/docs/reference/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

**최종 업데이트**: 2025-10-29
**버전**: 3.0
**작성자**: Production Analysis Team

---

## v2.0 Review & Next Steps (2025-10-29)

The current implementation is a significant improvement, featuring a robust tab-based architecture, advanced filtering, and detailed comparison metrics. The code is well-structured and follows good design principles.

Based on a full code review, the following suggestions are made for the next iteration.

### 1. Suggestion: Refactor for Code Reusability

*   **Observation:** The code for generating the "Production Trend by Product" chart is duplicated across `weekly_tab.py`, `monthly_tab.py`, and `custom_tab.py`.
*   **Recommendation:** Create a single, reusable function within `components/charts.py` to generate this chart. Each tab module will then call this central function.
*   **Benefit:** This will reduce code duplication (DRY principle), simplify maintenance, and ensure a consistent look and feel across all tabs.

### 2. Observation: Data Loading Strategy

*   **Current Approach:** The application loads the entire year's data into memory on startup.
*   **Assessment:** This approach provides a fast and responsive user experience for the current data size.
*   **Future Consideration:** For future scalability with a much larger database, implementing caching (`@st.cache_data`) on data loading functions would be beneficial to balance performance and memory usage.

### Next Action Plan

1.  **Proceed with UI/UX Improvement:** The immediate next step is to implement the refactoring suggested in Point 1.
2.  **Implementation Steps:**
    *   Create a new function `create_product_specific_trend_chart` in `components/charts.py`.
    *   Move the duplicated chart logic from the tab files into this new function.
    *   Modify `weekly_tab.py`, `monthly_tab.py`, and `custom_tab.py` to import and use this new reusable function.

## 🎯 실시간 생산 현황 모니터링 (Real-time Production Monitoring)

사용자님의 최우선 목표인 '생산 현황 실시간 확인'을 위해 다음 기능들을 구현합니다.

### 1. 자동 대시보드 새로고침 (Auto-Refresh)

*   **목표:** 대시보드 데이터가 주기적으로 자동으로 업데이트되도록 합니다.
*   **구현 방안:** `app.py`의 `load_production_data` 함수에 적용된 `@st.cache_data`의 `ttl` (Time To Live) 값을 **4시간(4 * 3600초)**으로 조정합니다. 이는 데이터가 4시간마다 데이터베이스에서 새로 로드됨을 의미합니다.
*   **추가:** 사용자가 필요할 때 즉시 데이터를 새로고침할 수 있도록 '새로고침' 버튼을 추가합니다.

### 2. "최종 업데이트 시간" 표시

*   **목표:** 대시보드에 표시되는 데이터가 언제 마지막으로 업데이트되었는지 명확히 알려줍니다.
*   **구현 방안:** `app.py`에서 데이터를 로드한 시점의 타임스탬프를 기록하고, 대시보드 상단에 "데이터 최종 업데이트: YYYY-MM-DD HH:MM:SS" 형식으로 표시합니다.

### 3. 최신 생산 기록 요약 (Latest Production Overview)

*   **목표:** 가장 최근에 발생한 생산 기록들을 한눈에 볼 수 있도록 합니다.
*   **구현 방안:** `app.py` 또는 새로운 컴포넌트 파일에, 데이터프레임에서 가장 최근 N개(예: 5~10개)의 생산 기록을 추출하여 컴팩트한 테이블 또는 카드 형태로 표시하는 섹션을 추가합니다. `item_name`, `lot_number`, `good_quantity`, `production_date` 등의 핵심 정보를 포함합니다.
