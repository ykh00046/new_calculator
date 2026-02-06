import argparse
import asyncio
from typing import Optional

from models.data_manager import DataManager
from config.config_manager import config


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate PDF for an existing record.")
    parser.add_argument("--lot", default="CSPB25102401", help="Product LOT number")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout seconds for PDF generation")
    parser.add_argument("--skip-export", action="store_true", help="Skip PDF export (fast check)")
    return parser.parse_args()


async def _export_with_timeout(
    data_manager: DataManager,
    product_lot: str,
    effects_params: dict,
    timeout_sec: float,
):
    return await asyncio.wait_for(
        asyncio.to_thread(data_manager.export_existing_record, product_lot, effects_params),
        timeout=timeout_sec,
    )


async def main():
    """
    Temporary script to regenerate a PDF for an existing record.
    """
    print("PDF ??? ???? ?????...")
    data_manager = DataManager()

    # Get default scan effects from config
    effects_params = config.scan_effects

    args = _parse_args()
    product_lot = args.lot

    print(f"LOT: {product_lot}? ?? PDF? ??????.")
    print(f"??? ?? ?? ????: {effects_params}")

    if args.skip_export:
        print("???: PDF ??? ?? (--skip-export)")
        return

    # Regenerate the PDF (with timeout)
    pdf_file = await _export_with_timeout(data_manager, product_lot, effects_params, args.timeout)

    if pdf_file:
        print(f"??: PDF? ?? ??? ????????: {pdf_file}")
    else:
        print("??: PDF ???? ??????.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.TimeoutError:
        print("????: PDF ???? ?? ?? ? ???? ?????.")
    except Exception as e:
        print(f"???? ?? ? ?? ??: {e}")
