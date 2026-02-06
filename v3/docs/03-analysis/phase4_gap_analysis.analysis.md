# Phase 4 Gap Analysis Report

> **Summary**: Phase 4 (MainWindow Refactoring & UX Improvements) 설계 대비 구현 완료도 분석 및 Gap 식별
> **Author**: AI Assistant
> **Created**: 2026-01-31  
> **Last Updated**: 2026-02-04
> **Status**: Approved

---

## 1. 개요

Phase 4의 핵심 목표인 **MainWindow 리팩토링**과 **UX 개선** 작업이 설계 문서(`02-design/`)에 정의된 요구사항을 충족하는지 분석합니다.

- **기준 문서**:
  1. `mainwindow_refactor.design.md` (2026-01-31)
  2. `features/ux_improvements.design.md` (2026-01-31)
- **분석 대상**:
  - `ui/main_window.py`
  - `ui/panels/` (5개 패널)
  - `ui/controllers.py`
  - `ui/builders.py`

## 2. Gap Analysis Results

### 2.1 MainWindow Refactoring

| 요구사항 ID | 설계 내용                                                | 구현 상태 | Gap 유무 | 비고                               |
| ----------- | -------------------------------------------------------- | --------- | -------- | ---------------------------------- |
| **REF-01**  | **Monolithic 구조 탈피**: `_init_ui` 등 거대 메서드 분리 | ✅ 완료   | 없음     | 5개 Panel 클래스로 분리됨          |
| **REF-02**  | **Panel 분리**: `ScanEffectsPanel` 외 4개 패널 독립      | ✅ 완료   | 없음     | `ui/panels/` 패키지 구성           |
| **REF-03**  | **SRP 준수**: 비즈니스 로직(Table 처리 등) 위임          | ✅ 완료   | 없음     | `MaterialTablePanel`이 로직 담당   |
| **REF-04**  | **Class 삭제**: `KeyHandlingTableWidget` Main에서 제거   | ✅ 완료   | 없음     | Panel 내부 클래스로 이동           |
| **REF-05**  | **데이터 흐름**: `DataManager` 및 시그널 기반 통신       | ✅ 완료   | 없음     | `data_manager` 주입 및 Signal 연결 |
| **REF-06**  | **Orchestration 분리**: Save/Status/Recipe/Signals 컨트롤러 분리 | ✅ 완료 | 없음 | `controllers.py` 도입 |
| **REF-07**  | **UI 조립 분리**: 페이지 구성 로직 분리                  | ✅ 완료   | 없음     | `builders.py` 도입 |

### 2.2 UX Improvements

| 요구사항 ID | 설계 내용                                                       | 구현 상태 | Gap 유무 | 비고                                |
| ----------- | --------------------------------------------------------------- | --------- | -------- | ----------------------------------- |
| **UX-01**   | **창 최상위 고정**: `WindowStaysOnTopHint` 적용                 | ✅ 완료   | 없음     | `main_window.py` 적용 확인          |
| **UX-02**   | **입력 포커스 흐름**: Recipe(Enter) → Amount(Enter) → Table     | ✅ 완료   | 없음     | 시그널(`amountConfirmed`) 연결 완료 |
| **UX-03**   | **Table 네비게이션**: Enter로 다음 행 이동, 마지막 행 완료 처리 | ✅ 완료   | 없음     | `lastRowEnterPressed` 시그널 구현   |
| **UX-04**   | **시각적 피드백**: 자재 LOT 컬럼(`#e3f2fd`) 강조                | ✅ 완료   | 없음     | `MaterialTablePanel` 적용 확인      |
| **UX-05**   | **저장 포커스**: 테이블 입력 완료 시 저장 버튼 포커스           | ✅ 완료   | 없음     | Lambda 연결 완료                    |

## 3. 회귀 테스트 결과 (Regression Check)

- **기본 기능**: 앱 실행, 레시피 로드, 로트 자동 배정 정상 동작 확인.
- **연동성**: 각 패널 간 시그널(배합량 변경 → 이론량 재계산) 정상 동작 확인.
- **테스트 커버리지**: Unit/Integration Test 일부 확인 (단위 테스트 `tests.unit.test_data_manager` OK).  
  전체 회귀 테스트는 별도 실행 필요.

## 4. 결론 및 제언

- **Conclusion**: 설계와 구현 간 **주요 Gap 없음**. 컨트롤러/빌더 분리까지 반영됨.
- **Recommendation**:
  - 현재 상태에서 **배포(Phase 9)** 단계로 진행 가능합니다.
  - `.venv` 정리 및 빌드 프로세스 검증을 통해 최종 안정성을 확보할 것을 권장합니다.
