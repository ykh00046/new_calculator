# MainWindow Refactoring Design

> **Target Component**: `v3/ui/main_window.py`
> **Goal**: Break down the monolithic `MainWindow` class into smaller, manageable components (Panels) following the Single Responsibility Principle (SRP).
> **Related Task**: Medium Priority - MainWindow Refactoring

---

## 1. Problem Analysis

### Current State

- **Size**: 712 LOC (Lines of Code)
- **Complexity**: High complexity with mixed responsibilities.
- **Responsibilities**:
  - UI Layout & Initialization (Tabs, Toolbars, Layouts)
  - Business Logic (Recipe loading, Calculation, Validation)
  - Data Persistence (Saving to DB)
  - External Output (Excel Export, PDF Generation, Image Processing)
  - Configuration Management (Scan effects, Google Sheets)
  - Event Handling (Signal/Slots for all widgets)

### Issues

- **Poor Maintainability**: Modification in one area (e.g., UI layout) risks breaking unrelated logic (e.g., calculation).
- **Low Reusability**: Widgets are tightly coupled to the main window logic.
- **Testing Difficulty**: Hard to unit test specific logic (e.g., calculation) without instantiating the entire window.

---

## 2. Proposed Architecture

### 2.1 Component Decomposition

The `MainWindow` is refactored into a **Controller-View** pattern where `MainWindow` acts as the Coordinator and **Panel classes** handle specific UI sections and their immediate interactions.

Additional separation applied:

- **Builders** (`ui/builders.py`): page composition and UI assembly
- **Controllers** (`ui/controllers.py`): flow orchestration for recipes, save, status, and signal binding

| New Component            | Responsibility                                                                                                           | Source UI Components                                                     |
| :----------------------- | :----------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------- |
| **`MainWindow`**         | **Coordinator**. Assembles panels, handles inter-panel communication, executes high-level business logic (Save, Export). | `QMainWindow`, `QToolBar`, `QTabWidget` (container)                      |
| **`RecipePanel`**        | **Recipe Management**. Selects recipe, sets amount, calculates theory amount.                                            | `recipe_combo`, `amount_spin`                                            |
| **`WorkInfoPanel`**      | **Work Context**. Manages date, time, and worker selection.                                                              | `date_edit`, `time_edit`, `chk_include_time`, `worker` logic             |
| **`MaterialTablePanel`** | **Data Entry**. Displays materials, handles LOT input/auto-assignment, table interactions.                               | `table` (`KeyHandlingTableWidget`), `assign_lot_btn`, `clear_btn`        |
| **`ScanEffectsPanel`**   | **Configuration**. Manages PDF scan effect parameters.                                                                   | Spins (`dpi`, `blur`, `noise`, `contrast`, `brightness`), Effect Buttons |
| **`SignaturePanel`**     | **Configuration**. Manages signature inclusion options.                                                                  | Checkboxes (`chk_charge`, `chk_review`, `chk_approve`)                   |

#### Supporting Components (Implemented)

| Component                  | Responsibility                                                                 |
| :------------------------- | :---------------------------------------------------------------------------- |
| **`RecipeController`**     | Load recipes, handle recipe change flow, delegate to panels                   |
| **`SaveController`**       | Validate inputs, collect payload, call `DataManager.save_record`              |
| **`StatusController`**     | Status bar messages and Google Sheets backup status                           |
| **`PanelSignalBinder`**    | Centralized signal-slot wiring between panels and MainWindow                  |
| **`builders.py`**          | Build `Dashboard`, `Mixing`, `Settings` pages and KPI cards                   |

### 2.2 Directory Structure

```
v3/ui/
├── panels/                 # [NEW]
│   ├── __init__.py
│   ├── base_panel.py       # (Optional) Shared interface
│   ├── recipe_panel.py
│   ├── work_info_panel.py
│   ├── material_table_panel.py
│   ├── scan_effects_panel.py
│   └── signature_panel.py
├── controllers.py          # [NEW] Recipe/Save/Status/Signals
├── builders.py             # [NEW] UI composition helpers
├── main_window.py          # [MODIFIED] Drastically reduced
└── ...
```

---

## 3. Data Flow & Communication

### Signal-Slot Strategy

1.  **Downstream (Main -> Panel)**: `MainWindow` calls public methods on Panels to set data (e.g., `material_panel.set_data(recipe_items)`).
2.  **Upstream (Panel -> Main)**: Panels emit custom PyQT Signals when critical state changes (e.g., `RecipePanel.amountChanged`). `MainWindow` connects to these signals.

### Example Flows

#### Scene 1: Recipe Selection

1.  User selects recipe in `RecipePanel`.
2.  `RecipePanel` emits `recipeChanged(recipe_name)`.
3.  `RecipeController` catches signal.
4.  `RecipeController` retrieves recipe data from `DataManager`.
5.  `RecipeController` calls `material_panel.load_items(items)`.

#### Scene 2: Theory Calculation

1.  User changes amount in `RecipePanel`.
2.  `RecipePanel` emits `amountChanged(new_amount)`.
3.  `MainWindow` catches signal.
4.  `MainWindow` calls `material_panel.update_theory_amounts(new_amount)`.
    - _Alternative_: Pass `amount` to `material_panel` directly if logic is simple.

#### Scene 3: Save Record

1.  User clicks "Save" toolbar action in `MainWindow`.
2.  `SaveController` acts as orchestrator:
    - `recipe_data` = `recipe_panel.get_data()`
    - `work_data` = `work_info_panel.get_data()`
    - `table_data` = `material_panel.get_data()`
    - `effect_data` = `scan_effects_panel.get_data()`
    - `sig_data` = `signature_panel.get_data()`
3.  `SaveController` validates aggregated data.
4.  `SaveController` calls `DataManager.save_record(...)`.

---

## 4. Implementation Steps

### Phase 1: Preparation

1.  Create `ui/panels/` directory.
2.  Create empty files for each panel.

### Phase 2: Migration (Iterative)

- **Step 1**: Move **Scan Effects & Signature** logic. (Least dependencies, easiest to isolate).
  - Create `ScanEffectsPanel` & `SignaturePanel`.
  - Move `_get_scan_effects_params`, `_reset_scan_effects_defaults`, `_save_scan_effects_as_default`.
  - Integrate into `MainWindow`.
- **Step 2**: Move **Work Info** logic.
  - Create `WorkInfoPanel`.
  - Move date/time/worker UI code.
- **Step 3**: Move **Recipe** logic.
  - Create `RecipePanel`.
  - Move `_load_recipes`, `_on_recipe_changed` (UI part only).
- **Step 4**: Move **Material Table** logic. (Most complex).
  - Create `MaterialTablePanel`.
  - Move `KeyHandlingTableWidget` class (or keep in components).
  - Move `_recalc_theory`, `auto_assign_lots`, `_on_cell_changed`.

### Phase 3: Cleanup

1.  Remove unused imports and methods from `MainWindow`.
2.  Verify TAB order and focus chains.
3.  Verify all shortcuts (`Ctrl+S`, `Ctrl+R`) still work via Controller delegation.

## 5. Risk Management

- **Regression**: UI logic extraction might break implicit dependencies (e.g., `self.amount_spin` used in table method).
  - _Mitigation_: Pass necessary data explicitly via method arguments or signals, avoiding direct access to other panels' widgets.
- **Event Handling**: KeyPress events or Focus events might behave differently after reparenting.
  - _Mitigation_: Test `KeyHandlingTableWidget` behavior specifically after move.

## 6. Verification Plan

1.  **Visual Check**: Layout should look identical to current version.
2.  **Functional Check**:
    - Recipe change -> Table update.
    - Amount change -> Theory calculation update.
    - Lot Auto Assign -> Working correctly with date.
    - Save/Export -> Data correctness.
3.  **Code Check**: `MainWindow` LOC should drop below 300.

---

## 7. Post-Refactor Additions

리팩토링 이후 Mixing/Manual/Bulk 3개 패널 간 사용자 경험 일관성을 위해 다음 동작을 MainWindow가 조정한다.

### 7.1 DHR UI Settings 3-Way Sync

**Goal**: `scan_effects`(DPI/noise/blur/contrast/brightness)와 `signature`(결재 3종 체크박스) 설정을 3개 탭에서 실시간으로 동기화한다.

**Components**:

- `DhrUiSettingsState` (dataclass): 현재 활성 설정 보관
- `MainWindow._setup_dhr_settings_sync`: 진입 시 바인딩 수행
- `MainWindow._bind_dhr_settings_pair`: 각 `(scan_panel, signature_panel)` 쌍에 대해 valueChanged/toggled 시그널 연결
- `MainWindow._apply_dhr_settings_to_all`: 재진입 방지 플래그(`_dhr_settings_syncing`)로 무한 루프 차단

**Pairs managed**:

1. `self.scan_effects_panel` + `self.signature_panel` (Mixing 탭)
2. `manual_interface.scan_effects_panel` + `manual_interface.signature_panel`
3. `bulk_interface.scan_effects_panel` + `bulk_interface.signature_panel`

**Rationale**: 사용자가 한 탭에서 효과/서명 설정을 바꾸면 다른 탭의 입력에도 동일하게 적용되어야 한다. 탭마다 별도 입력을 허용할 경우 최종 PDF 출력 결과가 일관되지 않는다.

### 7.2 Table Edit Auto-Save

**Goal**: `MaterialTablePanel`의 마지막 셀 편집 완료 시 자동 저장을 트리거한다.

**Implementation**:

- `PanelSignalBinder`에서 `on_table_edit_finished` 콜백 등록
- `MainWindow._handle_table_edit_finished`: `save_btn.isEnabled()` 체크 후 `_save_record()` 호출
- Save 버튼 경로(`Ctrl+S`, 버튼 클릭)와 동일한 검증/저장 로직을 재사용 — 별도 우회 경로 금지

**Rationale**: 작업자가 마지막 자재 입력 후 저장 버튼을 놓치는 실수를 방지한다. 저장 가능 상태(`isEnabled`) 조건 하에서만 실행되므로 불완전 저장 위험은 없다.

### 7.3 LOC Target — Resolved in PDCA #7

- 당초: 7.1/7.2 동작 추가로 `MainWindow`는 300 LOC 목표 미달성 상태(~675 LOC).
- **해소**: PDCA #7 (#7a~#7f)에서 6회 하위 사이클로 **291 LOC** 달성 (-57%).
- 추출된 컨트롤러/모듈:
  - `DhrSettingsSyncController` (`ui/controllers.py`) — PDCA #7b
  - `SidebarHoverController` (`ui/sidebar_hover_controller.py`) — PDCA #7c
  - `register_sidebar_interfaces`, `setup_statusbar` (`ui/builders.py`) — PDCA #7d/#7f
  - `notifications` 모듈 (`ui/notifications.py`) — PDCA #7e
- 참조: `mainwindow_loc_reduction.design.md`, `docs/04-report/features/pdca_cycle_07_mainwindow_loc_reduction.report.md`.
