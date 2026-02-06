"""

레시피 관리 다이얼로그

레시피 조회, 추가, 수정, 삭제 기능 제공

"""

from PySide6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,

    QTableWidget, QTableWidgetItem, QListWidget, QLabel,

    QMessageBox, QInputDialog, QHeaderView, QSplitter

)

from PySide6.QtCore import Qt
from ui.styles import UIStyles

import pandas as pd

import os





class RecipeManagerDialog(QDialog):

    def __init__(self, data_manager, parent=None):

        super().__init__(parent)

        self.data_manager = data_manager

        self.current_recipe = None

        self.init_ui()

        self.load_recipe_list()



    def init_ui(self):

        """UI 초기화"""

        self.setWindowTitle("레시피 관리")

        self.setGeometry(200, 200, 1000, 600)



        main_layout = QVBoxLayout()



        # 상단 타이틀

        title_label = QLabel("레시피 관리")

        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")

        main_layout.addWidget(title_label)



        # 메인 컨텐츠 (Splitter로 좌우 분할)

        splitter = QSplitter(Qt.Horizontal)



        # 좌측: 레시피 목록

        left_widget = self.create_recipe_list_panel()

        splitter.addWidget(left_widget)



        # 우측: 품목 상세

        right_widget = self.create_item_detail_panel()

        splitter.addWidget(right_widget)



        splitter.setStretchFactor(0, 1)

        splitter.setStretchFactor(1, 2)



        main_layout.addWidget(splitter)



        # 하단 버튼

        button_layout = QHBoxLayout()



        save_btn = QPushButton("저장")

        save_btn.setStyleSheet(UIStyles.get_primary_button_style())

        save_btn.clicked.connect(self.save_to_excel)

        button_layout.addWidget(save_btn)



        button_layout.addStretch()



        close_btn = QPushButton("닫기")

        close_btn.setStyleSheet(UIStyles.get_secondary_button_style())

        close_btn.clicked.connect(self.close)

        button_layout.addWidget(close_btn)



        main_layout.addLayout(button_layout)



        self.setLayout(main_layout)



    def create_recipe_list_panel(self):

        """레시피 목록 패널 생성"""

        from PySide6.QtWidgets import QWidget



        widget = QWidget()

        layout = QVBoxLayout()



        label = QLabel("레시피 목록")

        label.setStyleSheet("font-size: 14px; font-weight: bold;")

        layout.addWidget(label)



        self.recipe_list = QListWidget()

        self.recipe_list.itemClicked.connect(self.on_recipe_selected)

        layout.addWidget(self.recipe_list)



        # 버튼 레이아웃

        btn_layout = QHBoxLayout()



        add_recipe_btn = QPushButton("레시피 추가")

        add_recipe_btn.clicked.connect(self.add_recipe)

        btn_layout.addWidget(add_recipe_btn)



        delete_recipe_btn = QPushButton("레시피 삭제")

        delete_recipe_btn.clicked.connect(self.delete_recipe)

        btn_layout.addWidget(delete_recipe_btn)



        layout.addLayout(btn_layout)



        widget.setLayout(layout)

        return widget



    def create_item_detail_panel(self):

        """품목 상세 패널 생성"""

        from PySide6.QtWidgets import QWidget



        widget = QWidget()

        layout = QVBoxLayout()



        self.detail_label = QLabel("레시피를 선택하세요")

        self.detail_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        layout.addWidget(self.detail_label)



        self.item_table = QTableWidget()

        self.item_table.setColumnCount(3)

        self.item_table.setHorizontalHeaderLabels(["품목코드", "품목명", "배합비율"])

        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.item_table)



        # 버튼 레이아웃

        btn_layout = QHBoxLayout()



        add_item_btn = QPushButton("품목 추가")

        add_item_btn.clicked.connect(self.add_item)

        btn_layout.addWidget(add_item_btn)



        delete_item_btn = QPushButton("품목 삭제")

        delete_item_btn.clicked.connect(self.delete_item)

        btn_layout.addWidget(delete_item_btn)



        layout.addLayout(btn_layout)



        widget.setLayout(layout)

        return widget



    def load_recipe_list(self):

        """레시피 목록 로드"""

        self.recipe_list.clear()

        for recipe_name in sorted(self.data_manager.recipes.keys()):

            self.recipe_list.addItem(recipe_name)



    def on_recipe_selected(self, item):

        """레시피 선택 시 품목 표시"""

        self.current_recipe = item.text()

        self.detail_label.setText(f"레시피: {self.current_recipe}")

        self.load_items()



    def load_items(self):

        """선택된 레시피의 품목 로드"""

        if not self.current_recipe:

            return



        items = self.data_manager.recipes.get(self.current_recipe, [])

        self.item_table.setRowCount(len(items))



        for row, item in enumerate(items):

            self.item_table.setItem(row, 0, QTableWidgetItem(item['품목코드']))

            self.item_table.setItem(row, 1, QTableWidgetItem(item['품목명']))

            self.item_table.setItem(row, 2, QTableWidgetItem(str(item['배합비율'])))



    def add_recipe(self):

        """레시피 추가"""

        recipe_name, ok = QInputDialog.getText(self, "레시피 추가", "레시피 이름:")

        if ok and recipe_name:

            recipe_name = recipe_name.strip()

            if recipe_name in self.data_manager.recipes:

                QMessageBox.warning(self, "경고", "이미 존재하는 레시피 이름입니다.")

                return



            self.data_manager.recipes[recipe_name] = []

            self.load_recipe_list()

            QMessageBox.information(self, "완료", f"레시피 '{recipe_name}'가 추가되었습니다.")



    def delete_recipe(self):

        """레시피 삭제"""

        if not self.current_recipe:

            QMessageBox.warning(self, "경고", "삭제할 레시피를 선택하세요.")

            return



        reply = QMessageBox.question(

            self, "확인",

            f"레시피 '{self.current_recipe}'를 삭제하시겠습니까?",

            QMessageBox.Yes | QMessageBox.No

        )



        if reply == QMessageBox.Yes:

            del self.data_manager.recipes[self.current_recipe]

            self.current_recipe = None

            self.load_recipe_list()

            self.item_table.setRowCount(0)

            self.detail_label.setText("레시피를 선택하세요")

            QMessageBox.information(self, "완료", "레시피가 삭제되었습니다.")



    def add_item(self):

        """품목 추가"""

        if not self.current_recipe:

            QMessageBox.warning(self, "경고", "레시피를 먼저 선택하세요.")

            return



        row = self.item_table.rowCount()

        self.item_table.insertRow(row)

        self.item_table.setItem(row, 0, QTableWidgetItem(""))

        self.item_table.setItem(row, 1, QTableWidgetItem(""))

        self.item_table.setItem(row, 2, QTableWidgetItem("0.0"))



    def delete_item(self):

        """품목 삭제"""

        current_row = self.item_table.currentRow()

        if current_row >= 0:

            self.item_table.removeRow(current_row)

        else:

            QMessageBox.warning(self, "경고", "삭제할 품목을 선택하세요.")



    def save_to_excel(self):

        """엑셀에 저장"""

        try:

            # 테이블 데이터를 data_manager.recipes에 반영

            if self.current_recipe:

                items = []

                for row in range(self.item_table.rowCount()):

                    code = self.item_table.item(row, 0).text().strip()

                    name = self.item_table.item(row, 1).text().strip()

                    ratio_text = self.item_table.item(row, 2).text().strip()



                    if not code or not name:

                        QMessageBox.warning(self, "경고", f"{row+1}행: 품목코드와 품목명을 입력하세요.")

                        return



                    try:

                        ratio = float(ratio_text)

                    except ValueError:

                        QMessageBox.warning(self, "경고", f"{row+1}행: 배합비율은 숫자여야 합니다.")

                        return



                    items.append({

                        '품목코드': code,

                        '품목명': name,

                        '배합비율': ratio

                    })



                self.data_manager.recipes[self.current_recipe] = items



            # 엑셀 저장

            data = []

            for recipe_name, items in self.data_manager.recipes.items():

                for item in items:

                    data.append({

                        '레시피': recipe_name,

                        '품목코드': item['품목코드'],

                        '품목명': item['품목명'],

                        '배합비율': item['배합비율']

                    })



            df = pd.DataFrame(data)

            df.to_excel(self.data_manager.recipe_file, index=False, engine='openpyxl')



            QMessageBox.information(self, "완료", "레시피가 저장되었습니다.")



        except Exception as e:

            QMessageBox.critical(self, "오류", f"저장 중 오류가 발생했습니다:\n{str(e)}")

