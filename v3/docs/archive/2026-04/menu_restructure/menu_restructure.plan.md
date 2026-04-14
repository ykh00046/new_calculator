# menu_restructure.plan.md
Summary: 대시보드 제거 및 기능 중심의 3단 메뉴 분리(수기/일괄/관리) 구조 개편 계획  
Author: Antigravity  
Status: Plan

---

## 1. Overview & Purpose

### 1.1 배경 (Background)
현재 애플리케이션은 중복된 “대시보드(현황)” 메뉴와 혼재된 “입력(수기+일괄)” 기능으로 인해 작업자의 동선이 비효율적이다. 현장의 작업자는 빠른 입력과 조회를 원하며, 불필요한 현황판보다는 직관적인 기능 접근을 선호한다.

### 1.2 목적 (Goal)
불필요한 대시보드 단계를 제거하고, 핵심 기능을 사이드바 메뉴로 승격시켜 **One-Click Access** 환경을 구축한다. 또한 수기 입력과 일괄 생성 기능을 명확히 분리하여 사용자의 인지 부하를 줄인다.

---

## 2. Scope

### 2.1 In-Scope (포함 범위)
- 대시보드 제거: 앱 진입 시 즉시 “배합(Mixing)” 화면 표시
- 기능 재배치 (사이드바 메뉴화 또는 상단 커맨드바):
  - 작업자 변경
  - 기록 조회
  - 구글 시트 설정 (설정 하위 또는 별도 메뉴)
- 3단 메뉴 분리:
  - 수기 입력 (Manual Input)
  - 일괄 생성 (Bulk Creation)
  - DHR 관리 (Recipe Management)

### 2.2 Out-Scope (제외 범위)
- 비즈니스 로직(DB 저장, 엑셀/PDF 생성 등) 변경 없음
- 테마/색상 변경 없음 (레이아웃/네비 구조 변경은 포함)

---

## 3. Requirements

### 3.1 Functional Requirements
1. 앱 실행 후 로그인 시 즉시 “배합” 탭이 열려야 한다.
2. 사이드바에서 **수기 입력**, **일괄 생성**, **DHR 관리**를 독립적으로 선택 가능해야 한다.
3. **일괄 생성** 화면은 엑셀 붙여넣기(Ctrl+V)에 최적화된 전용 UI를 제공해야 한다.
4. “기록 조회”와 “작업자 변경”은 **상단 커맨드바 또는 사이드바**에서 상시 접근 가능해야 한다.
5. “구글 시트 설정”은 **설정 하위** 또는 **사이드바 별도 항목** 중 하나로 명확히 위치가 결정되어야 한다.

### 3.2 Non-Functional Requirements
1. Refactoring Safety: 기존 코드를 복사/이동하는 과정에서 동작 불능 상태가 되지 않도록 단계적으로 분리한다.
2. Regression Safety: 메뉴 변경 이후 핵심 저장/조회 흐름이 깨지지 않아야 한다.

---

## 4. Architecture Plan

### 4.1 UI Navigation Structure (Proposed)

```mermaid
graph TD
    Main[Main Window]
    Sidebar[Sidebar Navigation]

    Main --> Sidebar

    Sidebar --> Mixing[🧪 배합 (Default)]
    Sidebar --> Manual[✍️ 수기 입력]
    Sidebar --> Bulk[📑 일괄 생성]
    Sidebar --> Dhr[🧰 DHR 관리]
    Sidebar --> Records[📜 기록 조회]
    Sidebar --> Settings[🔧 설정]
```

### 4.2 Component Design

#### [NEW] BulkCreationInterface  
**Path**: `v3/ui/panels/bulk_creation_interface.py`  
**Role**: 대량 데이터 생성 전용 패널

**UI 구성**
- PasteableSimpleTableWidget (날짜/수량 2열)
- MaterialsTable (공통 자재 스펙)
- GeneratorAction (실행 버튼)

**입력 규칙 (예시)**
- 날짜: `YYYY-MM-DD`
- 수량: 숫자 (g)

#### [MODIFY] Main Window  
**Path**: `v3/ui/main_window.py`

**변경 내용**
- `build_dashboard_page` 제거
- `addSubInterface` 구성 재편:
  - 배합 (Start Page)
  - 수기 입력
  - 일괄 생성 (New)
  - DHR 관리
  - 기록 조회 (Sidebar Item)
  - 설정 (구글 시트/PDF 포함)

---

## 5. Migration Strategy

1. **Backup**  
   - `main_window.py`, `manual_input_interface.py` 백업 생성
2. **Create New Interface**  
   - `BulkCreationInterface` 파일 생성 및 로직 이식
3. **Clean Existing Interface**  
   - `ManualInputInterface`에서 일괄 생성 코드 제거
4. **Update Main Window**  
   - 대시보드 제거 및 신규 메뉴 연결
5. **Verify**  
   - 각 메뉴 정상 진입 및 기능 동작 확인

---

## 6. Verification Checklist

- [ ] 앱 로그인 후 기본 화면이 배합인지 확인
- [ ] 사이드바에서 수기/일괄/DHR 메뉴 진입 확인
- [ ] 기록 조회 접근 확인
- [ ] 작업자 변경 접근 확인
- [ ] 구글 시트 설정 접근 확인
