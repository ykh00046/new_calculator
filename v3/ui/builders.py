from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
from PySide6.QtCore import Qt
from qfluentwidgets import (
    CardWidget,
    CaptionLabel,
    SubtitleLabel,
    LargeTitleLabel,
    CommandBar,
    Action,
    FluentIcon as FIF,
)

from ui.components import MintInfoCard, StatusBar, StyledButton
from ui.styles import UITheme


def build_dashboard_page(window) -> QWidget:
    page = QWidget()
    page.setObjectName("DashboardPage")
    root = QVBoxLayout(page)
    root.setContentsMargins(36, 32, 36, 32)
    root.setSpacing(24)

    # Header with LargeTitleLabel + CommandBar
    header = CardWidget()
    header.setStyleSheet("background-color: transparent; border: none;")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(0, 0, 0, 12)

    # 타이틀 영역
    title_area = QVBoxLayout()
    title_area.setSpacing(4)
    title = LargeTitleLabel("DHR Mixing System")
    title.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY}; letter-spacing: 0.4px;")
    window.header_subtitle = CaptionLabel("Ready")
    window.header_subtitle.setStyleSheet(
        f"color: {UITheme.MINT_ACCENT}; font-weight: 600; font-size: 13px;"
    )
    title_area.addWidget(title)
    title_area.addWidget(window.header_subtitle)
    header_layout.addLayout(title_area)
    header_layout.addStretch()

    # CommandBar로 액션 그룹핑
    command_bar = CommandBar(window)
    command_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    command_bar.setStyleSheet(f"""
        QToolButton {{
            padding: 6px 10px;
            border-radius: 6px;
        }}
        QToolButton:hover {{
            background-color: {UITheme.ACCENT_RGBA_12};
        }}
        QToolButton:checked {{
            background-color: {UITheme.ACCENT_RGBA_18};
            color: {UITheme.MINT_ACCENT};
        }}
    """)

    command_bar.addAction(Action(FIF.PEOPLE, "작업자", triggered=window._request_worker_and_refresh))
    command_bar.addAction(Action(FIF.HISTORY, "기록 조회", triggered=window._open_records))
    command_bar.addSeparator()
    command_bar.addAction(Action(FIF.DOCUMENT, "PDF/서명", triggered=window._open_pdf_settings))
    command_bar.addAction(Action(FIF.CLOUD, "Sheets", triggered=window._open_google_sheets_settings))
    command_bar.addSeparator()
    command_bar.addAction(Action(FIF.CLOSE, "종료", triggered=window.close))

    header_layout.addWidget(command_bar)
    root.addWidget(header)

    # KPI row
    create_kpi_row(window, root)

    # Placeholder analytics card
    analytics = CardWidget()
    analytics_layout = QVBoxLayout(analytics)
    analytics_layout.setContentsMargins(20, 18, 20, 18)
    analytics_layout.setSpacing(12)
    analytics_layout.addWidget(CaptionLabel("Production Trend"))
    placeholder = SubtitleLabel("Chart Placeholder")
    placeholder.setStyleSheet(f"color: {UITheme.TEXT_SECONDARY}; font-size: 16px;")
    analytics_layout.addWidget(placeholder)
    analytics_layout.addStretch(1)
    root.addWidget(analytics)

    return page


def build_action_page(title: str, description: str, button_text: str, on_click, object_name: str) -> QWidget:
    page = QWidget()
    page.setObjectName(object_name)
    root = QVBoxLayout(page)
    root.setContentsMargins(36, 32, 36, 32)
    root.setSpacing(16)

    card = CardWidget()
    layout = QVBoxLayout(card)
    layout.setContentsMargins(32, 26, 32, 26)
    layout.setSpacing(14)

    title_label = LargeTitleLabel(title)
    title_label.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY};")
    desc_label = CaptionLabel(description)
    desc_label.setStyleSheet(f"color: {UITheme.TEXT_SECONDARY}; font-size: 13px;")

    action_btn = StyledButton(button_text, "primary")
    action_btn.setMinimumHeight(44)
    action_btn.setMaximumWidth(420)
    action_btn.clicked.connect(on_click)

    layout.addWidget(title_label)
    layout.addWidget(desc_label)
    layout.addSpacing(12)
    layout.addWidget(action_btn, 0, Qt.AlignLeft)

    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    root.addWidget(card)
    root.addStretch(1)
    return page


def build_mixing_page(window) -> QWidget:
    """배합 페이지 - 세로 레이아웃으로 작업자 워크플로우 최적화"""
    page = QWidget()
    page.setObjectName("MixingPage")
    root = QVBoxLayout(page)
    root.setContentsMargins(28, 22, 28, 22)
    root.setSpacing(16)

    # 상단: Recipe & Work Info (컴팩트)
    top_card = CardWidget()
    top_layout = QHBoxLayout(top_card)
    top_layout.setContentsMargins(14, 10, 14, 10)
    top_layout.setSpacing(16)

    # 레시피 패널
    top_layout.addWidget(window.recipe_panel, 2)
    # 작업 정보 패널
    top_layout.addWidget(window.work_info_panel, 3)

    # 저장 버튼 (상단 우측)
    if not hasattr(window, "save_btn"):
        window.save_btn = StyledButton("저장", "primary")
        window.save_btn.setEnabled(False)
        window.save_btn.clicked.connect(window._save_record)
        window.save_btn.setMinimumHeight(40)
    top_layout.addWidget(window.save_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

    root.addWidget(top_card)

    # 하단: Materials List (전체 너비, 확장)
    materials_card = CardWidget()
    materials_layout = QVBoxLayout(materials_card)
    materials_layout.setContentsMargins(14, 10, 14, 10)

    materials_title = CaptionLabel("자재 목록")
    materials_title.setStyleSheet(
        f"color: {UITheme.MINT_ACCENT}; font-weight: bold; font-size: 14px;"
    )
    materials_layout.addWidget(materials_title)
    materials_layout.addSpacing(6)
    materials_layout.addWidget(window.material_panel)

    root.addWidget(materials_card, 1)  # stretch factor로 확장

    # 상태바
    if not hasattr(window, "_status_bar"):
        window._status_bar = StatusBar()
    root.addWidget(window._status_bar)

    return page


def build_settings_page(window) -> QWidget:
    """설정 페이지 - PDF/서명 옵션"""
    page = QWidget()
    page.setObjectName("SettingsPage")
    root = QVBoxLayout(page)
    root.setContentsMargins(36, 32, 36, 32)
    root.setSpacing(22)

    # 타이틀 영역
    title = LargeTitleLabel("설정")
    title.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY};")
    subtitle = CaptionLabel("PDF 스캔 효과 및 서명 옵션을 관리합니다.")
    subtitle.setStyleSheet(f"color: {UITheme.TEXT_SECONDARY}; font-size: 13px;")
    root.addWidget(title)
    root.addWidget(subtitle)
    root.addSpacing(10)

    # 설정 카드들 (가로 배치)
    settings_row = QHBoxLayout()
    settings_row.setSpacing(20)

    # PDF 스캔 효과 카드
    pdf_card = create_panel_card("PDF 스캔 효과", window.scan_effects_panel)
    settings_row.addWidget(pdf_card)

    # 서명 옵션 카드
    sig_card = create_panel_card("서명 옵션", window.signature_panel)
    settings_row.addWidget(sig_card)

    settings_row.addStretch(1)
    root.addLayout(settings_row)
    root.addStretch(1)

    return page


def create_kpi_row(window, root: QVBoxLayout) -> None:
    row = QHBoxLayout()
    row.setSpacing(16)

    window.card_recipe = create_stat_card("Recipe", "-", 0)
    window.card_amount = create_stat_card("Batch Amount (g)", "0", 0)
    window.card_worker = create_stat_card("Worker / Date", "-", 0)

    row.addWidget(window.card_recipe["card"])
    row.addWidget(window.card_amount["card"])
    row.addWidget(window.card_worker["card"])
    root.addLayout(row)


def create_stat_card(title: str, value: str, progress_val: int) -> dict:
    card = MintInfoCard(title, value)
    card.p_bar.setValue(progress_val)
    return {"card": card, "value": card.value_lbl, "progress": card.p_bar}


def create_panel_card(title: str, widget: QWidget) -> QFrame:
    card = CardWidget()
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(10)

    title_label = CaptionLabel(title)
    layout.addWidget(title_label)
    layout.addWidget(widget)
    return card


# setup_bottom_buttons 제거: 저장 버튼은 상단 카드 우측에 배치
