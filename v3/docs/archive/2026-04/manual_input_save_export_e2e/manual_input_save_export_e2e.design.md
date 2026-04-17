# Manual Input Save/Export E2E — Design

> **Author**: AI Assistant
> **Created**: 2026-04-17
> **Status**: Design
> **Cycle**: PDCA #12
> **Parent Plan**: `01-plan/features/manual_input_save_export_e2e.plan.md`

---

## 1. Design Decisions (Plan에서 남긴 결정사항 확정)

### 1.1 테스트 파일 배치 — **신규 파일 분리**

기존 `test_manual_input_interface.py` (264 LOC, 19 cases)에 Layer D를 확장하는 대신, 신규 파일 2개로 분리:

| 신규 파일 | 담당 | 이유 |
|---|---|---|
| `tests/unit/test_manual_input_save_export.py` | D1 Orchestration + D3 Error Paths | 기존 Layer A/B/C(순수 UI 로직)와 성격이 다른 "오케스트레이션" 관점 — 파일 분리로 가독성/변경 국소성 확보 |
| `tests/unit/test_excel_exporter.py` | D2 Excel Content | `ExcelExporter`는 manual_input과 독립 모듈 — 테스트도 대상 모듈 기준으로 분리 (재사용성↑) |

**근거**: PDCA #11 feedback(F-01)에서 "Qt Mock 주입 시 시그니처 주의" 교훈이 `test_manual_input_interface.py`에 국소화되어 있고, 이 관심사를 Excel 모듈 테스트에 섞으면 setUp이 복잡해짐. 모듈 경계를 따라 분리.

### 1.2 `cell_mapping` 주입 전략 — **실 config 사용 + 런타임 값 검증**

`config.json` 내 `excel.cell_mapping`을 테스트 전용으로 덮어쓰지 않고 **실 config 그대로 사용**. 테스트 assertion은 다음 불변식만 검증:

- 필수 키 존재: `date`, `product_lot`, `total_amount`, `data_start_row`, `material_name_col`, `ratio_col`, `theory_amount_col`
- `data_start_row`로 지정된 행부터 자재 N줄이 연속 기입
- `total_amount` 셀 값 == `data['amount'] / 100` (현행 코드 동작 그대로 — `excel_exporter.py:207`)

**근거**:
1. config.json 값은 실제 템플릿 배치와 쌍으로 묶인 production contract. 테스트가 이를 임의 교체하면 "config 누락 시 회귀"를 놓친다.
2. 현재 `excel.cell_mapping` 값(위 plan 1.2의 실 dump):
   ```json
   {
     "date": "A3", "scale": "A4", "worker": "C3", "work_time": "E3",
     "product_lot": "A6", "total_amount": "B6", "data_start_row": 6,
     "material_name_col": "C", "material_lot_col": "D",
     "ratio_col": "E", "theory_amount_col": "F", "actual_amount_col": "G"
   }
   ```
3. `paths.output`만 `tempfile.TemporaryDirectory`로 격리 (실적서 폴더 오염 방지).

### 1.3 `ExcelExporter` 지연 import — **`models.excel_exporter.ExcelExporter` 패치**

`manual_input_interface.py:352` `from models.excel_exporter import ExcelExporter`는 함수 내부 지연 import이므로, patch는 **원본 모듈의 속성**을 대상으로 삼아야 한다.

```python
with patch("models.excel_exporter.ExcelExporter") as mock_cls:
    ...
```

함수가 호출될 때마다 `models.excel_exporter` 모듈에서 `ExcelExporter`를 lookup하므로 이 패치 경로가 유효. 단, 만약 이전 테스트가 `ui.panels.manual_input_interface` 모듈을 재임포트하지 않았다면 `sys.modules["models.excel_exporter"]`가 이미 로드된 상태라도 patch는 속성 교체이므로 문제없음.

**검증**: D1 첫 케이스 실행 후 `mock_cls.assert_called_once()` 확인으로 patch 경로 정확성 교차 검증.

---

## 2. Test Case 시그니처 목록

### 2.1 D1 Orchestration (`test_manual_input_save_export.py`) — 5 cases

```python
class TestSaveAndExportOrchestration(unittest.TestCase):
    """_save_and_export 오케스트레이션 (DB/Excel/PDF Mock)."""

    def setUp(self):
        self.panel = _make_panel_with_data()   # 제품명/수량/자재 2행 채워진 상태
        self.qmb_patcher = patch("ui.panels.manual_input_interface.QMessageBox")
        self.exp_patcher = patch("models.excel_exporter.ExcelExporter")
        self.mock_qmb = self.qmb_patcher.start()
        self.mock_exp_cls = self.exp_patcher.start()
        self.mock_exp = self.mock_exp_cls.return_value
        self.mock_exp.export_to_excel.return_value = "/tmp/X.xlsx"
        self.mock_exp.export_to_pdf.return_value = "/tmp/X.pdf"

    def tearDown(self):
        self.qmb_patcher.stop()
        self.exp_patcher.stop()

    def test_save_and_export_calls_db_then_excel_then_pdf(self):
        """정상 흐름: DB save → export_to_excel → export_to_pdf 순서 및 1회씩 호출"""

    def test_save_and_export_passes_resolved_lot_from_db(self):
        """DB가 반환한 product_lot이 Excel export_data['product_lot']에 사용되고 product_lot_edit도 갱신"""

    def test_save_and_export_passes_include_time_flag(self):
        """chk_include_time=False 시 work_time=''로 DB/Excel에 전달, include_work_time=False로 export_to_excel 호출"""

    def test_save_and_export_passes_materials_list_structure(self):
        """details_data가 material_code/name/lot/ratio/theory/actual 키로 DB에 전달, Excel 'materials'에도 동일 구조"""

    def test_save_and_export_passes_scan_effects_to_pdf(self):
        """scan_effects_panel.get_data() 결과가 export_to_pdf 2번째 인자로 전달"""
```

### 2.2 D3 Error Paths (`test_manual_input_save_export.py`) — 3 cases

```python
class TestSaveAndExportErrorPaths(unittest.TestCase):
    """_save_and_export 실패 경로."""

    # setUp/tearDown은 D1과 동일 (공통 헬퍼로 추출)

    def test_db_failure_shows_critical_and_skips_export(self):
        """dhr_db.save_dhr_record 예외 → QMessageBox.critical 호출, export_to_excel 미호출"""

    def test_excel_failure_shows_partial_success_warning(self):
        """export_to_excel returns None → QMessageBox.warning(Partial Success) 호출"""

    def test_pdf_failure_keeps_excel_and_shows_partial_success(self):
        """export_to_pdf returns None → QMessageBox.warning(Partial Success), export_to_excel 결과는 message에 포함"""
```

### 2.3 D2 Excel Content (`test_excel_exporter.py`) — 5 cases

```python
class TestExcelExporterExportToExcel(unittest.TestCase):
    """ExcelExporter.export_to_excel 실 템플릿 기반 검증."""

    @classmethod
    def setUpClass(cls):
        cls.template = os.path.join(PROJECT_ROOT, "resources", "template.xlsx")
        if not os.path.exists(cls.template):
            raise unittest.SkipTest("resources/template.xlsx not found")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg_patcher = patch("models.excel_exporter.config")
        self.mock_cfg = self.cfg_patcher.start()
        self.mock_cfg.get.side_effect = self._cfg_side_effect

    def tearDown(self):
        self.cfg_patcher.stop()
        self.tmp.cleanup()

    def _cfg_side_effect(self, key, default=None):
        table = {
            "paths.output": self.tmp.name,
            "excel.cell_mapping": REAL_CELL_MAPPING,  # config.json과 동일한 값 하드카피
        }
        return table.get(key, default)

    def test_export_to_excel_creates_file_with_product_lot_name(self):
        """출력 파일명 == f'{product_lot}.xlsx'"""

    def test_export_to_excel_returns_none_when_template_missing(self):
        """template.xlsx 경로 조작 → export returns None, 로그만 warning"""

    def test_export_to_excel_writes_key_cells(self):
        """openpyxl 재로드 후 date/product_lot/total_amount 셀 값 검증
           - total_amount 셀 == input / 100 (현 코드 스펙 유지)"""

    def test_export_to_excel_writes_material_rows_from_data_start_row(self):
        """N행 자재가 data_start_row부터 material_name_col/ratio_col/theory_amount_col/actual_amount_col에 기입"""

    def test_export_to_excel_omits_work_time_when_flag_false(self):
        """include_work_time=False → work_time 셀이 '' 또는 공란"""
```

**총 13 cases** (D1: 5 + D3: 3 + D2: 5)

---

## 3. 공통 헬퍼 설계

### 3.1 `_make_panel_with_data()` (D1/D3 공용)

PDCA #11의 `_make_panel`을 확장. 제품명·수량·자재 2행이 이미 채워진 상태로 반환:

```python
def _make_panel_with_data(product_lot_from_db: str = "TEST-20260417-01"):
    mock_db = MagicMock()
    mock_db.generate_product_lot.return_value = product_lot_from_db
    mock_db.save_dhr_record.return_value = 42  # record_id

    panel = ManualInputInterface(dhr_db=mock_db, lot_manager=MagicMock())
    panel.product_name_edit.setText("TEST")
    panel.amount_spin.setValue(500.0)
    panel.table.setRowCount(0)
    panel._add_row()
    _fill_row(panel, 0, ["M1", "Mat1", "40", "200", "199.5", "L1"])
    panel._add_row()
    _fill_row(panel, 1, ["M2", "Mat2", "60", "300", "300.2", "L2"])
    return panel
```

### 3.2 `REAL_CELL_MAPPING` 상수 (D2)

`config.json`과 동일한 매핑을 테스트 파일 상단에 리터럴로 하드카피:

```python
REAL_CELL_MAPPING = {
    "date": "A3", "scale": "A4", "worker": "C3", "work_time": "E3",
    "product_lot": "A6", "total_amount": "B6", "data_start_row": 6,
    "material_name_col": "C", "material_lot_col": "D",
    "ratio_col": "E", "theory_amount_col": "F", "actual_amount_col": "G",
}
```

**이유**: 테스트가 config.json 변경을 **의도적으로** 감지해야 한다. config.json과 REAL_CELL_MAPPING이 분기하면 D2 테스트가 실패 → 개발자가 매핑 변경을 인지하고 명시적으로 sync.

---

## 4. 실행 흐름

### 4.1 D1 예시 — `test_save_and_export_calls_db_then_excel_then_pdf`

```python
def test_save_and_export_calls_db_then_excel_then_pdf(self):
    self.panel._save_and_export()

    # DB 저장 1회
    self.panel.dhr_db.save_dhr_record.assert_called_once()

    # Excel export 1회, DB 이후
    self.mock_exp_cls.assert_called_once_with()
    self.mock_exp.export_to_excel.assert_called_once()

    # PDF export 1회
    self.mock_exp.export_to_pdf.assert_called_once()

    # 정상 완료 → information 팝업
    self.mock_qmb.information.assert_called_once()
    self.mock_qmb.critical.assert_not_called()
```

### 4.2 D2 예시 — `test_export_to_excel_writes_material_rows_from_data_start_row`

```python
def test_export_to_excel_writes_material_rows_from_data_start_row(self):
    exporter = ExcelExporter()
    data = {
        "product_lot": "LOT-TEST-01",
        "work_date": "2026-04-17",
        "total_amount": 500.0,
        "worker": "tester",
        "scale": "M-65",
        "materials": [
            {"material_name": "Mat1", "material_lot": "L1", "ratio": 40,
             "theory_amount": 200, "actual_amount": 199.5},
            {"material_name": "Mat2", "material_lot": "L2", "ratio": 60,
             "theory_amount": 300, "actual_amount": 300.2},
        ],
    }
    path = exporter.export_to_excel(data, include_work_time=True)
    self.assertIsNotNone(path)
    self.assertTrue(path.endswith("LOT-TEST-01.xlsx"))

    wb = load_workbook(path)
    ws = wb.active
    start = REAL_CELL_MAPPING["data_start_row"]
    self.assertEqual(ws[f"C{start}"].value, "Mat1")
    self.assertEqual(ws[f"C{start+1}"].value, "Mat2")
    self.assertEqual(ws[f"E{start}"].value, 40)
    self.assertEqual(ws[f"F{start+1}"].value, 300)
    wb.close()
```

### 4.3 D3 예시 — `test_db_failure_shows_critical_and_skips_export`

```python
def test_db_failure_shows_critical_and_skips_export(self):
    self.panel.dhr_db.save_dhr_record.side_effect = RuntimeError("db down")
    self.panel._save_and_export()

    self.mock_qmb.critical.assert_called_once()
    self.mock_exp.export_to_excel.assert_not_called()
    self.mock_exp.export_to_pdf.assert_not_called()
```

---

## 5. 코드 조직

### 5.1 파일 헤더 공통 패턴 (PDCA #11 재사용)

```python
"""Unit tests for ManualInputInterface._save_and_export (PDCA #12)."""
import importlib
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch


def _ensure_ui_test_dependencies() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    missing = []
    for module_name in ("PySide6", "qfluentwidgets", "openpyxl"):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)
    if missing:
        raise unittest.SkipTest(
            f"UI tests require optional dependencies: {', '.join(missing)}"
        )


_ensure_ui_test_dependencies()

from PySide6.QtWidgets import QApplication, QTableWidgetItem

current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, PROJECT_ROOT)

app = QApplication.instance() or QApplication(sys.argv)
```

### 5.2 import 위치 — **클래스 setUp 내 지연 import 아님, 파일 상단 import 허용**

`ManualInputInterface`와 `ExcelExporter`는 `sys.path` 조작 후 import해야 하므로, 헬퍼 함수 내부에서 import:

```python
def _make_panel_with_data(...):
    from ui.panels.manual_input_interface import ManualInputInterface
    ...

# D2는 파일 상단 import 허용 (sys.path 이미 세팅됨)
from models.excel_exporter import ExcelExporter
from openpyxl import load_workbook
```

---

## 6. 리스크 & 완화 (Plan §3.3 확정)

| 리스크 | Plan 단계 | Design 확정안 |
|---|---|---|
| `resources/template.xlsx` 부재 | setUpClass SkipTest | ✅ 존재 확인 완료 (13,863 bytes) |
| `cell_mapping` 런타임 값 의존 | 실 config + 불변식 검증 | ✅ `REAL_CELL_MAPPING` 리터럴 하드카피 + side_effect로 주입 |
| `paths.output` 오염 | tempfile | ✅ `TemporaryDirectory` per-test |
| `ExcelExporter` 지연 import patch 경로 | `models.excel_exporter.ExcelExporter` | ✅ `manual_input_interface.py:352`에서 확인 |
| win32com import 실패 (non-Windows) | N/A | ✅ 개발자 환경 Windows 고정, D2는 win32com 호출 경로 미경유 |
| D1 Mock + Qt 시그니처 충돌 (PDCA #11 F-01) | `return_value` 명시 | ✅ `generate_product_lot.return_value = "TEST-20260417-01"` |

---

## 7. 구현 순서 (Do 단계용)

1. **Step 1** — `tests/unit/test_manual_input_save_export.py` 골격 작성
   - 파일 헤더 + `_make_panel_with_data` 헬퍼 + `TestSaveAndExportOrchestration.setUp/tearDown`
2. **Step 2** — D1 5 cases 구현 → 로컬 실행
3. **Step 3** — D3 3 cases 구현 → 로컬 실행
4. **Commit #1**: `test: add save/export orchestration and error-path tests`
5. **Step 4** — `tests/unit/test_excel_exporter.py` 신규 작성 (setUpClass + _cfg_side_effect)
6. **Step 5** — D2 5 cases 구현 → 실 template으로 실행 확인
7. **Commit #2**: `test: add excel_exporter content verification with real template`
8. **Step 6** — 전체 실행 (`run_tests.py`) 52→65 확인, 실행시간 체크
9. **필요 시 Commit #3** (수정/보정)

---

## 8. Success Criteria (Plan §6과 동일, 구체화)

- [ ] 신규 파일 2개 (`test_manual_input_save_export.py`, `test_excel_exporter.py`)
- [ ] 13 test cases 추가 (D1: 5, D2: 5, D3: 3)
- [ ] 총 테스트 52 → **65**
- [ ] 실행 시간 < 1.7초 (D2의 실 template 복사 포함 시 증가분 ≤ 0.7초 예상)
- [ ] 프로덕션 코드 변경 0 라인
- [ ] `config.json` 변경 감지 메커니즘 작동 (REAL_CELL_MAPPING sync 필요 시 D2 실패로 드러남)

---

## 9. Next Phase

- **다음**: `/pdca do manual_input_save_export_e2e`
- Do 단계에서는 Step 1~9 순서대로 구현, 커밋 2~3개로 분할.
