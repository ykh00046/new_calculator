# -*- coding: utf-8 -*-
"""
백그라운드 워커 스레드
"""
from PySide6.QtCore import QThread, Signal
from processing.converter import PdfConverter


class ConversionWorker(QThread):
    """
    PDF 변환 작업을 백그라운드에서 실행하는 워커 스레드
    """
    # 시그널 정의
    progress_updated = Signal(int, str)  # (진행률, 메시지)
    finished = Signal(bool, str)  # (성공 여부, 메시지)

    def __init__(self, input_excel_path, output_pdf_path, blur_radius, noise_range,
                 contrast_factor, brightness_factor, dpi=300):
        super().__init__()
        self.input_excel_path = input_excel_path
        self.output_pdf_path = output_pdf_path
        self.blur_radius = blur_radius
        self.noise_range = noise_range
        self.contrast_factor = contrast_factor
        self.brightness_factor = brightness_factor
        self.dpi = dpi

        # Converter 인스턴스 생성
        self.converter = PdfConverter()

        # Converter의 시그널을 워커의 시그널로 연결
        self.converter.progress_updated.connect(self.progress_updated.emit)
        self.converter.finished.connect(self._on_converter_finished)

    def run(self):
        """스레드 실행 메서드"""
        try:
            self.converter.convert(
                self.input_excel_path,
                self.output_pdf_path,
                self.blur_radius,
                self.noise_range,
                self.contrast_factor,
                self.brightness_factor,
                self.dpi
            )
        except Exception as e:
            self.finished.emit(False, f"워커 스레드 오류: {str(e)}")

    def _on_converter_finished(self, success, message):
        """Converter 완료 시그널 핸들러"""
        self.finished.emit(success, message)
