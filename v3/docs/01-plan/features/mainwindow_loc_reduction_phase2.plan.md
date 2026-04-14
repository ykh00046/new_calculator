# MainWindow LOC Reduction Phase 2 Plan

> **Summary**: SidebarHoverController 추출로 MainWindow 추가 슬림화
>
> **Author**: AI Assistant
> **Created**: 2026-04-14
> **Status**: Approved

---

## Overview

PDCA #7b 후속 사이클. `main_window.py`(624 LOC)에서 가장 큰 SRP 위반 블록인 사이드바 호버 동작(약 160줄)을 전담 컨트롤러로 이관한다.

## Scope

### In Scope

`ui/sidebar_hover_controller.py` 신규 생성, 다음 항목 이관:

- 상태 변수: `_sidebar_hover_expand_enabled`, `_nav_hover_expanded`, `_nav_hover_collapse_timer`, `_nav_hover_poll_timer`, `_nav_hover_filter_widgets`
- 메서드: `_init_sidebar_hover_behavior`, `_on_sidebar_hover_enter`, `_on_sidebar_hover_leave`, `_is_cursor_in_sidebar`, `_poll_sidebar_hover_state`, `_collapse_navigation_after_hover`

MainWindow 잔존:
- `is_sidebar_hover_expand_enabled`, `_set_sidebar_hover_expand_enabled` (thin delegate — `builders.py` hasattr 호환)
- `eventFilter` (Qt 요구사항 — 컨트롤러에 위임 후 `super()` 체인)
- `_init_sidebar_hover_behavior` (thin delegate)

### Out of Scope

- Save 핸들러 이관 (다음 사이클)
- Google Sheets 백업 초기화 이관

## Target

- LOC: 624 → ~490 (약 -134줄)
- 300 LOC 목표까지 잔여 약 190줄 → 2~3회 추가 사이클 예상

## Success Criteria

- `tests/run_tests.py` 27/27 통과
- `builders.py`의 `hasattr(window, "is_sidebar_hover_expand_enabled")` 경로 유지
- 사이드바 호버 확장/축소 동작 유지(수동 검증 권장)

## Risks

- **eventFilter 위임 누락 시 Qt 메시지 루프 영향**
  - 대응: MainWindow.eventFilter 내 `handle_filter_event` 호출 + `super().eventFilter()` 체인 보장
- **타이머 소유권**
  - 대응: `QTimer` 생성 시 parent를 MainWindow로 지정(메모리 누수 방지)
