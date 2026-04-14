"""
일괄 생성 관련 공통 유틸리티 함수
날짜 파싱, 벌크 항목 파싱, 자재 정보 추출 등을 제공합니다.
"""
from datetime import datetime, timedelta
from typing import List, Dict


def parse_date_cell(value: str) -> str:
    """날짜 셀 값을 YYYY-MM-DD 형식으로 파싱합니다.

    엑셀 시리얼 넘버 또는 일반 날짜 문자열을 처리합니다.
    """
    raw = (value or "").strip()
    if not raw:
        return ""

    try:
        num = float(raw)
        if num > 0:
            base = datetime(1899, 12, 30)
            dt = base + timedelta(days=num)
            return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    candidates = ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%m/%d/%Y", "%m-%d-%Y"]
    for fmt in candidates:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def parse_bulk_entries(bulk_table) -> List[Dict]:
    """벌크 테이블에서 날짜/배합량 항목을 파싱합니다.

    Args:
        bulk_table: QTableWidget (col 0=날짜, col 1=배합량)

    Returns:
        [{date, amount, row}, ...] 리스트
    """
    entries = []
    for r in range(bulk_table.rowCount()):
        date_item = bulk_table.item(r, 0)
        amount_item = bulk_table.item(r, 1)
        date_text = date_item.text().strip() if date_item else ""
        amount_text = amount_item.text().strip() if amount_item else ""

        if not date_text and not amount_text:
            continue

        if not date_text or not amount_text:
            raise ValueError(f"{r+1}행: 날짜와 양을 모두 입력하세요.")

        work_date = parse_date_cell(date_text)
        if not work_date:
            raise ValueError(f"{r+1}행: 날짜를 인식할 수 없습니다.")

        try:
            amount = float(amount_text)
        except ValueError:
            raise ValueError(f"{r+1}행: 숫자가 아닌 값입니다.")

        if amount <= 0:
            raise ValueError(f"{r+1}행: 배합량은 0보다 커야 합니다.")

        entries.append({"date": work_date, "amount": amount, "row": r + 1})

    return entries


def get_materials_from_table(table) -> List[Dict]:
    """자재 테이블에서 자재 목록을 추출합니다.

    Args:
        table: QTableWidget (col 0=품목코드, col 1=품목명, col 2=배합비율)

    Returns:
        [{code, name, ratio}, ...] 리스트
    """
    materials = []
    for r in range(table.rowCount()):
        code_item = table.item(r, 0)
        name_item = table.item(r, 1)
        ratio_item = table.item(r, 2)
        code = code_item.text().strip() if code_item else ""
        name = name_item.text().strip() if name_item else ""

        if not code and not name:
            continue

        if not code:
            raise ValueError(f"자재 {r+1}행: 품목코드를 입력하세요.")

        ratio_text = ratio_item.text().strip() if ratio_item else ""
        if not ratio_text:
            raise ValueError(f"자재 {r+1}행: 배합비율을 입력하세요.")
        try:
            ratio = float(ratio_text)
        except ValueError:
            raise ValueError(f"자재 {r+1}행: 배합비율은 숫자로 입력하세요.")
        if ratio <= 0:
            raise ValueError(f"자재 {r+1}행: 배합비율은 0보다 커야 합니다.")

        materials.append({"code": code, "name": name, "ratio": ratio})

    if not materials:
        raise ValueError("자재 정보를 입력하세요.")
    return materials
