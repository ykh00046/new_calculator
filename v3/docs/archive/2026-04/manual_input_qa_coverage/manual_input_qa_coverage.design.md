# Manual Input QA Coverage — Design

> **Author**: AI Assistant
> **Created**: 2026-04-17
> **Status**: Design
> **Cycle**: PDCA #11
> **Parent**: [manual_input_qa_coverage.plan.md](../../01-plan/features/manual_input_qa_coverage.plan.md)

---

## 1. 테스트 파일 구조

### 1.1 위치
`v3/tests/unit/test_manual_input_interface.py` (신규)

### 1.2 파일 헤더 (표준)
`test_panels.py`와 동일한 패턴:

```python
import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


def _ensure_ui_test_dependencies() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    missing = []
    for mod in ("PySide6", "qfluentwidgets"):
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            missing.append(mod)
    if missing:
        raise unittest.SkipTest(f"UI tests require: {', '.join(missing)}")


_ensure_ui_test_dependencies()

from PySide6.QtWidgets import QApplication, QTableWidgetItem

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

app = QApplication.instance() or QApplication(sys.argv)
```

---

## 2. 공유 픽스처 전략

### 2.1 `_make_panel` 헬퍼
매 테스트마다 `ManualInputInterface`를 생성하되 외부 의존성은 Mock 주입:

```python
def _make_panel(dhr_db=None, lot_manager=None):
    from ui.panels.manual_input_interface import ManualInputInterface
    return ManualInputInterface(
        dhr_db=dhr_db or MagicMock(),
        lot_manager=lot_manager or MagicMock(),
    )
```

DI가 이미 생성자에 있어 추가 프로덕션 변경 불필요.

### 2.2 config 패치
`config.last_worker` / `config.default_scale` 등 전역 상태 접근은 `patch('ui.panels.manual_input_interface.config')` 로 격리.

### 2.3 QMessageBox 패치
`_validate` 테스트에서 팝업 차단 위해 `patch('ui.panels.manual_input_interface.QMessageBox')`.

---

## 3. 테스트 케이스 설계 (총 13 cases)

### 3.1 Layer A — Pure Logic (3 cases)

#### `TestToFloat`
| Case | 입력 | 기대 |
|---|---|---|
| `test_to_float_valid` | `"12.5"` | `12.5` |
| `test_to_float_blank_returns_zero` | `""` / `"  "` | `0.0` |
| `test_to_float_invalid_returns_zero` | `"abc"` | `0.0` |

#### `TestWorkerName`
| Case | config.last_worker | 기대 |
|---|---|---|
| `test_worker_name_returns_config_value` | `"김민호"` | `"김민호"` |
| `test_worker_name_empty_falls_back` | `""` | `"Unknown"` |

### 3.2 Layer B — UI/Table Logic (8 cases)

#### `TestTableHelpers`
| Case | 설정 | 기대 |
|---|---|---|
| `test_is_empty_material_row_true_for_new_row` | 신규 빈 행 | `True` |
| `test_is_empty_material_row_false_for_partial` | 코드 1개 셀 입력 | `False` |
| `test_effective_row_count_mixed` | 3행: 빈/채운/부분 | `2` |

#### `TestValidate` (QMessageBox 패치)
| Case | 설정 | 기대 |
|---|---|---|
| `test_validate_fails_without_product_name` | name=빈, amount=100, 자재=1 | `False` + warning 호출 |
| `test_validate_fails_with_zero_amount` | name=유효, amount=0 | `False` |
| `test_validate_fails_without_materials` | name=유효, amount=100, 자재=0 | `False` |
| `test_validate_passes_with_full_data` | 전부 유효 | `True` + warning 미호출 |

#### `TestRecalcAndCollect`
| Case | 설정 | 기대 |
|---|---|---|
| `test_recalc_theory_computes_ratio` | amount=1000, ratio=[50, 25] | 이론=[500, 250] |
| `test_collect_data_structure` | 제품명+자재 2행 | dict 키 7개 + materials dict |

#### `TestRowOps`
| Case | 설정 | 기대 |
|---|---|---|
| `test_add_row_increments_count` | 초기 1행 → `_add_row()` | `rowCount() == 2` |
| `test_remove_row_without_selection_removes_last` | 3행, 선택 없음 | `rowCount() == 2` |

#### `TestLoadRecipe`
| Case | 설정 | 기대 |
|---|---|---|
| `test_load_recipe_populates_table` | 자재 3개 recipe | `rowCount() == 3`, 제품명·배합량 세팅 |

### 3.3 Layer C — DB Mock (2 cases)

#### `TestUpdateProductLot`
| Case | dhr_db mock | 기대 |
|---|---|---|
| `test_update_product_lot_uses_db` | `generate_product_lot.return_value = "ABC-20260417-01"` | `product_lot_edit.text() == "ABC-20260417-01"` |
| `test_update_product_lot_fallback_on_exception` | `generate_product_lot.side_effect = RuntimeError` | fallback `"ABC260417"` (제품명+YYMMDD) |

---

## 4. Mock 전략

| 대상 | 방식 | 이유 |
|---|---|---|
| `DhrDatabaseManager` | 생성자 인자 `dhr_db=MagicMock()` | DI 재활용, DB 파일 차단 |
| `LotManager` | 생성자 인자 `lot_manager=MagicMock()` | 파일 I/O 차단 |
| `config` (last_worker) | `patch('ui.panels.manual_input_interface.config')` | 전역 상태 격리 |
| `QMessageBox` | `patch('ui.panels.manual_input_interface.QMessageBox')` | 팝업 차단 |

---

## 5. 프로덕션 코드 영향

**영향 없음** — 테스트 파일 추가만. `ManualInputInterface.__init__`이 이미 `dhr_db=None, lot_manager=None` 인자를 받아 DI 가능 상태였음을 활용.

---

## 6. 실행

```bash
QT_QPA_PLATFORM=offscreen python v3/tests/run_tests.py
```

기대: `Ran 46 tests in <1s` (기존 33 + 신규 13).

---

## 7. 파일 카운트 예상

- 신규: `test_manual_input_interface.py` — 약 200~260 LOC
- 수정: 없음
