# UX Improvements Design Document

> **Summary**: 사용자 작업 효율성 향상을 위한 UI/UX 개선 사항 상세 설계
> **Author**: AI Assistant
> **Created**: 2026-01-31
> **Status**: Draft

---

## 1. 개요 (Overview)

배합 프로그램의 사용성을 높이기 위해 **창 관리**, **입력 흐름(Focus Flow)**, **시각적 피드백**을 개선한다. 작업자는 터치스크린 또는 키보드/마우스를 혼용하므로 직관적이고 끊김 없는 입력 경험이 중요하다.

## 2. 주요 개선 기능 (Key Features)

### 2.1 창 최상위 고정 (Window Always on Top)

- **목적**: 다른 프로그램 작업 중에도 배합 현황을 항상 모니터링하기 위함.
- **설계**:
  - `MainWindow` 초기화 시 `Qt.WindowStaysOnTopHint` 플래그 적용.
  - (옵션) 설정 메뉴에서 토글 가능하도록 고려 (현재는 강제 적용).

### 2.2 입력 포커스 흐름 (Focus Flow Optimization)

- **목적**: 키보드만으로 배합 기록 전체 프로세스를 완료할 수 있도록 함.
- **시나리오**:
  1. **레시피 선택**: `RecipePanel` 콤보박스 선택 → **Enter**
  2. **배합량 입력**: `RecipePanel` 스핀박스로 포커스 이동 (`setFocus`).
     - 입력 시 기존 값 전체 선택 (`SelectAll`) 상태로 시작 (바로 덮어쓰기 가능).
  3. **자재 LOT 입력**: 배합량 입력 후 **Enter** → `MaterialTablePanel` 첫 번째 자재 LOT 셀로 이동.
  4. **테이블 내 이동**: `KeyHandlingTableWidget` (또는 이벤트 필터) 적용.
     - **Enter**: 현재 셀 수정 완료 → 다음 행 LOT 셀로 이동.
     - 마지막 행에서 **Enter**: 저장 버튼(`SaveBtn`)으로 포커스 이동 또는 저장 로직 활성화.

### 2.3 시각적 피드백 (Visual Feedback)

- **자재 LOT 셀 강조**:
  - 입력해야 할 핵심 필드인 '자재LOT' 컬럼(Col 5)의 배경색을 `#e3f2fd` (Light Blue)로 설정하여 시선을 유도.
- **완료 상태 피드백**:
  - 모든 필수 입력 완료 시 '저장' 버튼 활성화 및 색상 변경 (Disabled Gray → Active Green).

## 3. 구현 계획 (Implementation Plan)

### 3.1 MainWindow

- `Qt.WindowStaysOnTopHint` 플래그 추가.
- 패널 간 포커스 이동 시그널 연결 (`RecipePanel.amountEntered` → `MaterialTablePanel.focusFirstCell`).

### 3.2 RecipePanel

- `QSpinBox` 이벤트 필터링: FocusIn 이벤트 시 `selectAll()`.
- ReturnPressed 시그널 방출.

### 3.3 MaterialTablePanel

- `QTableWidget` 키 이벤트 재정의 (`KeyHandlingTableWidget` 대체 로직 확인).
- Enter 입력 시 다음 행 이동 로직 검증.

## 4. 검증 시나리오

1. 프로그램 실행 시 창이 다른 창라보다 위에 뜨는가?
2. 레시피 선택 후 탭/엔터로 배합량 입력창으로 바로 이동하는가?
3. 배합량 입력 후 엔터 시 첫 번째 자재 LOT로 이동하는가?
4. 마지막 자재 LOT 입력 후 엔터 시 저장이 가능한가?
