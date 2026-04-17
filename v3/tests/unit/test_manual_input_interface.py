"""Unit tests for ManualInputInterface (PDCA #11 QA coverage)."""
import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


def _ensure_ui_test_dependencies() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    missing = []
    for module_name in ("PySide6", "qfluentwidgets"):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)
    if missing:
        raise unittest.SkipTest(
            f"UI tests require optional GUI dependencies: {', '.join(missing)}"
        )


_ensure_ui_test_dependencies()

from PySide6.QtWidgets import QApplication, QTableWidgetItem

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

app = QApplication.instance() or QApplication(sys.argv)


def _make_panel(dhr_db=None, lot_manager=None):
    from ui.panels.manual_input_interface import ManualInputInterface
    if dhr_db is None:
        # product_name_edit.textChanged signal → _update_product_lot → setText 경로에서
        # MagicMock 반환값이 QLineEdit.setText(str) 시그니처를 깨므로 빈 문자열 기본값 지정.
        dhr_db = MagicMock()
        dhr_db.generate_product_lot.return_value = ""
    return ManualInputInterface(
        dhr_db=dhr_db,
        lot_manager=lot_manager or MagicMock(),
    )


def _fill_row(panel, row: int, values):
    for col, value in enumerate(values):
        item = panel.table.item(row, col)
        if item is None:
            item = QTableWidgetItem("")
            panel.table.setItem(row, col, item)
        item.setText(str(value))


# ---------------------------------------------------------------------------
# Layer A — Pure Logic
# ---------------------------------------------------------------------------

class TestToFloat(unittest.TestCase):
    def setUp(self):
        self.panel = _make_panel()

    def test_to_float_valid(self):
        self.assertEqual(self.panel._to_float("12.5"), 12.5)

    def test_to_float_blank_returns_zero(self):
        self.assertEqual(self.panel._to_float(""), 0.0)
        self.assertEqual(self.panel._to_float("   "), 0.0)

    def test_to_float_invalid_returns_zero(self):
        self.assertEqual(self.panel._to_float("abc"), 0.0)


class TestWorkerName(unittest.TestCase):
    def test_worker_name_returns_config_value(self):
        with patch("ui.panels.manual_input_interface.config") as mock_cfg:
            mock_cfg.last_worker = "김민호"
            panel = _make_panel()
            self.assertEqual(panel.worker_name, "김민호")

    def test_worker_name_empty_falls_back(self):
        with patch("ui.panels.manual_input_interface.config") as mock_cfg:
            mock_cfg.last_worker = ""
            panel = _make_panel()
            self.assertEqual(panel.worker_name, "Unknown")


# ---------------------------------------------------------------------------
# Layer B — UI/Table Logic
# ---------------------------------------------------------------------------

class TestTableHelpers(unittest.TestCase):
    def setUp(self):
        self.panel = _make_panel()

    def test_is_empty_material_row_true_for_new_row(self):
        self.panel.table.setRowCount(0)
        self.panel._add_row()
        self.assertTrue(self.panel._is_empty_material_row(0))

    def test_is_empty_material_row_false_for_partial(self):
        self.panel.table.setRowCount(0)
        self.panel._add_row()
        _fill_row(self.panel, 0, ["CODE", "", "", "", "", ""])
        self.assertFalse(self.panel._is_empty_material_row(0))

    def test_effective_row_count_mixed(self):
        self.panel.table.setRowCount(0)
        for _ in range(3):
            self.panel._add_row()
        _fill_row(self.panel, 0, ["", "", "", "", "", ""])
        _fill_row(self.panel, 1, ["M1", "Mat1", "50", "", "", "L1"])
        _fill_row(self.panel, 2, ["M2", "", "", "", "", ""])
        self.assertEqual(self.panel._get_effective_material_row_count(), 2)


class TestValidate(unittest.TestCase):
    def setUp(self):
        self.panel = _make_panel()
        self.qmb_patcher = patch("ui.panels.manual_input_interface.QMessageBox")
        self.mock_qmb = self.qmb_patcher.start()

    def tearDown(self):
        self.qmb_patcher.stop()

    def _prepare(self, name: str, amount: float, materials: int):
        self.panel.product_name_edit.setText(name)
        self.panel.amount_spin.setValue(amount)
        self.panel.table.setRowCount(0)
        for i in range(max(materials, 0)):
            self.panel._add_row()
            _fill_row(self.panel, i, [f"M{i}", f"Mat{i}", "50", "", "", f"L{i}"])
        if materials == 0:
            self.panel._add_row()  # 빈 행 1개는 남겨 둠 (실제 UX)

    def test_validate_fails_without_product_name(self):
        self._prepare(name="", amount=100.0, materials=1)
        self.assertFalse(self.panel._validate())
        self.mock_qmb.warning.assert_called()

    def test_validate_fails_with_zero_amount(self):
        self._prepare(name="제품A", amount=0.0, materials=1)
        self.assertFalse(self.panel._validate())
        self.mock_qmb.warning.assert_called()

    def test_validate_fails_without_materials(self):
        self._prepare(name="제품A", amount=100.0, materials=0)
        self.assertFalse(self.panel._validate())
        self.mock_qmb.warning.assert_called()

    def test_validate_passes_with_full_data(self):
        self._prepare(name="제품A", amount=100.0, materials=2)
        self.assertTrue(self.panel._validate())
        self.mock_qmb.warning.assert_not_called()


class TestRecalcAndCollect(unittest.TestCase):
    def setUp(self):
        self.panel = _make_panel()

    def test_recalc_theory_computes_ratio(self):
        self.panel.amount_spin.setValue(1000.0)
        self.panel.table.setRowCount(0)
        self.panel._add_row()
        _fill_row(self.panel, 0, ["M1", "Mat1", "50", "", "", "L1"])
        self.panel._add_row()
        _fill_row(self.panel, 1, ["M2", "Mat2", "25", "", "", "L2"])
        self.panel._recalc_theory()
        self.assertEqual(self.panel.table.item(0, 3).text(), "500.000")
        self.assertEqual(self.panel.table.item(1, 3).text(), "250.000")

    def test_collect_data_structure(self):
        self.panel.product_name_edit.setText("제품A")
        self.panel.amount_spin.setValue(500.0)
        self.panel.table.setRowCount(0)
        self.panel._add_row()
        _fill_row(self.panel, 0, ["M1", "Mat1", "40", "200", "199.5", "L1"])
        self.panel._add_row()
        _fill_row(self.panel, 1, ["M2", "Mat2", "60", "300", "300.2", "L2"])

        data = self.panel._collect_data()
        for key in (
            "product_name", "product_lot", "amount",
            "work_date", "work_time", "include_time", "materials",
        ):
            self.assertIn(key, data)
        self.assertEqual(data["product_name"], "제품A")
        self.assertEqual(data["amount"], 500.0)
        self.assertEqual(len(data["materials"]), 2)
        self.assertEqual(data["materials"]["M1"]["배합비율"], 40.0)
        self.assertEqual(data["materials"]["M2"]["LOT"], "L2")


class TestRowOps(unittest.TestCase):
    def setUp(self):
        self.panel = _make_panel()

    def test_add_row_increments_count(self):
        self.panel.table.setRowCount(1)
        before = self.panel.table.rowCount()
        self.panel._add_row()
        self.assertEqual(self.panel.table.rowCount(), before + 1)

    def test_remove_row_without_selection_removes_last(self):
        self.panel.table.setRowCount(0)
        for _ in range(3):
            self.panel._add_row()
        self.panel.table.clearSelection()
        self.panel.table.setCurrentCell(-1, -1)
        self.panel._remove_row()
        self.assertEqual(self.panel.table.rowCount(), 2)


class TestLoadRecipe(unittest.TestCase):
    def setUp(self):
        self.panel = _make_panel()

    def test_load_recipe_populates_table(self):
        recipe = {"recipe_name": "제품B", "default_amount": 1500.0}
        materials = [
            {"material_code": "A1", "material_name": "자재1", "ratio": 30},
            {"material_code": "A2", "material_name": "자재2", "ratio": 40},
            {"material_code": "A3", "material_name": "자재3", "ratio": 30},
        ]
        self.panel.load_recipe(recipe, materials)
        self.assertEqual(self.panel.table.rowCount(), 3)
        self.assertEqual(self.panel.product_name_edit.text(), "제품B")
        self.assertEqual(self.panel.amount_spin.value(), 1500.0)
        self.assertEqual(self.panel.table.item(0, 0).text(), "A1")
        self.assertEqual(self.panel.table.item(2, 1).text(), "자재3")
        # 이론계량 재계산 확인 (1500 * 30% = 450)
        self.assertEqual(self.panel.table.item(0, 3).text(), "450.000")


# ---------------------------------------------------------------------------
# Layer C — DB Mock
# ---------------------------------------------------------------------------

class TestUpdateProductLot(unittest.TestCase):
    def test_update_product_lot_uses_db(self):
        mock_db = MagicMock()
        mock_db.generate_product_lot.return_value = "ABC-20260417-01"
        panel = _make_panel(dhr_db=mock_db)
        panel.product_name_edit.setText("ABC")
        # setText가 signal을 통해 _update_product_lot 호출, 또는 명시 호출
        panel._update_product_lot()
        mock_db.generate_product_lot.assert_called_with("ABC", panel.date_edit.date().toString("yyyy-MM-dd"))
        self.assertEqual(panel.product_lot_edit.text(), "ABC-20260417-01")

    def test_update_product_lot_fallback_on_exception(self):
        mock_db = MagicMock()
        mock_db.generate_product_lot.side_effect = RuntimeError("db down")
        panel = _make_panel(dhr_db=mock_db)
        panel.product_name_edit.setText("ABC")
        panel._update_product_lot()
        # 폴백: product_name + YYMMDD (현재 날짜 기반이므로 시작 부분만 검증)
        text = panel.product_lot_edit.text()
        self.assertTrue(text.startswith("ABC"))
        self.assertEqual(len(text), len("ABC") + 6)


if __name__ == "__main__":
    unittest.main()
