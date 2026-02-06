"""
DHR 모드 선택 다이얼로그
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.styles import UIStyles, UITheme


class DhrModeDialog(QDialog):
    """DHR 진입 시 모드 선택 다이얼로그"""
    
    # 반환 값 상수
    MODE_FREE_INPUT = 1
    MODE_LOAD_RECIPE = 2
    MODE_MANAGE_RECIPE = 3
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_mode = None
        self.setWindowTitle("DHR 모드 선택")
        self.setFixedSize(400, 250)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 제목
        title = QLabel("DHR 입력 모드를 선택하세요")
        title.setFont(QFont("맑은 고딕", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {UITheme.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # 자유 입력 버튼
        free_btn = QPushButton("📝 자유 입력")
        free_btn.setObjectName("freeInput")
        free_btn.setStyleSheet(UIStyles.get_primary_button_style())
        free_btn.clicked.connect(lambda: self._select_mode(self.MODE_FREE_INPUT))
        layout.addWidget(free_btn)
        
        # 레시피 불러오기 버튼
        load_btn = QPushButton("📋 레시피 불러오기")
        load_btn.setObjectName("loadRecipe")
        load_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        load_btn.clicked.connect(lambda: self._select_mode(self.MODE_LOAD_RECIPE))
        layout.addWidget(load_btn)
        
        # 레시피 관리 버튼
        manage_btn = QPushButton("⚙️ 레시피 관리")
        manage_btn.setObjectName("manageRecipe")
        manage_btn.setStyleSheet(UIStyles.get_secondary_button_style())
        manage_btn.clicked.connect(lambda: self._select_mode(self.MODE_MANAGE_RECIPE))
        layout.addWidget(manage_btn)
        
        self.setLayout(layout)
    
    def _select_mode(self, mode):
        self.selected_mode = mode
        self.accept()
    
    def get_selected_mode(self):
        return self.selected_mode
