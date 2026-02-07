"""
엑셀 붙여넣기 지원 테이블 위젯
BasePasteableTableWidget 및 파생 클래스를 제공합니다.
"""
from PySide6.QtWidgets import QTableWidgetItem, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence
from qfluentwidgets import TableWidget
from ui.styles import UITheme
from utils.logger import logger


class BasePasteableTableWidget(TableWidget):
    """엑셀 붙여넣기 지원 기반 테이블 클래스"""

    READONLY_COLUMNS: list = []
    READONLY_BG_COLOR: str = UITheme.READONLY_BG

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            self._paste_from_clipboard()
            event.accept()
            return
        super().keyPressEvent(event)

    def _paste_from_clipboard(self):
        """클립보드에서 붙여넣기"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            return

        start_row = self.currentRow()
        start_col = self.currentColumn()

        if start_row < 0:
            start_row = 0
        if start_col < 0:
            start_col = 0

        lines = text.strip().split('\n')

        for row_offset, line in enumerate(lines):
            cells = line.split('\t')
            target_row = start_row + row_offset

            while target_row >= self.rowCount():
                self._add_empty_row()

            for col_offset, value in enumerate(cells):
                target_col = start_col + col_offset
                if target_col < self.columnCount():
                    item = self.item(target_row, target_col)
                    if item is None:
                        item = QTableWidgetItem("")
                        self.setItem(target_row, target_col, item)
                    if item.flags() & Qt.ItemIsEditable:
                        item.setText(value.strip())

        logger.info(f"붙여넣기 완료: {len(lines)}행")

    def _add_empty_row(self):
        """빈 행 추가 (서브클래스에서 오버라이드 가능)"""
        row = self.rowCount()
        self.insertRow(row)
        for c in range(self.columnCount()):
            item = QTableWidgetItem("")
            if c in self.READONLY_COLUMNS:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QColor(self.READONLY_BG_COLOR))
            self.setItem(row, c, item)


class PasteableTableWidget(BasePasteableTableWidget):
    """자재 테이블용 붙여넣기 지원 테이블 (이론계량 컬럼 읽기전용)"""
    READONLY_COLUMNS = [3]


class PasteableSimpleTableWidget(BasePasteableTableWidget):
    """일괄 생성용 테이블 (단순 붙여넣기, 모든 컬럼 편집 가능)"""
    READONLY_COLUMNS = []
