# UI 구조 개선 및 사이드바 UX 개선 완료 보고서

> **Summary**: `v3`의 DHR 안정성 이슈 수정, UI 구조 리팩터링, 사이드바 아이콘/hover UX 개선, PySide6 UI 구조 리뷰 스킬 제작 및 전역 승격까지 완료한 작업 보고서
>
> **Author**: Codex
> **Created**: 2026-02-25
> **Last Modified**: 2026-02-25
> **Status**: Completed

---

## 1. 작업 범위 요약

이번 작업에서는 다음 4개 축을 묶어서 정리했습니다.

1. DHR 데이터 저장 안정성 및 입력 검증 강화
2. 테스트/헤드리스 환경 안정화
3. `v3/ui` 구조 리팩터링 (의존성/상태 공유/숨은 결합도 완화)
4. 사이드바 UX 개선 (아이콘 구분성 + hover 자동 펼침/접힘 옵션)

추가로, 반복 가능한 리뷰를 위해 프로젝트 전용 스킬(`pyside6-ui-architecture-review`)을 만들고 전역 로컬 스킬로 승격했습니다.

---

## 2. 주요 완료 사항

### 2.1 DHR 저장/입력 안정성 개선

#### 완료 항목
- 수동 DHR 입력 시 `product_lot` 중복 방지 강화
  - 저장 직전 중복 LOT 자동 재생성 로직 추가
  - DB 고유 인덱스 생성 시도(기존 중복 데이터가 있으면 경고 후 스킵)
- 수동 DHR 입력의 완전 빈 자재행 저장 방지
  - 수집 단계에서 빈 행 skip
  - 검증 기준을 "실제 입력된 자재 행" 기준으로 수정
- 저장 + 출력 비원자 흐름 개선
  - DB 저장 성공 후 PDF/Excel 출력 실패 시 `Partial Success`로 사용자에게 구분 안내
- 벌크 생성 비율 검증 강화
  - 잘못된 비율 입력을 `0.0`으로 자동 치환하지 않고 즉시 오류 처리
- 벌크 생성 시 export 실패 내역 분리 기록
  - DB 저장 유지 + export 실패 목록 추적 가능하게 개선

#### 관련 파일
- `v3/models/dhr_database.py`
- `v3/ui/panels/manual_input_interface.py`
- `v3/models/dhr_bulk_generator.py`
- `v3/ui/panels/bulk_creation_interface.py`
- `v3/utils/bulk_helpers.py`

---

### 2.2 테스트/헤드리스 환경 안정화

#### 완료 항목
- 로거 파일 핸들러 실패 시 콘솔 로깅으로 fallback (import 단계 크래시 방지)
- `PySide6` 미설치 환경에서 `error_handler`가 GUI 없이 로깅 fallback 하도록 보완
- `Config.get()` 반환값(dict/list) deep copy 처리로 내부 설정 객체 변이 누수 방지

#### 관련 파일
- `v3/utils/logger.py`
- `v3/utils/error_handler.py`
- `v3/config/config_manager.py`

---

### 2.3 UI 구조 리팩터링 (`v3/ui`)

#### 완료 항목
- `MainWindow` 서비스 생성 중앙화 (`AppServices`)
  - `DataManager`, `DhrDatabaseManager`, `LotManager` 1회 생성 후 공유
- DHR 패널 생성자 DI 지원(과도기 호환)
  - 수기/일괄/레시피 관리 화면이 공유 매니저를 주입받도록 변경
- `builders.py`의 숨은 `window.*` 직접 주입 제거
  - `build_mixing_page()` -> `MixingPageRefs` 반환
  - `build_dashboard_page()`/`create_kpi_row()` -> `DashboardPageRefs` 반환
- `MainWindow.statusBar()` 오버라이드 제거
  - 믹싱 페이지 상태바를 명시 속성으로 사용
- `save_btn.click()` 우회 호출 제거
  - 명시 핸들러 경로로 저장 호출
- DHR 설정 패널 상태 동기화
  - 메인/수기/일괄 페이지의 `ScanEffectsPanel`, `SignaturePanel` 값 동기화

#### 관련 파일
- `v3/ui/main_window.py`
- `v3/ui/builders.py`
- `v3/ui/panels/manual_input_interface.py`
- `v3/ui/panels/bulk_creation_interface.py`
- `v3/ui/panels/recipe_management_interface.py`
- `v3/ui/panels/scan_effects_panel.py`
- `v3/ui/panels/signature_panel.py`

---

### 2.4 프로젝트 전용 UI 구조 리뷰 스킬 제작 및 승격

#### 생성한 스킬 (워크스페이스)
- `skills/pyside6-ui-architecture-review/SKILL.md`
- `skills/pyside6-ui-architecture-review/references/checklist.md`
- `skills/pyside6-ui-architecture-review/references/patterns.md`
- `skills/pyside6-ui-architecture-review/references/refactor-order.md`
- `skills/pyside6-ui-architecture-review/references/visual-smoke.md`
- `skills/pyside6-ui-architecture-review/scripts/ui_structure_scan.ps1`

#### 전역 로컬 스킬 승격
- 설치 경로: `C:\Users\interojo\.codex\skills\pyside6-ui-architecture-review`

#### 스킬 기반 점검 효과
- `builders.py`의 `window.*` 숨은 변형 탐지/제거
- `MainWindow.statusBar()` 오버라이드 제거 확인
- `save_btn.click()` 우회 이벤트 경로 제거 확인

---

### 2.5 사이드바 UX 개선 (아이콘 + Hover 옵션)

#### 완료 항목
- 사이드바 아이콘 재배치로 구분성 개선
  - `배합`, `수기 입력`, `일괄 생성`, `DHR 관리` 아이콘 분리
- 설정 페이지에 사이드바 hover 옵션 추가
  - 체크박스 + 툴팁 설명 문구 정리
- hover 자동 펼침/자동 접힘 구현
  - 접힌 상태에서 hover 시 펼침
  - 벗어나면 지연 후 자동 접힘
  - 옵션 OFF 시 기존 동작 유지

#### 버그 수정 (실사용 검증 중 발견)
- 자동 접힘 타이머가 hover polling에 의해 계속 리셋되어 접히지 않던 버그 수정
  - 원인: `120ms` polling이 `220ms` single-shot collapse timer를 매번 `start()`
  - 조치: timer active 상태에서는 재시작하지 않도록 변경
- hover 판정 범위/조건 보완
  - `displayMode` 단일 조건 의존 완화
  - 사이드바 하위 위젯 `underMouse()` 기반 판정 + 좌표 fallback

#### 최종 UX 조정
- 자동 접힘 지연 시간: `220ms -> 200ms` (소폭 단축)

#### 관련 파일
- `v3/ui/main_window.py`
- `v3/ui/builders.py`
- `v3/config/config_manager.py`

---

## 3. 검증 내역

### 3.1 테스트/실행 검증
- `pytest v3/tests/unit/test_config_manager.py v3/tests/unit/test_data_manager.py -q` 통과 (`11 passed`)
- 변경 파일 `compileall` 반복 검증 통과
- 오프스크린(`QT_QPA_PLATFORM=offscreen`) 기준 `MainWindow` 생성 스모크 테스트 통과
- DHR 설정 패널 동기화 스모크 테스트 통과 (메인/수기/일괄 값 동기화 확인)
- 사이드바 hover 로직 스모크 테스트 통과 (메서드 경로/타이머 경로 확인)

### 3.2 사용자 실사용 확인
- `사이드바 hover 자동 펼침`: 동작 확인
- `사이드바 hover 후 자동 접힘`: 지연 후 동작 확인

---

## 4. 현재 상태 (마무리 기준)

### 완료된 핵심 문제
- DHR 수동 입력 중복 LOT/빈 자재행 저장 위험 완화
- 벌크 비율 입력 검증 강화
- 저장 후 출력 실패 시 사용자 혼란 감소(부분 성공 처리)
- 로거/에러핸들러의 헤드리스 환경 import 안정성 개선
- UI 구조의 숨은 결합도 감소 (`builders -> refs`, `AppServices`, 명시 이벤트 경로)
- 사이드바 아이콘 식별성 개선
- 사이드바 hover UX 옵션 동작 완료

### 남은 비치명(후속 개선 후보)
- 일부 패널의 `QMessageBox + 비즈니스 로직` 결합 (`MaterialTablePanel` 등)
- DHR 패널 생성자 fallback DI (`or manager()` 패턴) 정리
- 실제 사용자 플로우 전체 클릭 스모크(수기 저장/일괄 생성 end-to-end) 추가

---

## 5. 변경 파일 목록 (요약)

### 데이터/모델/유틸
- `v3/models/dhr_database.py`
- `v3/models/dhr_bulk_generator.py`
- `v3/utils/bulk_helpers.py`
- `v3/utils/logger.py`
- `v3/utils/error_handler.py`
- `v3/config/config_manager.py`

### UI 구조/패널/UX
- `v3/ui/main_window.py`
- `v3/ui/builders.py`
- `v3/ui/panels/manual_input_interface.py`
- `v3/ui/panels/bulk_creation_interface.py`
- `v3/ui/panels/recipe_management_interface.py`
- `v3/ui/panels/scan_effects_panel.py`
- `v3/ui/panels/signature_panel.py`

### 스킬(프로젝트 전용 + 전역 승격)
- `skills/pyside6-ui-architecture-review/*` (워크스페이스 생성)
- `C:\Users\interojo\.codex\skills\pyside6-ui-architecture-review/*` (전역 설치)

---

## 6. 버전 이력

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-25 | 초기 작성 (DHR 안정성 + UI 구조 + 사이드바 UX + 스킬 승격 작업 정리) | Codex |

