# MainWindow LOC Reduction Design

> **Summary**: DhrSettingsSyncController 추출로 MainWindow 슬림화
>
> **Author**: AI Assistant
> **Created**: 2026-04-14
> **Status**: Approved

---

## 1. Target

`ui/main_window.py`에서 DHR 설정 동기화 관련 코드 블록을 `ui/controllers.py`의 신규 `DhrSettingsSyncController`로 이관한다.

## 2. Proposed Component

### `DhrSettingsSyncController`

```python
class DhrSettingsSyncController:
    def __init__(self, pairs: List[Tuple[ScanEffectsPanel, SignaturePanel]]) -> None:
        self._pairs = pairs
        self._syncing = False
        first_scan, first_sig = pairs[0]
        self._state = DhrUiSettingsState(
            scan_effects=dict(first_scan.get_data()),
            signature=dict(first_sig.get_data()),
        )

    def setup(self) -> None:
        for scan_panel, signature_panel in self._pairs:
            self._bind_pair(scan_panel, signature_panel)
        self._apply_to_all()

    def _bind_pair(self, scan_panel, signature_panel) -> None:
        ...  # 기존 _bind_dhr_settings_pair 로직 그대로

    def _apply_to_all(self) -> None:
        ...  # 기존 _apply_dhr_settings_to_all 로직 그대로

    def _on_scan_changed(self, source_panel) -> None: ...
    def _on_sig_changed(self, source_panel) -> None: ...
```

- `DhrUiSettingsState` dataclass는 MainWindow → `controllers.py`로 이동
- 재진입 플래그 `_syncing`은 컨트롤러 내부 상태로 캡슐화

## 3. MainWindow Changes

### Before (675 LOC)

```python
class DhrUiSettingsState: ...  # 60-64줄

class MainWindow(FluentWindow):
    def _setup_dhr_settings_sync(self): ...       # 447-463
    def _bind_dhr_settings_pair(self, ...): ...   # 465-482
    def _apply_dhr_settings_to_all(self): ...     # 484-494
    def _on_scan_effects_panel_changed(self): ... # 496-500
    def _on_signature_panel_changed(self): ...    # 502-506
```

### After (~615 LOC)

```python
from ui.controllers import DhrSettingsSyncController  # 신규 임포트

class MainWindow(FluentWindow):
    def _setup_dhr_settings_sync(self) -> None:
        pairs = [
            (self.scan_effects_panel, self.signature_panel),
            (self.manual_interface.scan_effects_panel, self.manual_interface.signature_panel),
            (self.bulk_interface.scan_effects_panel, self.bulk_interface.signature_panel),
        ]
        self.dhr_settings_sync_controller = DhrSettingsSyncController(pairs)
        self.dhr_settings_sync_controller.setup()
```

MainWindow에는 컨트롤러 인스턴스화 + `setup()` 호출만 남음 (~10줄).

## 4. Public API

- `DhrSettingsSyncController(pairs)`
- `.setup()` — 시그널 바인딩 + 초기 상태 적용
- `.state` (property, 선택적) — 현재 `DhrUiSettingsState` 접근

## 5. Test Plan

- 기존 `tests/run_tests.py` 27건 회귀 통과 필수
- `test_panels.py`에 영향 없음 (패널 API 불변)
- 신규 유닛 테스트: 선택적 (GUI 의존성으로 통합 테스트 대체 가능)

## 6. Verification

1. **Import Check**: `controllers.py` 임포트 정상
2. **Regression**: 27/27 테스트 통과
3. **LOC Check**: `wc -l main_window.py` < 620
4. **Runtime Smoke**: (권장) 앱 실행 후 DHR 설정을 한 탭에서 바꿔 다른 탭에 반영되는지 수동 확인

## 7. Rollback Plan

문제 발생 시 단일 커밋 revert로 원복 가능 (`git revert HEAD`).

## Related Documents

- Plan: [../01-plan/features/mainwindow_loc_reduction.plan.md](../01-plan/features/mainwindow_loc_reduction.plan.md)
- Parent: [mainwindow_refactor.design.md](./mainwindow_refactor.design.md) §7.3
