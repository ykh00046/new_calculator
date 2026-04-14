# MainWindow LOC Reduction Plan

> **Summary**: MainWindow LOC 축소 (675 → <300) 리팩토링 계획
>
> **Author**: AI Assistant
> **Created**: 2026-04-14
> **Last Modified**: 2026-04-14
> **Status**: Approved

---

## Overview & Purpose

- `mainwindow_refactor.design.md` §6에 명시된 "MainWindow LOC should drop below 300" 목표를 달성한다.
- 현재 LOC: 675줄 (목표 대비 +375줄 초과).
- PDCA #7a에서 문서화된 후처리 추가 기능(DHR 3-way sync, 테이블 자동저장)이 MainWindow 비대화의 주요 원인.

## Scope

### In Scope (이번 사이클)

- `DhrSettingsSyncController` 추출: DHR 설정 3-way sync 로직을 별도 컨트롤러로 이관
  - `DhrUiSettingsState` dataclass (60-64줄)
  - `_setup_dhr_settings_sync` (447-463줄)
  - `_bind_dhr_settings_pair` (465-482줄)
  - `_apply_dhr_settings_to_all` (484-494줄)
  - `_on_scan_effects_panel_changed` (496-500줄)
  - `_on_signature_panel_changed` (502-506줄)

### Out of Scope (다음 사이클 후보)

- `_connect_panel_signals` 블록 추가 슬림화
- Save/Export 핸들러 로직 `SaveController` 완전 이관
- 수기/일괄 인터페이스 위임 코드 `InterfaceRegistry` 통합

## Requirements

### Functional

- 리팩토링 전후 동작 완전 동일 (DHR 설정이 3개 탭에서 동기화됨)
- `PanelSignalBinder` API 변경 없음
- 기존 테스트(27개) 전부 통과

### Non-Functional

- MainWindow LOC: 675 → ~615 (약 60줄 감소)
- 단일 책임 원칙 준수: MainWindow는 조정자, 컨트롤러는 동기화 로직
- Python 3.9 호환 유지

## Success Criteria

- `v3/tests/run_tests.py` 27/27 통과
- MainWindow에서 `DhrUiSettingsState`, `_setup_dhr_settings_sync` 등 6개 항목 제거 확인
- `controllers.py`에 `DhrSettingsSyncController` 신규 클래스 추가

## Risks & Mitigation

- **재진입 방지 플래그(`_dhr_settings_syncing`) 동작 변경 위험**
  - 대응: 상태 변수를 컨트롤러 내부로 캡슐화, 기존 로직 그대로 이관
- **시그널 연결 누락**
  - 대응: 3개 쌍(Mixing/Manual/Bulk) 바인딩을 리스트로 명시, `setup()` 호출 1회 보장
- **GUI 런타임 회귀**
  - 대응: 단위 테스트 우선 실행, 수동 검증은 별도 QA 단계

## Related Documents

- Design: [../../02-design/mainwindow_loc_reduction.design.md](../../02-design/mainwindow_loc_reduction.design.md)
- Parent: [../../02-design/mainwindow_refactor.design.md](../../02-design/mainwindow_refactor.design.md) §7.3
