"""

메인 윈도우

기존 파일이 손상되어 최소 기능으로 재구성했습니다.

 - 작업자 선택 다이얼로그

 - 기록 조회 다이얼로그 열기

 - 상태바에 정보 표시(스케일/허용오차)

필요 시 이후 단계에서 원래 기능을 확장 복원할 수 있습니다.

"""

from dataclasses import dataclass, field

from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QCursor, QKeySequence, QShortcut
from qfluentwidgets import (
    FluentWindow,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
    NavigationDisplayMode,
    setTheme, Theme  # 테마 설정 추가
)
from ui.styles import UIStyles  # 프리미엄 스타일 임포트
from ui.components import center_window
from ui.builders import build_action_page, build_mixing_page, build_settings_page
from ui.controllers import RecipeController, PanelSignalBinder, StatusController, SaveController
from typing import Callable, Tuple

from models.data_manager import DataManager
from models.dhr_database import DhrDatabaseManager
from models.lot_manager import LotManager
from config.settings import LOT_FILE
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


@dataclass
class AppServices:
    data_manager: DataManager
    dhr_db: DhrDatabaseManager
    lot_manager: LotManager


@dataclass
class DhrUiSettingsState:
    scan_effects: dict = field(default_factory=dict)
    signature: dict = field(default_factory=dict)


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

        self.services = self._create_services()
        self.data_manager = self.services.data_manager
        self._sidebar_hover_expand_enabled = bool(config.sidebar_hover_expand)
        self._nav_hover_expanded = False
        self._nav_hover_collapse_timer = QTimer(self)
        self._nav_hover_collapse_timer.setSingleShot(True)
        self._nav_hover_collapse_timer.setInterval(200)
        self._nav_hover_collapse_timer.timeout.connect(self._collapse_navigation_after_hover)
        self._nav_hover_poll_timer = QTimer(self)
        self._nav_hover_poll_timer.setInterval(120)
        self._nav_hover_poll_timer.timeout.connect(self._poll_sidebar_hover_state)
        # self.worker_name = None # WorkInfoPanel에서 관리됨

        self._init_ui()
        self._setup_shortcuts()
        self._load_recipes()
        
        # 작업자 선택 - 취소 시 앱 종료
        worker = self.work_info_panel.request_worker_input(initial=True)
        if not worker:
            self.hide()
            QTimer.singleShot(0, self._exit_app)
            return

        self._update_backup_status()

    def _create_services(self) -> AppServices:
        """앱에서 공유하는 서비스/매니저를 한 곳에서 생성합니다."""
        return AppServices(
            data_manager=DataManager(),
            dhr_db=DhrDatabaseManager(),
            lot_manager=LotManager(LOT_FILE),
        )

    def _exit_app(self):
        """앱 종료"""
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def is_sidebar_hover_expand_enabled(self) -> bool:
        return bool(self._sidebar_hover_expand_enabled)

    def _set_sidebar_hover_expand_enabled(self, enabled: bool, persist: bool = True) -> None:
        enabled = bool(enabled)
        self._sidebar_hover_expand_enabled = enabled
        if persist:
            config.save_sidebar_hover_expand(enabled)

        if not enabled:
            self._nav_hover_collapse_timer.stop()
            self._nav_hover_poll_timer.stop()
            if self._nav_hover_expanded:
                self._collapse_navigation_after_hover(force=True)
        elif hasattr(self, "navigationInterface"):
            self._nav_hover_poll_timer.start()

    def _init_sidebar_hover_behavior(self) -> None:
        nav = getattr(self, "navigationInterface", None)
        if nav is None:
            return

        nav.setCollapsible(True)
        panel = getattr(nav, "panel", None)
        hover_widgets = [nav]
        if panel is not None:
            hover_widgets.append(panel)
            hover_widgets.extend(panel.findChildren(QWidget))

        # Install on all sidebar descendants because mouse enter/leave is often
        # received by internal scroll/viewport widgets instead of the panel.
        self._nav_hover_filter_widgets = []
        seen = set()
        for widget in hover_widgets:
            if widget is None:
                continue
            key = id(widget)
            if key in seen:
                continue
            seen.add(key)
            widget.installEventFilter(self)
            self._nav_hover_filter_widgets.append(widget)

        if self._sidebar_hover_expand_enabled:
            self._nav_hover_poll_timer.start()

    def eventFilter(self, obj, e):
        nav = getattr(self, "navigationInterface", None)
        panel = getattr(nav, "panel", None) if nav else None
        hover_widgets = getattr(self, "_nav_hover_filter_widgets", ())

        if obj in hover_widgets or obj in (nav, panel):
            et = e.type()
            if et == QEvent.Enter:
                self._on_sidebar_hover_enter()
            elif et == QEvent.Leave:
                self._on_sidebar_hover_leave()

        return super().eventFilter(obj, e)

    def _on_sidebar_hover_enter(self) -> None:
        if not self._sidebar_hover_expand_enabled:
            return

        self._nav_hover_collapse_timer.stop()

        nav = getattr(self, "navigationInterface", None)
        panel = getattr(nav, "panel", None) if nav else None
        if nav is None or panel is None:
            return

        # `displayMode` can be unreliable for hover checks in some runtime states
        # (e.g. AUTO/MENU transitions). Treat a narrow panel as visually collapsed.
        is_visually_collapsed = (
            panel.width() <= 60
            or panel.displayMode in (NavigationDisplayMode.COMPACT, NavigationDisplayMode.MINIMAL)
        )
        if not is_visually_collapsed:
            return

        try:
            nav.expand()
            self._nav_hover_expanded = True
        except Exception as e:
            logger.debug(f"sidebar hover expand skipped: {e}")

    def _on_sidebar_hover_leave(self) -> None:
        if not self._sidebar_hover_expand_enabled or not self._nav_hover_expanded:
            return
        # Polling runs every 120ms; restarting a 220ms single-shot timer on every
        # tick prevents timeout from ever firing. Start only once per leave phase.
        if not self._nav_hover_collapse_timer.isActive():
            self._nav_hover_collapse_timer.start()

    def _is_cursor_in_sidebar(self) -> bool:
        nav = getattr(self, "navigationInterface", None)
        panel = getattr(nav, "panel", None) if nav else None
        if nav is None or panel is None:
            return False

        # Prefer Qt's hover state on actual descendants. This avoids global
        # coordinate mismatches and catches scroll/viewport children.
        hover_widgets = getattr(self, "_nav_hover_filter_widgets", ())
        for widget in hover_widgets:
            if widget is None or not widget.isVisible():
                continue
            try:
                if widget.underMouse():
                    return True
            except RuntimeError:
                # Widget can be deleted during shutdown/tab rebuild.
                continue

        global_pos = QCursor.pos()
        try:
            if panel.isVisible() and panel.rect().contains(panel.mapFromGlobal(global_pos)):
                return True
        except RuntimeError:
            pass

        try:
            if nav.isVisible() and nav.rect().contains(nav.mapFromGlobal(global_pos)):
                return True
        except RuntimeError:
            pass

        return False

    def _poll_sidebar_hover_state(self) -> None:
        if not self._sidebar_hover_expand_enabled or not self.isVisible():
            return

        if self._is_cursor_in_sidebar():
            self._on_sidebar_hover_enter()
        elif self._nav_hover_expanded:
            self._on_sidebar_hover_leave()

    def _collapse_navigation_after_hover(self, force: bool = False) -> None:
        if not self._nav_hover_expanded:
            return

        nav = getattr(self, "navigationInterface", None)
        panel = getattr(nav, "panel", None) if nav else None
        if nav is None or panel is None:
            self._nav_hover_expanded = False
            return

        if not force and self._is_cursor_in_sidebar():
            return

        if panel.displayMode in (NavigationDisplayMode.EXPAND, NavigationDisplayMode.MENU):
            try:
                panel.collapse()
            except Exception as e:
                logger.debug(f"sidebar hover collapse skipped: {e}")

        self._nav_hover_expanded = False

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
        self._init_sidebar_hover_behavior()
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
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(
            self._request_worker_and_refresh
        )

    def _create_central_widget(self):
        """중앙 위젯 생성"""
        # 1. 패널 객체 생성 (시그널 연결 전에)
        self._create_panels()

        # 2. 배합 페이지 (메인 작업 화면 - 첫 화면)
        mixing, self.mixing_page_refs = build_mixing_page(self)
        self.mixing_status_bar = self.mixing_page_refs.status_bar
        self.addSubInterface(mixing, FIF.MIX_VOLUMES, "배합")

        # 3. 수기 입력 (Manual Input)
        self.manual_interface = ManualInputInterface(
            self,
            dhr_db=self.services.dhr_db,
            lot_manager=self.services.lot_manager,
        )
        self.addSubInterface(self.manual_interface, FIF.EDIT, "수기 입력")

        # 4. 일괄 생성 (Bulk)
        self.bulk_interface = BulkCreationInterface(
            self,
            dhr_db=self.services.dhr_db,
            lot_manager=self.services.lot_manager,
        )
        self.addSubInterface(self.bulk_interface, FIF.PASTE, "일괄 생성")

        # 5. DHR 관리 (Recipe Management)
        self.recipe_interface = RecipeManagementInterface(
            self,
            dhr_db=self.services.dhr_db,
        )
        self.addSubInterface(self.recipe_interface, FIF.LIBRARY, "DHR 관리")

        # 5-1. DHR 설정 패널 상태 동기화 (메인/수기/일괄)
        self._setup_dhr_settings_sync()

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

    def _setup_dhr_settings_sync(self) -> None:
        """메인/수기/일괄 DHR 설정 패널의 값을 동기화합니다."""
        self._dhr_settings_syncing = False
        self._dhr_settings_pairs = [
            (self.scan_effects_panel, self.signature_panel),
            (self.manual_interface.scan_effects_panel, self.manual_interface.signature_panel),
            (self.bulk_interface.scan_effects_panel, self.bulk_interface.signature_panel),
        ]
        self.dhr_ui_settings_state = DhrUiSettingsState(
            scan_effects=dict(self.scan_effects_panel.get_data()),
            signature=dict(self.signature_panel.get_data()),
        )

        for scan_panel, signature_panel in self._dhr_settings_pairs:
            self._bind_dhr_settings_pair(scan_panel, signature_panel)

        self._apply_dhr_settings_to_all()

    def _bind_dhr_settings_pair(self, scan_panel, signature_panel) -> None:
        scan_signals = (
            scan_panel.dpi_spin.valueChanged,
            scan_panel.noise_spin.valueChanged,
            scan_panel.blur_spin.valueChanged,
            scan_panel.contrast_spin.valueChanged,
            scan_panel.brightness_spin.valueChanged,
        )
        for signal in scan_signals:
            signal.connect(lambda *_args, p=scan_panel: self._on_scan_effects_panel_changed(p))

        signature_signals = (
            signature_panel.chk_charge.toggled,
            signature_panel.chk_review.toggled,
            signature_panel.chk_approve.toggled,
        )
        for signal in signature_signals:
            signal.connect(lambda *_args, p=signature_panel: self._on_signature_panel_changed(p))

    def _apply_dhr_settings_to_all(self) -> None:
        if getattr(self, "_dhr_settings_syncing", False):
            return

        self._dhr_settings_syncing = True
        try:
            for scan_panel, signature_panel in self._dhr_settings_pairs:
                scan_panel.set_data(self.dhr_ui_settings_state.scan_effects)
                signature_panel.set_data(self.dhr_ui_settings_state.signature)
        finally:
            self._dhr_settings_syncing = False

    def _on_scan_effects_panel_changed(self, source_panel) -> None:
        if getattr(self, "_dhr_settings_syncing", False):
            return
        self.dhr_ui_settings_state.scan_effects = dict(source_panel.get_data())
        self._apply_dhr_settings_to_all()

    def _on_signature_panel_changed(self, source_panel) -> None:
        if getattr(self, "_dhr_settings_syncing", False):
            return
        self.dhr_ui_settings_state.signature = dict(source_panel.get_data())
        self._apply_dhr_settings_to_all()

    def _connect_panel_signals(self):
        """패널 간 시그널 연결"""
        binder = PanelSignalBinder(self.recipe_panel, self.work_info_panel, self.material_panel)
        binder.bind({
            "on_recipe_changed": self._on_recipe_changed,
            "on_amount_changed": self._recalc_theory,
            "on_amount_confirmed": lambda: self.material_panel.focus_first_cell(),
            "on_amount_check_failed": self.recipe_panel.focus_amount,
            "on_validation_changed": self._update_actions_enabled,
            "on_table_edit_finished": self._handle_table_edit_finished,
            "on_reset_requested": self.recipe_panel.reset,
        })

    def _handle_table_edit_finished(self) -> None:
        """테이블 편집 완료 시 저장 요청(버튼 클릭 우회 금지)."""
        if not self.mixing_page_refs.save_btn.isEnabled():
            return
        self._save_record()
    
    def _setup_statusbar(self):
        """상태바 초기화"""
        tol = config.tolerance
        scale = config.default_scale
        self._set_status_message(f"기본 스케일: {scale} | 허용오차: ±{tol}")
        
        self.google_sheets_status_label = QLabel("")
        self.mixing_status_bar.addPermanentWidget(self.google_sheets_status_label)
        self.google_sheets_status_label.setStyleSheet("padding: 0 5px;")
        self.status_controller = StatusController(
            status_bar=self.mixing_status_bar,
            google_sheets_label=self.google_sheets_status_label,
            google_sheets_config=self.data_manager.google_sheets_config,
        )



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
        elif hasattr(self, "mixing_status_bar"):
            self.mixing_status_bar.showMessage(message)

    def _request_worker_and_refresh(self):
        self.work_info_panel.request_worker_input(initial=False)

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
        save_btn = self.mixing_page_refs.save_btn
        save_btn.setEnabled(enabled)
        save_btn.setText("배합 저장")
        save_btn.setStyleSheet(UIStyles.get_primary_button_style())

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
