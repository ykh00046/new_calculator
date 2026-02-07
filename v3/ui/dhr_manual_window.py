"""
DHR 수동 관리 창 - 빈 테이블로 배합일지 작성
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QTableWidgetItem, QHeaderView,
    QMessageBox, QTabWidget, QApplication
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor, QKeySequence
from datetime import datetime, timedelta
from models.lot_manager import LotManager
from config.settings import LOT_FILE

from ui.components import StyledButton, create_group_box
from ui.styles import UIStyles, UITheme
from ui.panels.scan_effects_panel import ScanEffectsPanel
from ui.panels.signature_panel import SignaturePanel
from config.config_manager import config
from utils.logger import logger
from models.dhr_database import DhrDatabaseManager
from models.dhr_bulk_generator import DhrBulkGenerator
from qfluentwidgets import FluentWindow, CardWidget, LineEdit, DoubleSpinBox, DateEdit, TimeEdit, CheckBox, TableWidget, FluentIcon as FIF, setTheme, Theme, setThemeColor
from ui.styles import UITheme


class BasePasteableTableWidget(TableWidget):
    """엑셀 붙여넣기 지원 기반 테이블 클래스"""
    
    # 자동계산 컬럼 설정 (서브클래스에서 오버라이드)
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
            
            # 필요하면 행 추가
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
    READONLY_COLUMNS = [3]  # 이론계량 자동계산


class PasteableSimpleTableWidget(BasePasteableTableWidget):
    """일괄 생성용 테이블 (단순 붙여넣기, 모든 컬럼 편집 가능)"""
    READONLY_COLUMNS = []


class DHRManualWindow(FluentWindow):
    """DHR 수동 배합일지 작성 창"""

    def __init__(self, worker_name: str, parent=None):
        super().__init__(parent)
        self.worker_name = worker_name
        setTheme(Theme.DARK)
        setThemeColor(UITheme.MINT_ACCENT)
        self.dhr_db = DhrDatabaseManager()  # DHR 전용 DB
        self.lot_manager = LotManager(LOT_FILE)
        self.setWindowTitle(f"DHR 관리 - {worker_name}")
        self.resize(1200, 800)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        central = QWidget()
        central.setObjectName("DHRManual")
        root = QVBoxLayout()
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)

        # 상단: 작업 정보 (왼쪽) + 제품 정보 (오른쪽)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        
        # 작업 정보 (왼쪽)
        work_group = CardWidget()
        work_container = QVBoxLayout(work_group)
        work_container.setContentsMargins(16, 12, 16, 12)
        work_container.setSpacing(8)
        work_title = QLabel("작업 정보")
        work_container.addWidget(work_title)

        work_layout = QHBoxLayout()
        
        work_layout.addWidget(QLabel("작업일자:"))
        self.date_edit = DateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        work_layout.addWidget(self.date_edit)
        
        work_layout.addWidget(QLabel("작업시간:"))
        self.time_edit = TimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        work_layout.addWidget(self.time_edit)
        
        self.chk_include_time = CheckBox("엑셀에 시간 표시")
        self.chk_include_time.setToolTip("일괄 생성 시 09시+랜덤 분부터 시작, 동일 날짜는 20~40분 가산")
        self.chk_include_time.setChecked(True)
        work_layout.addWidget(self.chk_include_time)
        
        work_container.addLayout(work_layout)
        top_layout.addWidget(work_group)
        
        # 제품 정보 (오른쪽)
        product_group = CardWidget()
        product_container = QVBoxLayout(product_group)
        product_container.setContentsMargins(16, 12, 16, 12)
        product_container.setSpacing(8)
        product_title = QLabel("제품 정보")
        product_container.addWidget(product_title)
        
        product_layout = QHBoxLayout()
        
        product_layout.addWidget(QLabel("제품명:"))
        self.product_name_edit = LineEdit()
        self.product_name_edit.setPlaceholderText("제품명을 입력하세요")
        product_layout.addWidget(self.product_name_edit)
        
        product_layout.addWidget(QLabel("제품LOT:"))
        self.product_lot_edit = LineEdit()
        self.product_lot_edit.setReadOnly(True)
        product_layout.addWidget(self.product_lot_edit)
        
        product_layout.addWidget(QLabel("배합량(g):"))
        self.amount_spin = DoubleSpinBox()
        self.amount_spin.setRange(0, 9999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(0)
        product_layout.addWidget(self.amount_spin)
        
        product_container.addLayout(product_layout)
        top_layout.addWidget(product_group)
        
        root.addLayout(top_layout)


        # 일괄 생성 입력 (Ctrl+V)
        bulk_group = CardWidget()
        bulk_container = QVBoxLayout(bulk_group)
        bulk_container.setContentsMargins(16, 12, 16, 12)
        bulk_layout = QVBoxLayout()

        guide_label = QLabel("입력 형식: 작업일자(YYYY-MM-DD 또는 엑셀 날짜) / 배합량(g)")
        guide_label.setStyleSheet(f"color: {UITheme.TEXT_SECONDARY}; font-size: 13px;")
        bulk_layout.addWidget(guide_label)


        self.bulk_table = PasteableSimpleTableWidget()
        self.bulk_table.setColumnCount(2)
        self.bulk_table.setHorizontalHeaderLabels(["작업일자", "배합량(g)"])
        self.bulk_table.setRowCount(1)
        bulk_header = self.bulk_table.horizontalHeader()
        bulk_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        bulk_header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        # 스타일 적용
        self.bulk_table.setStyleSheet(UIStyles.get_table_style())
        self.bulk_table.setAlternatingRowColors(True)
        self.bulk_table.verticalHeader().setVisible(False)

        bulk_layout.addWidget(self.bulk_table)

        bulk_btn_layout = QHBoxLayout()
        bulk_add_btn = StyledButton("행 추가")
        bulk_add_btn.clicked.connect(self._add_bulk_row)
        bulk_btn_layout.addWidget(bulk_add_btn)

        bulk_remove_btn = StyledButton("행 삭제")
        bulk_remove_btn.clicked.connect(self._remove_bulk_row)
        bulk_btn_layout.addWidget(bulk_remove_btn)

        bulk_btn_layout.addStretch()

        bulk_generate_btn = StyledButton("일괄 생성", "success")
        bulk_generate_btn.clicked.connect(self._bulk_create)
        bulk_btn_layout.addWidget(bulk_generate_btn)

        bulk_layout.addLayout(bulk_btn_layout)
        bulk_container.addLayout(bulk_layout)
        root.addWidget(bulk_group)

        # 중앙: 탭 위젯 (설정)
        tabs = QTabWidget()
        
        # PDF/서명 설정 탭
        settings_tab = QWidget()
        settings_layout = QHBoxLayout()
        
        self.scan_effects_panel = ScanEffectsPanel()
        settings_layout.addWidget(create_group_box("PDF 스캔 효과", self.scan_effects_panel))
        
        self.signature_panel = SignaturePanel()
        settings_layout.addWidget(create_group_box("서명 옵션", self.signature_panel))
        
        settings_layout.addStretch()
        settings_tab.setLayout(settings_layout)
        tabs.addTab(settings_tab, "PDF/서명 설정")
        
        root.addWidget(tabs)

        # 자재 테이블 (붙여넣기 지원)
        table_group = CardWidget()
        table_container = QVBoxLayout(table_group)
        table_container.setContentsMargins(16, 12, 16, 12)
        table_layout = QVBoxLayout()
        
        self.table = PasteableTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "품목코드", "품목명", "배합비율(%)", "이론계량(g)", "실제배합(g)", "자재LOT"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setStyleSheet(UIStyles.get_table_style())
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        # 기본 행 추가
        self._add_row()
        
        table_layout.addWidget(self.table)
        
        # 테이블 버튼
        table_btn_layout = QHBoxLayout()
        
        add_row_btn = StyledButton("행 추가")
        add_row_btn.clicked.connect(self._add_row)
        table_btn_layout.addWidget(add_row_btn)
        
        remove_row_btn = StyledButton("행 삭제")
        remove_row_btn.clicked.connect(self._remove_row)
        table_btn_layout.addWidget(remove_row_btn)
        
        table_btn_layout.addStretch()
        table_layout.addLayout(table_btn_layout)
        
        table_container.addLayout(table_layout)
        root.addWidget(table_group)

        # 하단 버튼
        bottom = QHBoxLayout()
        
        record_view_btn = StyledButton("기록 조회", "secondary")
        record_view_btn.clicked.connect(self._open_record_view)
        bottom.addWidget(record_view_btn)
        
        bottom.addStretch()
        
        self.save_btn = StyledButton("저장 및 출력", "success")
        self.save_btn.clicked.connect(self._save_and_export)
        bottom.addWidget(self.save_btn)
        
        close_btn = StyledButton("닫기", "secondary")
        close_btn.clicked.connect(self.close)
        bottom.addWidget(close_btn)
        
        bottom.addStretch()
        root.addLayout(bottom)

        central.setLayout(root)
        self.addSubInterface(central, FIF.EDIT, "Manual Entry")

    def _connect_signals(self):
        """시그널 연결"""
        # 제품명 또는 날짜 변경 시 LOT 자동 생성
        self.product_name_edit.textChanged.connect(self._update_product_lot)
        self.date_edit.dateChanged.connect(self._update_product_lot)
        
        # 초기 LOT 생성
        self._update_product_lot()

    def _add_bulk_row(self):
        row = self.bulk_table.rowCount()
        self.bulk_table.insertRow(row)
        for c in range(self.bulk_table.columnCount()):
            self.bulk_table.setItem(row, c, QTableWidgetItem(""))

    def _remove_bulk_row(self):
        row = self.bulk_table.currentRow()
        if row >= 0:
            self.bulk_table.removeRow(row)
        elif self.bulk_table.rowCount() > 0:
            self.bulk_table.removeRow(self.bulk_table.rowCount() - 1)

    def _parse_date_cell(self, value: str) -> str:
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

    def _parse_bulk_entries(self):
        entries = []
        for r in range(self.bulk_table.rowCount()):
            date_item = self.bulk_table.item(r, 0)
            amount_item = self.bulk_table.item(r, 1)
            date_text = date_item.text().strip() if date_item else ""
            amount_text = amount_item.text().strip() if amount_item else ""

            if not date_text and not amount_text:
                continue

            if not date_text or not amount_text:
                raise ValueError(f"{r+1}행: 작업일자/배합량이 비어 있습니다.")

            work_date = self._parse_date_cell(date_text)
            if not work_date:
                raise ValueError(f"{r+1}행: 작업일자 형식을 인식할 수 없습니다.")

            try:
                amount = float(amount_text)
            except ValueError:
                raise ValueError(f"{r+1}행: 배합량이 숫자가 아닙니다.")

            if amount <= 0:
                raise ValueError(f"{r+1}행: 배합량이 0보다 커야 합니다.")

            entries.append({"date": work_date, "amount": amount, "row": r + 1})

        return entries

    def _get_materials_for_bulk(self):
        materials = []
        for r in range(self.table.rowCount()):
            code_item = self.table.item(r, 0)
            name_item = self.table.item(r, 1)
            ratio_item = self.table.item(r, 2)
            code = code_item.text().strip() if code_item else ""
            name = name_item.text().strip() if name_item else ""

            if not code and not name:
                continue

            if not code:
                raise ValueError(f"재료 {r+1}행: 품목코드가 비어 있습니다.")

            try:
                ratio = float(ratio_item.text()) if ratio_item else 0.0
            except ValueError:
                ratio = 0.0

            materials.append({"code": code, "name": name, "ratio": ratio})

        if not materials:
            raise ValueError("재료가 하나도 없어 진행할 수 없습니다. 테이블을 확인해 주세요.")

        return materials

    def _bulk_create(self):
        product_name = self.product_name_edit.text().strip()
        if not product_name:
            QMessageBox.warning(self, "입력 오류", "레시피를 먼저 선택하세요.")
            return

        try:
            entries = self._parse_bulk_entries()
            materials = self._get_materials_for_bulk()
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
            return

        if not entries:
            QMessageBox.warning(self, "입력 오류", "일괄 생성할 데이터가 없습니다.")
            return

        include_time = self.chk_include_time.isChecked()
        generator = DhrBulkGenerator(self.dhr_db, self.lot_manager)

        try:
            count = generator.generate(
                entries=entries,
                product_name=product_name,
                materials=materials,
                worker=self.worker_name,
                include_time=include_time,
                scan_effects=self.scan_effects_panel.get_data(),
                signature_options=self.signature_panel.get_data(),
                export=True
            )
            QMessageBox.information(self, "완료", f"일괄 생성이 완료되었습니다. (총 {count}건)")
        except Exception as e:
            logger.error(f"DHR 일괄 생성 실패: {e}")
            QMessageBox.critical(self, "오류", f"일괄 생성 중 오류가 발생했습니다.\n{e}")


    def _update_product_lot(self):
        """제품 LOT 자동 생성 (제품명 + YYMMDD)"""
        product_name = self.product_name_edit.text().strip()
        date = self.date_edit.date()
        
        if product_name:
            date_str = date.toString("yyMMdd")
            lot = f"{product_name}{date_str}"
            self.product_lot_edit.setText(lot)

    def _add_row(self):
        """행 추가"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        for col in range(6):
            item = QTableWidgetItem("")
            if col == 3:  # 이론계량 - 자동계산
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QColor(UITheme.READONLY_BG))
            self.table.setItem(row, col, item)

    def _remove_row(self):
        """현재 선택된 행 삭제"""
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
        elif self.table.rowCount() > 0:
            self.table.removeRow(self.table.rowCount() - 1)

    def _recalc_theory(self):
        """이론계량 재계산"""
        amount = self.amount_spin.value()  # 이미 g 단위
        
        for row in range(self.table.rowCount()):
            ratio_item = self.table.item(row, 2)
            if ratio_item:
                try:
                    ratio = float(ratio_item.text()) if ratio_item.text() else 0
                    theory = amount * (ratio / 100.0)
                    self.table.item(row, 3).setText(f"{theory:.3f}")
                except ValueError:
                    pass

    def _validate(self) -> bool:
        """입력 검증"""
        if not self.product_name_edit.text().strip():
            QMessageBox.warning(self, "입력 오류", "제품명을 입력하세요.")
            self.product_name_edit.setFocus()
            return False
        
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "입력 오류", "배합량을 입력하세요.")
            self.amount_spin.setFocus()
            return False
        
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "입력 오류", "자재를 최소 1개 이상 입력하세요.")
            return False
        
        return True

    def _save_and_export(self):
        """저장 및 엑셀/PDF 출력"""
        if not self._validate():
            return
        
        # 이론계량 재계산
        self._recalc_theory()
        
        # 데이터 수집
        data = self._collect_data()
        
        try:
            # 1. DB에 기록 저장
            record_data = {
                'product_lot': data['product_lot'],
                'product_name': data['product_name'],
                'worker': self.worker_name,
                'work_date': data['work_date'],
                'work_time': data['work_time'] if data['include_time'] else '',
                'total_amount': data['amount'],
                'scale': config.default_scale
            }
            
            details_data = []
            for name, mat in data['materials'].items():
                details_data.append({
                    'material_code': mat.get('품목코드', ''),
                    'material_name': mat.get('품목명', ''),
                    'material_lot': mat.get('LOT', ''),
                    'ratio': mat.get('배합비율', 0),
                    'theory_amount': mat.get('이론계량', 0),
                    'actual_amount': mat.get('실제배합', 0)
                })
            
            self.dhr_db.save_dhr_record(record_data, details_data)
            logger.info(f"DHR 기록 DB 저장 완료: {data['product_lot']}")
            
            # 2. 엑셀/PDF 생성
            from models.excel_handler import ExcelHandler
            from config.settings import BASE_PATH
            import os
            
            handler = ExcelHandler()
            
            # 엑셀 생성
            excel_path = handler.create_mixing_report(
                recipe_name=data['product_name'],
                work_date=data['work_date'],
                work_time=data['work_time'] if data['include_time'] else None,
                worker=self.worker_name,
                total_amount=data['amount'],
                product_lot=data['product_lot'],
                materials=data['materials'],
                scale=config.default_scale
            )
            
            if excel_path:
                # PDF 생성
                pdf_path = handler.convert_to_pdf(
                    excel_path,
                    scan_effects=self.scan_effects_panel.get_data(),
                    signature_options=self.signature_panel.get_data(),
                    worker_name=self.worker_name
                )
                
                msg = f"저장 완료!\n\n엑셀: {os.path.basename(excel_path)}"
                if pdf_path:
                    msg += f"\nPDF: {os.path.basename(pdf_path)}"
                
                QMessageBox.information(self, "완료", msg)
                logger.info(f"DHR 수동 저장 완료: {data['product_name']}")
            else:
                QMessageBox.critical(self, "오류", "엑셀 파일 생성에 실패했습니다.")
                
        except Exception as e:
            logger.error(f"DHR 저장 실패: {e}")
            QMessageBox.critical(self, "오류", f"저장 중 오류 발생:\n{str(e)}")

    def _open_record_view(self):
        """DHR 기록 조회 다이얼로그 열기"""
        from ui.dhr_record_view_dialog import DhrRecordViewDialog
        effects_params = self.scan_effects_panel.get_data()
        dialog = DhrRecordViewDialog(effects_params, self)
        dialog.exec()

    def _collect_data(self) -> dict:
        """테이블 데이터 수집"""
        materials = {}
        
        for row in range(self.table.rowCount()):
            code = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            if not code.strip():
                code = f"ITEM_{row+1}"
            
            materials[code] = {
                '품목코드': code,
                '품목명': self.table.item(row, 1).text() if self.table.item(row, 1) else "",
                '배합비율': self._to_float(self.table.item(row, 2).text() if self.table.item(row, 2) else "0"),
                '이론계량': self._to_float(self.table.item(row, 3).text() if self.table.item(row, 3) else "0"),
                '실제배합': self._to_float(self.table.item(row, 4).text() if self.table.item(row, 4) else "0"),
                'LOT': self.table.item(row, 5).text() if self.table.item(row, 5) else ""
            }
        
        return {
            'product_name': self.product_name_edit.text().strip(),
            'product_lot': self.product_lot_edit.text().strip(),
            'amount': self.amount_spin.value(),
            'work_date': self.date_edit.date().toString("yyyy-MM-dd"),
            'work_time': self.time_edit.time().toString("HH:mm:ss"),
            'include_time': self.chk_include_time.isChecked(),
            'materials': materials
        }

    def _to_float(self, s: str) -> float:
        try:
            return float(s.strip()) if s.strip() else 0.0
        except ValueError:
            return 0.0

    def load_recipe(self, recipe_data: dict, materials: list):
        """레시피 데이터로 테이블 채우기"""
        # 제품명 설정
        if recipe_data.get('recipe_name'):
            self.product_name_edit.setText(recipe_data['recipe_name'])
        
        # 기본 배합량 설정
        if recipe_data.get('default_amount'):
            self.amount_spin.setValue(recipe_data['default_amount'])
        
        # 테이블 초기화 후 자재 추가
        self.table.setRowCount(0)
        
        for mat in materials:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 품목코드
            self.table.setItem(row, 0, QTableWidgetItem(str(mat.get('material_code', ''))))
            # 품목명
            self.table.setItem(row, 1, QTableWidgetItem(str(mat.get('material_name', ''))))
            # 배합비율
            self.table.setItem(row, 2, QTableWidgetItem(str(mat.get('ratio', ''))))
            # 이론계량 (자동계산)
            theory_item = QTableWidgetItem("")
            theory_item.setFlags(theory_item.flags() & ~Qt.ItemIsEditable)
            theory_item.setBackground(QColor(UITheme.READONLY_BG))
            self.table.setItem(row, 3, theory_item)
            # 실제배합
            self.table.setItem(row, 4, QTableWidgetItem(""))
            # 자재LOT
            self.table.setItem(row, 5, QTableWidgetItem(""))
        
        # 이론계량 재계산
        self._recalc_theory()
        
        logger.info(f"레시피 로드 완료: {recipe_data.get('recipe_name', 'Unknown')}, 자재 {len(materials)}건")
