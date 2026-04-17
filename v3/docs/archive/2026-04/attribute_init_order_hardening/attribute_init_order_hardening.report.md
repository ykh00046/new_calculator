# PDCA #10 완료 보고서 — attribute_init_order_hardening

> **Author**: AI Assistant
> **Created**: 2026-04-17
> **Cycle**: PDCA #10 (Lightweight)
> **Status**: Completed (1커밋 핫픽스)
> **Feature**: MainWindow 속성 초기화 순서 경화

---

## 1. Overview

`run.bat` 기동 직후 `'MainWindow' object has no attribute 'sidebar_hover_controller'` AttributeError로 앱이 뜨지 않는 Critical 기동 장애를 1커밋으로 해결. 원인은 `MainWindow.__init__` 내 `setWindowFlags()` 등 Qt 이벤트 유발 연산이 `sidebar_hover_controller` 할당보다 먼저 실행되어, 서브클래싱된 `eventFilter`가 미할당 속성을 참조한 것.

근본 해결(순서 이동) + 방어(가드) 병행으로 동일 패턴 재발을 차단.

---

## 2. Goals vs Results

| 목표 | 결과 |
|---|---|
| 기동 시 AttributeError 제거 | ✅ 사용자 육안 확인 — "정상 가동하네" |
| 사이드바 호버 확장 동작 보존 | ✅ 기존 `init_behavior`/`set_enabled` 경로 불변 |
| 테스트 무회귀 | ✅ 33/33 pass (QT_QPA_PLATFORM=offscreen) |
| 경량 처리 (LOC ≤ 10, 1커밋) | ✅ +8/-4, 1커밋 |

---

## 3. Commit Log

| # | Commit | SHA |
|---|---|---|
| 1 | fix: guard MainWindow sidebar_hover_controller init order | `cc41093` |

---

## 4. Key Changes

### 4.1 `v3/ui/main_window.py` — 초기화 순서 이동
`SidebarHoverController(self)` 생성을 `super().__init__()` 직후로 상향. 생성자가 `config.sidebar_hover_expand` 플래그와 `QTimer(window)`만 의존하고 `navigationInterface` 등 아직 미생성 속성을 참조하지 않음을 확인 후 안전하게 이동.

```python
def __init__(self):
    super().__init__()
    # eventFilter가 super().__init__() 이후 Qt 내부 이벤트(setWindowFlags 등)에서
    # 선(先) 호출될 수 있어, 속성 미존재 AttributeError를 막기 위해 최우선 할당.
    self.sidebar_hover_controller = SidebarHoverController(self)
    ...
```

### 4.2 `v3/ui/main_window.py` — eventFilter 방어 가드
순서 이동만으로도 충분하지만, 향후 `super().__init__()` 내부 시점의 콜백까지 커버하기 위해 `getattr` 가드 추가.

```python
def eventFilter(self, obj, e):
    controller = getattr(self, "sidebar_hover_controller", None)
    if controller is not None:
        controller.handle_filter_event(obj, e)
    return super().eventFilter(obj, e)
```

---

## 5. Root Cause

Qt의 `setWindowFlags()`는 네이티브 윈도우를 재생성하며, 이 과정에서 `ShowEvent`·`PaintEvent`·`WinIdChangeEvent` 등이 이벤트 시스템을 통과한다. FluentWindow가 자기 자신에 설치한 이벤트 필터는 Python 메서드 디스패치 규칙상 서브클래스 override(`MainWindow.eventFilter`)를 호출하므로, 이 시점에 아직 정의되지 않은 `self.sidebar_hover_controller` 참조가 AttributeError를 일으켰다.

---

## 6. Metrics

| 지표 | 값 |
|---|---|
| 커밋 수 | 1 |
| 수정 파일 | 1 (`main_window.py`) |
| 추가/삭제 LOC | +8 / −4 |
| 테스트 | 33/33 (변경 없음) |
| 작업 시간 | 1 세션 (핫픽스 모드, ~10분) |
| 사용자 승인 모드 | 일괄 진행 (저위험 1커밋) |

---

## 7. Lessons Learned

1. **`super().__init__()` 이후 즉시 Qt 이벤트가 오버라이드된 메서드를 호출할 수 있음**
   - FluentWindow처럼 부모가 이벤트 필터를 자기 자신에 설치하는 구조에서는 서브클래스 `__init__`의 할당 순서가 안전성과 직결된다.
2. **getattr 가드는 공짜 보험**
   - 오버라이드된 이벤트 훅(`eventFilter`, `showEvent`, `resizeEvent` 등)에서 `self.xxx.something` 형태 참조 시 `getattr` 가드는 코드 비용이 낮고 방어력이 크다.
3. **PDCA #7에서 분리한 `SidebarHoverController`의 위치가 중요**
   - 책임 분리는 성공적이었으나, `__init__` 내 생성 시점이 원래 `eventFilter` 내 inline 처리보다 늦어졌다는 부작용을 이번에 확인. 향후 컨트롤러 추출 시 "생성 시점 = super().__init__() 직후"를 기본 관례로 한다.

---

## 8. Follow-ups

- 다른 오버라이드 이벤트 훅(`showEvent`, `resizeEvent`)에서 유사한 속성 의존 패턴이 없는지 **다음 PDCA 착수 전 grep 확인** 수준의 경량 점검
- 순서 이동과 가드 모두 유지 (한쪽만으로도 충족이지만, 이중 안전망 가치가 큼)

---

## 9. Archive

- 위치: `v3/docs/archive/2026-04/attribute_init_order_hardening/`
- 생성 문서: `attribute_init_order_hardening.plan.md`, `attribute_init_order_hardening.report.md` (경량 — Design/Analysis 생략)
- 다음 사이클 번호: **PDCA #11**
