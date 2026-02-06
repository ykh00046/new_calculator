
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from PySide6.QtWidgets import QApplication

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from ui.panels.recipe_panel import RecipePanel
from ui.panels.work_info_panel import WorkInfoPanel
from ui.panels.scan_effects_panel import ScanEffectsPanel
from ui.panels.material_table_panel import MaterialTablePanel
from ui.panels.signature_panel import SignaturePanel

# Global QApplication instance for all tests
app = QApplication.instance() or QApplication(sys.argv)

class TestRecipePanel(unittest.TestCase):
    def setUp(self):
        self.panel = RecipePanel()

    def test_initial_state(self):
        self.assertEqual(self.panel.get_recipe_name(), "")
        self.assertEqual(self.panel.get_amount(), 0.0)

    def test_set_recipes(self):
        recipes = ["Recipe A", "Recipe B"]
        self.panel.set_recipes(recipes)
        self.assertEqual(self.panel.recipe_combo.count(), 3)
        self.assertEqual(self.panel.recipe_combo.itemText(1), "Recipe A")

class TestWorkInfoPanel(unittest.TestCase):
    def setUp(self):
        self.patcher_config = patch('ui.panels.work_info_panel.config')
        self.mock_config = self.patcher_config.start()
        self.mock_config.workers = ["Worker A", "Worker B"]
        self.panel = WorkInfoPanel()

    def tearDown(self):
        self.patcher_config.stop()

    def test_get_data(self):
        # Simulate worker selection logic manually or just set attribute
        self.panel.worker_name = "Worker A"
        
        data = self.panel.get_data()
        self.assertIn('work_date', data)
        self.assertIn('work_time', data)
        self.assertEqual(data['worker_name'], "Worker A")
        self.assertTrue(data['include_time'])

class TestScanEffectsPanel(unittest.TestCase):
    def setUp(self):
        self.patcher_config = patch('ui.panels.scan_effects_panel.config')
        self.mock_config = self.patcher_config.start()
        # Mock default return values
        self.mock_config.scan_effects = {
            "dpi": 200, "blur_radius": 0.5, "noise_range": 10,
            "contrast_factor": 1.0, "brightness_factor": 1.0
        }
        self.panel = ScanEffectsPanel()

    def tearDown(self):
        self.patcher_config.stop()

    def test_get_data_defaults(self):
        data = self.panel.get_data()
        # Correct keys based on implementation
        self.assertIn('dpi', data)
        self.assertIn('contrast_factor', data)
        self.assertIn('noise_range', data)
        self.assertIn('blur_radius', data)
        self.assertIn('brightness_factor', data)

class TestMaterialTablePanel(unittest.TestCase):
    def setUp(self):
        self.mock_data_manager = MagicMock()
        self.panel = MaterialTablePanel(self.mock_data_manager)

    def test_initial_state(self):
        self.assertEqual(self.panel.table.rowCount(), 0)
        # Empty table is technically complete (no lots missing), 
        # but usually we check if recipe is selected in MainWindow.
        self.assertTrue(self.panel.is_complete())

    def test_incomplete_state(self):
        items = [{'품목코드': 'M01', '품목명': 'Item1', '배합비율': 50.0}]
        self.panel.load_items(items)
        # Loaded but LOT empty -> Should be False
        self.assertFalse(self.panel.is_complete())

    def test_load_items(self):
        items = [
            {'품목코드': 'M01', '품목명': 'Item1', '배합비율': 50.0},
            {'품목코드': 'M02', '품목명': 'Item2', '배합비율': 50.0}
        ]
        self.panel.load_items(items)
        self.assertEqual(self.panel.table.rowCount(), 2)

    def test_theory_update(self):
        items = [{'품목코드': 'M01', '품목명': 'Item1', '배합비율': 50.0}]
        self.panel.load_items(items)
        
        self.panel.update_theory(100.0)
        # 100 * 50% = 50.0
        theory_item = self.panel.table.item(0, 3) # Col 3 is theory
        self.assertEqual(theory_item.text(), "50.000")


class TestSignaturePanel(unittest.TestCase):
    """SignaturePanel 테스트"""

    def setUp(self):
        self.panel = SignaturePanel()

    def test_initial_state(self):
        """초기 체크박스 상태 확인 - 모두 체크됨"""
        self.assertTrue(self.panel.chk_charge.isChecked())
        self.assertTrue(self.panel.chk_review.isChecked())
        self.assertTrue(self.panel.chk_approve.isChecked())

    def test_get_data(self):
        """get_data() 반환값 확인"""
        # 초기 상태
        data = self.panel.get_data()
        self.assertTrue(data['charge'])
        self.assertTrue(data['review'])
        self.assertTrue(data['approve'])
        
        # 체크 해제 후
        self.panel.chk_review.setChecked(False)
        data = self.panel.get_data()
        self.assertFalse(data['review'])

if __name__ == '__main__':
    unittest.main()
