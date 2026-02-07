import argparse
from pathlib import Path

from models.dhr_database import DhrDatabaseManager
from models.lot_manager import LotManager
from models.dhr_bulk_generator import DhrBulkGenerator
from config.settings import LOT_FILE


def parse_tsv(path: Path):
    entries = []
    for idx, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split('	')
        if len(parts) < 2:
            raise ValueError(f"{idx}행: 형식이 올바르지 않습니다.")
        date = parts[0].strip()
        amount = float(parts[1].strip())
        entries.append({"date": date, "amount": amount, "row": idx})
    return entries


def load_recipe_materials(db: DhrDatabaseManager, recipe_name: str):
    recipes = db.get_recipes()
    recipe = None
    for r in recipes:
        if r.get('recipe_name') == recipe_name:
            recipe = r
            break
    if not recipe:
        raise ValueError(f"레시피를 찾을 수 없습니다: {recipe_name}")

    materials = db.get_recipe_materials(recipe['id'])
    result = []
    for m in materials:
        result.append({
            "code": m.get('material_code', ''),
            "name": m.get('material_name', ''),
            "ratio": m.get('ratio', 0.0),
        })
    return result


def main():
    parser = argparse.ArgumentParser(description="DHR bulk dry-run test (DB only)")
    parser.add_argument("--tsv", required=True, help="TSV file with date	amount")
    parser.add_argument("--recipe", required=True, help="Recipe name")
    parser.add_argument("--worker", default="TEST", help="Worker name")
    parser.add_argument("--include-time", action="store_true", help="Include work time")
    parser.add_argument("--export", action="store_true", help="Export Excel/PDF")
    args = parser.parse_args()

    entries = parse_tsv(Path(args.tsv))
    db = DhrDatabaseManager()
    lot_manager = LotManager(LOT_FILE)
    materials = load_recipe_materials(db, args.recipe)

    generator = DhrBulkGenerator(db, lot_manager)
    count = generator.generate(
        entries=entries,
        product_name=args.recipe,
        materials=materials,
        worker=args.worker,
        include_time=args.include_time,
        scan_effects={},
        signature_options={},
        export=args.export
    )
    print(f"OK: {count} records")


if __name__ == "__main__":
    main()
