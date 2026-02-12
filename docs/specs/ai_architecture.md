# AI Chat System Architecture & Specification

## 1. 개요
본 문서는 `Production Data Hub`의 AI Chat 시스템(`api/chat.py`, `api/tools.py`)의 동작 원리, 프롬프트 설계, 도구 명세를 기술합니다. AI 동작을 수정하거나 확장할 때 본 문서를 기준으로 합니다.

---

## 2. 시스템 구성 (Architecture)

### 2.1 모델 정보
- **Provider:** Google Gemini API
- **Model:** `gemini-2.0-flash`
- **Mode:** Function Calling (Auto)

### 2.2 핵심 컴포넌트
- **Controller (`api/chat.py`):** 사용자 질문 수신, Gemini API 통신, 시스템 프롬프트 주입.
- **Tools (`api/tools.py`):** 실제 DB를 조회하는 Python 함수 집합. Gemini가 이 함수들의 스키마를 읽고 자동으로 실행 요청을 보냄.
- **DBRouter (`shared/database.py`):** 날짜 범위 기반으로 Archive/Live DB를 자동 선택하고 UNION 쿼리를 생성.
- **Database (`SQLite`):** 2025(Archive) + 2026(Live) 통합 조회.

---

## 3. 프롬프트 엔지니어링 (Prompt Engineering)

### 3.1 시스템 프롬프트 (Persona)
AI에게 부여된 역할 정의입니다. (`api/chat.py` 내 `SYSTEM_INSTRUCTION`)

> "너는 'Production Data Hub' 시스템의 전문 생산 데이터 분석가야..."

**핵심 원칙:**
1.  **데이터 기반:** 반드시 도구(Tool)를 사용하여 조회된 데이터로만 답변한다.
2.  **정직함:** 데이터가 없으면 "없다"고 말한다. (추측 금지)
3.  **검색 우선:** 제품명(키워드) 질문 시 `search_production_items`를 먼저 수행한다.
4.  **단위/기간 명시:** 수치에는 단위(개, 건)와 기준 기간을 반드시 포함한다.

---

## 4. 도구 명세 (Tools Specification)

AI가 사용할 수 있는 함수 목록입니다.

### 4.1 `search_production_items(keyword, include_archive)`
- **목적:** 사용자가 불확실한 제품명(예: "P물")을 말했을 때, 정확한 `item_code`를 찾기 위해 사용.
- **입력:**
    - `keyword` (문자열): 검색 키워드
    - `include_archive` (bool, 기본값=True): Archive DB 포함 여부. "작년", "2025년", "단종" 등의 표현 시 True, "올해만", "현재 제품만" 표현 시 False.
- **로직:** `item_code` 또는 `item_name`에 키워드가 포함된(`LIKE %...%`) 상위 10개 제품 검색.
- **출력:** 후보 제품 목록(코드, 이름, 기록 수).

### 4.2 `get_production_summary(date_from, date_to, item_code)`
- **목적:** 특정 기간의 생산량 합계, 평균, 건수 등을 조회.
- **입력:**
    - `date_from`, `date_to` (YYYY-MM-DD)
    - `item_code` (옵션, 정확한 코드)
- **로직 (Data Policy):**
    - **날짜 보정:** `date_to`를 **다음날 00:00 미만**(`< next_day`)으로 변환하여 해당 일자 전체를 포함.
    - **DB 라우팅:** 2026년 1월 1일 기준으로 `archive_2025.db`와 `production_analysis.db`를 `UNION ALL`로 통합 조회.
- **출력:** 합계(total_quantity), 평균(average_quantity), 건수(production_count).

---

## 5. 데이터 처리 규칙 (Data Logic)

### 5.1 날짜 해석
- AI는 "오늘", "작년" 등의 자연어를 `YYYY-MM-DD` 형식으로 변환하여 도구에 전달합니다.
- **시스템 규칙:** 
    - `date_from`: Inclusive (`>=`)
    - `date_to`: Exclusive (`< date_to + 1 day`)

### 5.2 DB 연결 정책
- 모든 도구는 `mode=ro` (Read-Only) 모드로 DB에 연결하여 데이터 무결성을 보장합니다.
- `ATTACH DATABASE` 구문을 사용하여 물리적으로 분리된 연도별 DB를 논리적으로 하나처럼 다룹니다.

---

## 6. 유지보수 가이드

### 모델 변경 시
`api/chat.py`의 `genai.GenerativeModel(...)` 부분에서 `model_name`을 수정합니다.

### 도구 추가 시
1.  `api/tools.py`에 새로운 파이썬 함수를 작성합니다. (Docstring 필수 - AI가 읽음)
2.  `api/tools.py` 하단의 `PRODUCTION_TOOLS` 리스트에 함수명을 추가합니다.
3.  `api/chat.py`의 시스템 프롬프트에 새 도구 사용 가이드를 추가하면 더 잘 동작합니다.
