# -*- coding: utf-8 -*-
"""
PDF 프로세서 GUI 애플리케이션 진입점
"""
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """메인 함수"""
    app = QApplication(sys.argv)

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    # 애플리케이션 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
