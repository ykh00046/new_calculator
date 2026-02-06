# Gap Analysis: INFO-level 5 Issues Fix

> PDCA Check Phase - Design vs Implementation Comparison

---

## Analysis Summary

| Metric | Value |
|--------|-------|
| Analysis Date | 2026-02-07 |
| Feature | INFO-level 5 issues fix (code quality PDCA cycle #2) |
| Total Items Checked | 22 |
| Items Matched | 22 |
| Gaps Found | 0 |
| **Match Rate** | **100%** |

---

## Issue-by-Issue Results

### Issue 1: settings.py BOM + Mojibake (HIGH) - 6/6 items

| # | Plan Item | Status |
|---|-----------|--------|
| 1 | BOM removed from settings.py | PASS |
| 2 | All mojibake Korean comments restored | PASS |
| 3 | CELL_MAPPING excessive blank lines removed | PASS |
| 4 | PEP 8 spacing applied | PASS |
| 5 | data_manager.py line 202 mojibake fixed (`"배합 저장"`) | PASS |
| 6 | data_manager.py line 209 mojibake fixed (`"배합 기록 저장 실패"`) | PASS |

### Issue 2: data_manager.py Export Logic DRY (MEDIUM) - 8/8 items

| # | Plan Item | Status |
|---|-----------|--------|
| 1 | `_generate_report_files()` helper extracted | PASS |
| 2 | Handles signature image creation | PASS |
| 3 | Handles Excel generation | PASS |
| 4 | Handles PDF generation | PASS |
| 5 | Handles temp file cleanup | PASS |
| 6 | Returns `Optional[str]` (PDF path) | PASS |
| 7 | `_export_report()` is thin wrapper | PASS |
| 8 | `export_existing_record()` is thin wrapper | PASS |

### Issue 3: image_processor.py Method Decomposition (MEDIUM) - 4/4 items

| # | Plan Item | Status |
|---|-----------|--------|
| 1 | `_prepare_signature_alpha()` sub-method extracted | PASS |
| 2 | `_apply_enhancements()` sub-method extracted | PASS |
| 3 | `_apply_transform()` sub-method extracted | PASS |
| 4 | `from typing import Optional, Tuple` import added | PASS |

### Issue 4: WindowStaysOnTopHint Configurable (LOW) - 2/2 items

| # | Plan Item | Status |
|---|-----------|--------|
| 1 | `config.get("ui.window_stays_on_top", True)` guard added | PASS |
| 2 | `"window_stays_on_top": true` added to config.json | PASS |

### Issue 5: record_view_dialog.py DRY (LOW) - 2/2 items

| # | Plan Item | Status |
|---|-----------|--------|
| 1 | `_get_checked_lots() -> List[str]` method extracted | PASS |
| 2 | Both callers use `self._get_checked_lots()` | PASS |

---

## Verification

| Check | Result |
|-------|--------|
| BOM removed (first 3 bytes = `b'"""'`) | PASS |
| All 25 tests pass | PASS |
| No functional behavior changes | PASS |

---

## Observations (Out of Scope)

- `v3/ui/main_window.py` contains mojibake in methods not targeted by the plan (e.g., `_clear_table()`, `auto_assign_lots()`). These were not in scope for this cycle.

---

## Assessment

**Match Rate: 100%** - All plan items fully implemented. Ready for completion report.
