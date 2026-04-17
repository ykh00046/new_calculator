# Attribute Init Order Hardening — Plan

> **Author**: AI Assistant
> **Created**: 2026-04-17
> **Status**: Plan (Lightweight PDCA)
> **Cycle**: PDCA #10
> **Parent**: PDCA #9 completion (release pipeline)

---

## 1. Overview & Purpose

### 1.1 배경
사용자가 `run.bat` (→ `run_dev.bat` → 소스 실행)으로 앱을 기동한 직후 다음 오류 팝업을 보고했다.

```
오류 유형: AttributeError
오류 내용: 'MainWindow' object has no attribute 'sidebar_hover_controller'
```

`v3/main.py:46`에서 `MainWindow()` 생성 시 `__init__` 내부의 예외가 `except Exception as e` 블록(main.py:49-52)에 잡혀 "메인 윈도우 초기화 실패" 팝업으로 표시된 상황. 앱 기동 자체가 불가능.

### 1.2 원인 분석
`v3/ui/main_window.py:48-62`의 초기화 순서:

```
49: super().__init__()          # FluentWindow가 MainWindow.eventFilter 참조 확보
52: setTheme(Theme.DARK)
54-55: setWindowTitle, resize
57-58: setWindowFlags(... | WindowStaysOnTopHint)  ★ 네이티브 윈도우 재생성
60-61: services / data_manager
62: self.sidebar_hover_controller = SidebarHoverController(self)
```

`setWindowFlags()`는 Qt 내부에서 윈도우 핸들을 재생성하며 ShowEvent/PaintEvent 등을 발생시킨다. FluentWindow가 자기 자신에 설치한 이벤트 필터가 서브클래스의 `eventFilter`(main_window.py:100-102)를 호출하면, 그 시점에는 `self.sidebar_hover_controller`가 아직 미할당 상태 → AttributeError.

### 1.3 목적
기동 시 AttributeError를 제거하고, 향후 유사한 "속성 미초기화 시점 이벤트" 패턴에 방어적으로 대응한다.

---

## 2. Scope

### 2.1 In-Scope
- `v3/ui/main_window.py`:
  - `SidebarHoverController` 생성을 `super().__init__()` 직후로 이동 (근본 해결)
  - `eventFilter`에 `getattr` 가드 추가 (이중 안전망)
- 회귀 검증: `python v3/tests/run_tests.py` 33/33 통과

### 2.2 Out-of-Scope
- 다른 컨트롤러(`RecipeController`, `PanelSignalBinder` 등)의 초기화 순서 점검 — 현재 이슈 없음
- `super().__init__()` 이전 속성 정의 표준화 가이드 — 별도 PDCA로 다룰 여지

---

## 3. Requirements

### 3.1 Functional
1. `run.bat` 기동 시 AttributeError 없이 메인 윈도우 표시
2. 기존 사이드바 호버 확장 동작 보존
3. 기존 이벤트 필터 동작 보존

### 3.2 Non-Functional
- Python 3.9 호환성 유지
- 테스트 33/33 무회귀
- 수정 LOC ≤ 10 (경량 핫픽스)

---

## 4. Risks

| 리스크 | 영향 | 완화 |
|---|---|---|
| `SidebarHoverController.__init__`이 `window.navigationInterface` 등 아직 미생성 속성에 의존할 경우 | Medium | 컨트롤러 생성자 검토 — `config.sidebar_hover_expand`와 `QTimer(window)`만 사용, 안전 확인 완료 |
| `eventFilter` 가드가 필터 호출을 삼켜 동작 누락 | Low | `getattr` 반환 None 케이스만 `handle_filter_event` 스킵, `super().eventFilter` 호출은 유지 |

---

## 5. Plan Steps

1. **수정** — `main_window.py` 2곳
2. **테스트** — `QT_QPA_PLATFORM=offscreen python v3/tests/run_tests.py` (33/33 기준)
3. **커밋** — `fix: guard MainWindow sidebar_hover_controller init order`
4. **사용자 기동 확인** — `run.bat` 정상 기동 여부 육안 확인
5. **문서화** — 본 Plan + Report (경량, Design/Analysis 생략)

---

## 6. Success Criteria (DoD)

- [x] 앱 기동 시 AttributeError 미발생
- [x] 사이드바 호버 확장 기능 정상 동작
- [x] 테스트 33/33 통과
- [x] 1커밋으로 종결 (저위험, 일괄 진행 모드)
