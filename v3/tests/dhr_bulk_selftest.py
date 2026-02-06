import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import os
import tempfile
from models.dhr_database import DhrDatabaseManager
from models.dhr_bulk_generator import DhrBulkGenerator


class FakeLotManager:
    def __init__(self):
        self.calls = {}

    def get_lot(self, item_code: str, work_date: str):
        key = (item_code, work_date)
        self.calls[key] = self.calls.get(key, 0) + 1
        return [(f"LOT-{item_code}-{work_date.replace('-', '')}", work_date)]


def seed_recipe(db: DhrDatabaseManager, recipe_name: str):
    recipe = {
        "recipe_name": recipe_name,
        "company": "TEST",
        "product_type": "TEST",
        "drug": "TEST",
        "wear_period": "TEST",
        "default_amount": 1000,
    }
    materials = [
        {"material_code": "MAT001", "material_name": "??1", "ratio": 60},
        {"material_code": "MAT002", "material_name": "??2", "ratio": 40},
    ]
    db.save_recipe(recipe, materials)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "dhr_test.db")
        db = DhrDatabaseManager(db_path=db_path)
        seed_recipe(db, "TEST_RECIPE")

        lot_manager = FakeLotManager()
        generator = DhrBulkGenerator(db, lot_manager)

        entries = [
            {"date": "2026-02-03", "amount": 500, "row": 1},
            {"date": "2026-02-03", "amount": 700, "row": 2},
            {"date": "2026-02-04", "amount": 600, "row": 3},
        ]

        count = generator.generate(
            entries=entries,
            product_name="TEST_RECIPE",
            materials=[
                {"code": "MAT001", "name": "??1", "ratio": 60},
                {"code": "MAT002", "name": "??2", "ratio": 40},
            ],
            worker="TEST",
            include_time=True,
            scan_effects={},
            signature_options={},
            export=False
        )

        print(f"SELFTEST OK: {count} records")


if __name__ == "__main__":
    main()
