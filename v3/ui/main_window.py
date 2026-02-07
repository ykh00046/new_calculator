"""

메인 윈도우

기존 파일이 손상되어 최소 기능으로 재구성했습니다.

 - 작업자 선택 다이얼로그

 - 기록 조회 다이얼로그 열기

 - 상태바에 정보 표시(스케일/허용오차)

필요 시 이후 단계에서 원래 기능을 확장 복원할 수 있습니다.

"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from qfluentwidgets import (
    FluentWindow,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
    setTheme, Theme  # 테마 설정 추가
)
from ui.styles import UIStyles  # 프리미엄 스타일 임포트
from ui.components import StatusBar, center_window
from ui.builders import build_action_page, build_mixing_page, build_settings_page
from ui.controllers import RecipeController, PanelSignalBinder, StatusController, SaveController
from typing import Callable, Tuple

from models.data_manager import DataManager
from ui.record_view_dialog import RecordViewDialog
from utils.logger import logger
from config.config_manager import config
from ui.panels.scan_effects_panel import ScanEffectsPanel
from ui.panels.signature_panel import SignaturePanel
from ui.panels.work_info_panel import WorkInfoPanel
from ui.panels.recipe_panel import RecipePanel
from ui.panels.material_table_panel import MaterialTablePanel
from ui.dialogs.pdf_signature_settings_dialog import PdfSignatureSettingsDialog
from ui.panels.manual_input_interface import ManualInputInterface
from ui.panels.recipe_management_interface import RecipeManagementInterface
from ui.panels.bulk_creation_interface import BulkCreationInterface

class MainWindow(FluentWindow):
    """애플리케이션 메인 윈도우(복구 버전)"""

    def __init__(self):
        super().__init__()
        
        # 테마 설정 (UI 생성 전)
        setTheme(Theme.DARK)
        
        self.setWindowTitle("DHR 배합 프로그램")
        self.resize(1200, 800) # Window size increased
        # 창 항상 맨 위 설정
        if config.get("ui.window_stays_on_top", True):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.data_manager = DataManager()
        # self.worker_name = None # WorkInfoPanel에서 관리됨

        self._init_ui()
        self._setup_shortcuts()
        self._load_recipes()
        
        # 작업자 선택 - 취소 시 앱 종료
        worker = self.work_info_panel.request_worker_input(initial=True)
        if not worker:
            # __init__에서는 QApplication.quit()이 바로 동작하지 않음
            # QTimer.singleShot으로 이벤트 루프 후 종료
            from PySide6.QtCore import QTimer
            self.hide()
            QTimer.singleShot(0, self._exit_app)
            return
        self._refresh_dashboard()
        
        self._update_backup_status() # 초기 백업 상태 업데이트

    def _exit_app(self):
        """앱 종료"""
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    # ─────────────── InfoBar 알림 헬퍼 ───────────────
    def show_success(self, title: str, content: str, duration: int = 2000):
        """성공 토스트 알림"""
        InfoBar.success(
            title=title,
            content=content,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration
        )
    
    def show_warning(self, title: str, content: str, duration: int = 3000):
        """경고 토스트 알림"""
        InfoBar.warning(
            title=title,
            content=content,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration
        )
    
    def show_error(self, title: str, content: str, duration: int = 4000):
        """에러 토스트 알림"""
        InfoBar.error(
            title=title,
            content=content,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration
        )
    
    def show_info(self, title: str, content: str, duration: int = 2500):
        """정보 토스트 알림"""
        InfoBar.info(
            title=title,
            content=content,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration
        )

    def _init_ui(self):
        """UI 초기화 - 리팩토링된 구조"""
        # Mica 효과 비활성화 (순수 배경색 사용을 위해)
        self.setMicaEffectEnabled(False)
        
        # 글로벌 스타일 적용 (SSOT)
        self.setStyleSheet(UIStyles.get_main_style())
        
        self._create_central_widget()
        self._setup_statusbar()

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_has_centered", False):
            center_window(self)
            self._has_centered = True

    def _setup_shortcuts(self):
        """단축키 설정"""
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._save_record)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self._clear_table)
        QShortcut(QKeySequence("F5"), self).activated.connect(self._refresh_dashboard)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(
            self._request_worker_and_refresh
        )

    def _create_central_widget(self):
        """중앙 위젯 생성"""
        # 1. 패널 객체 생성 (시그널 연결 전에)
        self._create_panels()

        # 2. 배합 페이지 (메인 작업 화면 - 첫 화면)
        mixing = build_mixing_page(self)
        self.addSubInterface(mixing, FIF.EDIT, "배합")

        # 3. 수기 입력 (Manual Input)
        self.manual_interface = ManualInputInterface(self)
        self.addSubInterface(self.manual_interface, FIF.EDIT, "수기 입력")

        # 4. 일괄 생성 (Bulk)
        self.bulk_interface = BulkCreationInterface(self)
        self.addSubInterface(self.bulk_interface, FIF.DOCUMENT, "일괄 생성")

        # 5. DHR 관리 (Recipe Management)
        self.recipe_interface = RecipeManagementInterface(self)
        self.addSubInterface(self.recipe_interface, FIF.SETTING, "DHR 관리")

        # 6. 기록 조회
        records_page = build_action_page(
            "기록 조회",
            "저장된 배합 기록을 검색하고 출력합니다.",
            "기록 조회 열기",
            self._open_records,
            "RecordsPage",
        )
        self.addSubInterface(records_page, FIF.HISTORY, "기록 조회")

        # 7. 설정 페이지
        settings = build_settings_page(self)
        self.addSubInterface(settings, FIF.SETTING, "설정")

        # 8. 작업자 변경
        worker_page = build_action_page(
            "작업자 변경",
            "현재 작업자를 변경합니다.",
            "작업자 변경",
            self._request_worker_and_refresh,
            "WorkerPage",
        )
        self.addSubInterface(worker_page, FIF.PEOPLE, "작업자 변경")

        # 시그널 연결
        self._connect_panel_signals()

    def _create_panels(self):
        """모든 패널 객체 생성"""
        # 레시피 패널
        self.recipe_panel = RecipePanel()
        
        # 작업 정보 패널
        self.work_info_panel = WorkInfoPanel()
        
        # 자재 테이블 패널
        self.material_panel = MaterialTablePanel(self.data_manager)
        self.material_panel.set_auto_assign_callback(self.auto_assign_lots)
        
        # PDF/서명 패널 (다이얼로그에서 사용)
        self.scan_effects_panel = ScanEffectsPanel()
        self.signature_panel = SignaturePanel()

        self.recipe_controller = RecipeController(
            data_manager=self.data_manager,
            recipe_panel=self.recipe_panel,
            material_panel=self.material_panel,
            on_recipe_loaded=lambda _n: None,
            on_recipe_cleared=self._handle_recipe_cleared,
            on_after_load=self._after_recipe_loaded,
            on_error=self._set_status_message,
        )

        self.save_controller = SaveController(
            data_manager=self.data_manager,
            recipe_panel=self.recipe_panel,
            work_info_panel=self.work_info_panel,
            material_panel=self.material_panel,
            signature_panel=self.signature_panel,
            scan_effects_panel=self.scan_effects_panel,
            validate_inputs=self._validate_inputs,
            on_validation_error=self._handle_save_validation_error,
            on_success=self._handle_save_success,
        )

    def _connect_panel_signals(self):
        """패널 간 시그널 연결"""
        binder = PanelSignalBinder(self.recipe_panel, self.work_info_panel, self.material_panel)
        binder.bind({
            "on_recipe_changed": self._on_recipe_changed,
            "on_amount_changed": self._recalc_theory,
            "on_amount_confirmed": lambda: self.material_panel.focus_first_cell(),
            "on_refresh_dashboard": self._refresh_dashboard,
            "on_amount_check_failed": self.recipe_panel.focus_amount,
            "on_validation_changed": self._update_actions_enabled,
            "on_table_edit_finished": lambda: self.save_btn.click(),
            "on_reset_requested": self.recipe_panel.reset,
        })
    
    def _refresh_dashboard(self) -> None:
        if not hasattr(self, "card_recipe") or not hasattr(self, "header_subtitle"):
            return
        recipe, amount, worker, date = self._collect_kpi_data()
        self._update_kpi_cards(recipe, amount, worker, date)
        self._update_header_subtitle(worker, date)

    def _collect_kpi_data(self) -> Tuple[str, float, str, str]:
        recipe = self.recipe_panel.get_recipe_name() or "-"
        amount = self.recipe_panel.get_amount()
        worker = self.work_info_panel.get_worker_name() or "-"
        date = self.work_info_panel.date_edit.date().toString("yyyy-MM-dd")
        return recipe, amount, worker, date

    def _update_kpi_cards(self, recipe: str, amount: float, worker: str, date: str) -> None:
        self.card_recipe["card"].update_value(recipe, 100 if recipe != "-" else 0)
        self.card_amount["card"].update_value(f"{amount:,.2f}", 100 if amount > 0 else 0)
        self.card_worker["value"].setText(f"{worker} · {date}")

    def _update_header_subtitle(self, worker: str, date: str) -> None:
        self.header_subtitle.setText(f"{worker} · {date}")

    def _setup_statusbar(self):
        """상태바 초기화"""
        tol = config.tolerance
        scale = config.default_scale
        self._set_status_message(f"기본 스케일: {scale} | 허용오차: ±{tol}")
        
        self.google_sheets_status_label = QLabel("")
        self.statusBar().addPermanentWidget(self.google_sheets_status_label)
        self.google_sheets_status_label.setStyleSheet("padding: 0 5px;")
        self.status_controller = StatusController(
            status_bar=self.statusBar(),
            google_sheets_label=self.google_sheets_status_label,
            google_sheets_config=self.data_manager.google_sheets_config,
        )

    def statusBar(self):
        return self._status_bar



    def _open_google_sheets_settings(self):
        """Google Sheets 설정 다이얼로그를 엽니다."""
        def _action():
            from ui.dialogs.google_sheets_settings_dialog import GoogleSheetsSettingsDialog
            dlg = GoogleSheetsSettingsDialog(self)
            dlg.settings_updated.connect(self._update_backup_status)  # 설정 변경 시 상태 업데이트
            dlg.exec()

        self._run_dialog_action("open_google_sheets_settings", _action)
        
    def _update_backup_status(self):
        """Google Sheets 백업 상태를 업데이트합니다."""
        self.status_controller.update_backup_status()

    def _set_status_message(self, message: str) -> None:
        if hasattr(self, "status_controller"):
            self.status_controller.set_message(message)
        else:
            self.statusBar().showMessage(message)

    def _request_worker_and_refresh(self):
        worker = self.work_info_panel.request_worker_input(initial=False)
        if worker:
            self._refresh_dashboard()

    def _clear_table(self):
        """테이블 자재LOT 및 실제배합 입력값 초기화"""
        logger.info("테이블 입력 초기화 시작.")
        self.material_panel.clear_table()
        self._update_actions_enabled(False)
        self._set_status_message("테이블이 초기화되었습니다.")
        logger.info("테이블 초기화 완료.")

    def auto_assign_lots(self):
        """자재별로 작업일자 기준 적합한 자재LOT을 자동배정합니다."""
        work_date = self.work_info_panel.get_data().get("work_date")
        logger.info(f"자동 LOT 배정 시작 (작업일자: {work_date})")
        self.material_panel.auto_assign_lots(work_date)
        self._set_status_message("자동 LOT 배정 완료")

    def _open_records(self):
        def _action():
            effects_params = self.scan_effects_panel.get_data()
            dlg = RecordViewDialog(self.data_manager, effects_params, self)
            dlg.exec()

        self._run_dialog_action("open_records", _action)

    def _open_pdf_settings(self):
        """PDF/서명 설정 다이얼로그 열기"""
        def _action():
            if hasattr(self, '_pdf_settings_dialog') and self._pdf_settings_dialog.isVisible():
                self._pdf_settings_dialog.raise_()
                self._pdf_settings_dialog.activateWindow()
                return

            self._pdf_settings_dialog = PdfSignatureSettingsDialog(
                self.scan_effects_panel,
                self.signature_panel,
                self
            )
            self._pdf_settings_dialog.show()
        self._run_dialog_action("open_pdf_settings", _action)

    def _run_dialog_action(self, context: str, action: Callable[[], None]) -> None:
        try:
            action()
        except Exception as e:
            logger.log_error_with_context(e, {"context": context})

    def _load_recipes(self):
        """레시피 목록 로드"""
        self.recipe_controller.load_recipes()

    def _on_recipe_changed(self, recipe_name: str):
        self.recipe_controller.on_recipe_changed(recipe_name)

    def _after_recipe_loaded(self) -> None:
        self._recalc_theory()
        self._update_actions_enabled(False)

    def _recalc_theory(self):
        """배합량 변경시 이론 계량값을 재계산"""
        amount = self.recipe_panel.get_amount()
        self.material_panel.update_theory(amount)

    def _update_actions_enabled(self, valid: bool):
        self._set_save_button_state(valid)

    def _set_save_button_state(self, enabled: bool) -> None:
        self.save_btn.setEnabled(enabled)
        if enabled:
            self.save_btn.setText("배합 저장")
            self.save_btn.setStyleSheet(UIStyles.get_primary_button_style())
        else:
            self.save_btn.setText("배합 저장")
            self.save_btn.setStyleSheet(UIStyles.get_primary_button_style())

    def _handle_recipe_cleared(self) -> None:
        self.material_panel.clear_items()
        self._update_actions_enabled(False)

    def _validate_inputs(self) -> Tuple[bool, str]:
        materials_data = self.material_panel.get_data()
        return self.data_manager.validate_record_inputs(
            worker_name=self.work_info_panel.get_worker_name(),
            recipe_name=self.recipe_panel.get_recipe_name(),
            mixing_amount=self.recipe_panel.get_amount(),
            materials_data=materials_data,
        )

    def _save_record(self):
        try:
            self.save_controller.save_record()
        except Exception as e:
            self._handle_save_error(e)

    def _handle_save_validation_error(self, error_msg: str) -> None:
        self._set_status_message(error_msg)
        self.show_warning("입력 오류", error_msg)

    def _handle_save_success(self, lot: str) -> None:
        self._set_status_message(
            f"배합 저장 (DB/백업): LOT {lot} | 엑셀/PDF 출력은 '기록 조회' 화면을 이용하세요."
        )
        logger.info(f"배합 완료: LOT {lot}")
        self.show_success("저장 완료", f"LOT: {lot} 저장이 완료되었습니다.")
        self.material_panel.clear_table()
        reset_mode = config.get("ui.save_reset_mode", "safe")
        if reset_mode == "safe":
            self.recipe_panel.reset()
        self._update_actions_enabled(False)

    def _handle_save_error(self, error: Exception) -> None:
        logger.log_error_with_context(error, {"context": "save_record"})
        self._set_status_message("저장 중 오류가 발생했습니다.")
        self.show_error("저장 실패", f"저장 중 오류가 발생했습니다: {error}")
