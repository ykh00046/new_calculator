# Mixing Improvements Design

Author: Codex  
Status: Draft  
Last Updated: 2026-02-05

## 1. Overview
This design updates the Mixing workflow per review findings:
1) Work time is disabled by default and only included when the user opts in.  
2) LOT auto-assign validates the work date and fails safely with user feedback.  
3) Post-save reset behavior is clearer to prevent accidental repeat saves.  
4) Validation includes actual-amount rules (non-empty, numeric, > 0).

## 2. Current Behavior (Summary)
- Work time always stored in DB; include flag exists but not enforced.
- Auto-assign assumes valid work date; logs warnings if lots missing.
- Save clears materials table only; recipe/amount remain.
- Validation checks LOT presence only (actual amount may be empty/0).

## 3. Target Behavior
### 3.1 Work Time (Opt-in)
- Default: unchecked “작업시간 포함”.
- When unchecked:
  - work_time stored as empty string (or None) and excluded from exports.
- When checked:
  - work_time stored normally.

### 3.2 Auto-Assign Date Validation
- If work_date is empty/invalid:
  - Block auto-assign.
  - Show warning: “작업일자를 먼저 확인하세요.”
- If valid but no lots found:
  - Warn with count (0 assigned) and keep existing lot inputs.

### 3.3 Post-Save Reset
Two modes (configurable):
1. Safe Reset (Default)  
   - Clear materials table + clear recipe selection + set amount to 0.  
   - Keep work date/worker.
2. Repeat Mode  
   - Clear materials only (current behavior).

### 3.4 Actual Amount Validation
For each material row:
- actual_amount must be numeric and > 0.  
- If empty or 0 -> validation error: “실제 배합량을 입력하세요.”

## 4. Implementation Plan (Mapping)
### 4.1 Work Time
Update v3/ui/panels/work_info_panel.py
- Default checkbox unchecked.
- Provide include_time in get_data() (already exists).

Update v3/models/data_manager.py
- In save_record, if include_work_time is false, persist empty work_time.
- Ensure exporters respect empty work time (already downstream parameter).

Update v3/ui/controllers.py
- SaveController._collect_payload already passes include_work_time.
- Ensure DataManager.save_record uses this flag.

### 4.2 Auto-Assign Validation
Update v3/ui/panels/material_table_panel.py
- Guard clause: if work_date invalid -> show warning and return.
- Use a small helper is_valid_date(work_date) (local or DataManager).

### 4.3 Post-Save Reset
Update v3/ui/main_window.py
- Add config toggle (e.g., config.save_reset_mode) with default safe.
- After save, call recipe_panel.reset() and recipe_panel.reset_amount() when in safe mode.

### 4.4 Actual Amount Validation
Update v3/models/data_manager.py
- Extend validate_record_inputs:
  - Check actual_amount per row.
  - Return specific error message.

## 5. Edge Cases
- Work time disabled but work_time field still has UI value: should be ignored.
- Auto-assign called with empty table: no-op but no error.
- Validation should allow actual_amount with decimals.

## 6. Test Matrix (Manual)
1. Work time unchecked -> save -> DB work_time empty.
2. Work time checked -> save -> DB work_time present.
3. Auto-assign with missing date -> warning only, no changes.
4. Auto-assign with valid date but no lots -> warning.
5. Save with any row actual_amount empty/0 -> blocked.
6. Save success -> reset mode behavior confirmed.
