import random
from datetime import datetime, timedelta
from typing import List, Dict

from config.config_manager import config
from utils.logger import logger


class DhrBulkGenerator:
    def __init__(self, dhr_db, lot_manager):
        self.dhr_db = dhr_db
        self.lot_manager = lot_manager

    def _validate_material_lots_for_date(self, work_date: str, materials: List[Dict]):
        missing = []
        lot_map = {}
        for m in materials:
            lots = self.lot_manager.get_lot(m["code"], work_date)
            if not lots:
                missing.append(m["code"])
                continue
            lot_value = lots[0][0] if isinstance(lots[0], tuple) else lots[0]
            lot_map[m["code"]] = lot_value
        return (len(missing) == 0), missing, lot_map

    def _get_base_time_for_date(self, product_name: str, work_date: str):
        records = self.dhr_db.get_dhr_records(start_date=work_date, end_date=work_date, limit=1000)
        latest = None
        for r in records:
            if r.get("product_name") != product_name:
                continue
            wt = (r.get("work_time") or "").strip()
            if not wt:
                continue
            try:
                t = datetime.strptime(wt, "%H:%M:%S").time()
                if latest is None or t > latest:
                    latest = t
            except ValueError:
                continue

        if latest:
            return datetime.strptime(f"{work_date} {latest.strftime('%H:%M:%S')}", "%Y-%m-%d %H:%M:%S")

        base_minute = random.randint(0, 59)
        return datetime.strptime(f"{work_date} 09:{base_minute:02d}:00", "%Y-%m-%d %H:%M:%S")

    def generate(self, entries: List[Dict], product_name: str, materials: List[Dict], worker: str,
                 include_time: bool, scan_effects: Dict, signature_options: Dict, export: bool = True) -> int:
        if not entries:
            return 0

        unique_dates = []
        for e in entries:
            if e["date"] not in unique_dates:
                unique_dates.append(e["date"])

        lot_map_by_date = {}
        for d in unique_dates:
            ok, missing, lot_map = self._validate_material_lots_for_date(d, materials)
            if not ok:
                raise ValueError(f"{d} ?? LOT? ?? ? ?? ??? ????. ?? ????: {', '.join(missing)}")
            lot_map_by_date[d] = lot_map

        last_time_by_date = {}
        success_count = 0

        for entry in entries:
            work_date = entry["date"]
            amount = entry["amount"]

            if include_time:
                if work_date not in last_time_by_date:
                    last_time_by_date[work_date] = self._get_base_time_for_date(product_name, work_date)
                else:
                    add_min = random.randint(20, 40)
                    last_time_by_date[work_date] = last_time_by_date[work_date] + timedelta(minutes=add_min)
                work_time = last_time_by_date[work_date].strftime("%H:%M:%S")
            else:
                work_time = ""

            product_lot = self.dhr_db.generate_product_lot(product_name, work_date)

            details_data = []
            for m in materials:
                ratio = m["ratio"]
                theory = amount * (ratio / 100.0)
                lot_value = lot_map_by_date[work_date].get(m["code"], "")

                details_data.append({
                    'material_code': m["code"],
                    'material_name': m["name"],
                    'material_lot': lot_value,
                    'ratio': ratio,
                    'theory_amount': theory,
                    'actual_amount': theory,
                })

            record_data = {
                'product_lot': product_lot,
                'product_name': product_name,
                'worker': worker,
                'work_date': work_date,
                'work_time': work_time,
                'total_amount': amount,
                'scale': config.default_scale
            }

            self.dhr_db.save_dhr_record(record_data, details_data)

            if export:
                from models.excel_exporter import ExcelExporter
                from models.image_processor import ImageProcessor
                import os

                exporter = ExcelExporter()

                base_dir = os.path.dirname(os.path.dirname(__file__))
                resources_path = os.path.join(base_dir, "resources", "signature")
                base_image_path = os.path.join(resources_path, "image.jpeg")

                signature_cfg = config.get("signature", {})
                if signature_options:
                    signature_cfg["include"] = signature_options

                img_processor = ImageProcessor(resources_path=resources_path, config=signature_cfg)
                signed_image_path = os.path.join(base_dir, "resources", f"temp_signed_{worker}.png")

                image_to_embed = None
                if os.path.exists(base_image_path):
                    success, _ = img_processor.create_signed_image(
                        base_image_path, signed_image_path, worker
                    )
                    image_to_embed = signed_image_path if success else base_image_path

                export_data = {
                    "product_lot": product_lot,
                    "recipe_name": product_name,
                    "worker": worker,
                    "work_date": work_date,
                    "work_time": work_time if include_time else "",
                    "total_amount": amount,
                    "scale": config.default_scale,
                    "materials": details_data,
                }

                excel_path = exporter.export_to_excel(
                    export_data,
                    include_image=bool(image_to_embed),
                    image_path=image_to_embed,
                    include_work_time=include_time,
                )

                if excel_path:
                    exporter.export_to_pdf(excel_path, scan_effects or {})

                if image_to_embed == signed_image_path and os.path.exists(signed_image_path):
                    try:
                        os.remove(signed_image_path)
                    except Exception:
                        pass

            success_count += 1

        return success_count
