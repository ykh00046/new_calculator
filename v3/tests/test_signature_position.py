"""
서명 위치 조정 테스트 (X 좌표 +20)
"""
import os
import sys
from datetime import datetime

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(__file__))

from config.config_manager import config
from models.image_processor import ImageProcessor
from models.excel_exporter import ExcelExporter

def test_signature_position():
    print("=" * 60)
    print("서명 위치/크기 조정 테스트")
    print("=" * 60)

    # 1. ImageProcessor로 서명 이미지 생성
    print("\n[1/3] 서명 합성 이미지 생성 중...")
    resources_path = os.path.join(os.path.dirname(__file__), "resources", "signature")
    base_image_path = os.path.join(resources_path, "image.jpeg")

    processor = ImageProcessor(resources_path=resources_path, config=config.get("signature", {}))

    # 출력 경로 설정
    output_dir = "temp_test"
    os.makedirs(output_dir, exist_ok=True)
    signed_image_path = os.path.join(output_dir, "signed_300x88.png")

    # 서명 이미지 생성
    success, message = processor.create_signed_image(
        base_image_path=base_image_path,
        output_path=signed_image_path,
        selected_worker="김민호"
    )

    if not success:
        print(f"[ERROR] 서명 이미지 생성 실패: {message}")
        return

    # 파일 크기 확인
    file_size = os.path.getsize(signed_image_path) / 1024
    print(f"[SUCCESS] 서명 이미지 생성: {signed_image_path}")
    print(f"          파일 크기: {file_size:.1f} KB")

    # 2. ExcelExporter로 엑셀 생성
    print("\n[2/3] 엑셀 파일 생성 중...")
    exporter = ExcelExporter()

    # 테스트 데이터
    test_data = {
        'product_lot': 'TEST_280X88',
        'worker': '김민호',
        'work_date': datetime.now().strftime('%Y-%m-%d'),
        'work_time': datetime.now().strftime('%H:%M:%S'),
        'scale': 'TEST-SCALE',
        'total_amount': 100.0,
        'materials': [
            {
                'material_name': 'PB',
                'material_lot': 'LOT001',
                'ratio': 100.0,
                'theory_amount': 100.0,
                'actual_amount': 100.0
            }
        ]
    }

    excel_file = exporter.export_to_excel(
        data=test_data,
        include_image=True,
        image_path=signed_image_path
    )

    if not excel_file:
        print("[ERROR] 엑셀 파일 생성 실패")
        return

    excel_size = os.path.getsize(excel_file) / 1024
    print(f"[SUCCESS] 엑셀 파일 생성: {excel_file}")
    print(f"          파일 크기: {excel_size:.1f} KB")

    # 3. PDF 변환
    print("\n[3/3] PDF 변환 중...")
    pdf_file = exporter.export_to_pdf(excel_file)

    if not pdf_file:
        print("[ERROR] PDF 변환 실패")
        return

    pdf_size = os.path.getsize(pdf_file) / 1024
    print(f"[SUCCESS] PDF 파일 생성: {pdf_file}")
    print(f"          파일 크기: {pdf_size:.1f} KB")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print("\n변경 사항:")
    print("  [위치 변경 - 원본 350x100 기준]")
    print("    담당 (Charge): X=150, Y=67 (위로 -5)")
    print("    검토 (Review): X=215, Y=64 (위로 -5)")
    print("    승인 (Approve): X=288, Y=63 (위로 -5)")
    print("  [서명 크기]")
    print("    개별 서명: 63x25 픽셀 (90%)")
    print("  [원본 이미지]")
    print("    서명 합성 이미지: 350x100 픽셀")
    print("  [엑셀 삽입 크기]")
    print("    이미지: 228x65 픽셀 (원본 350x100의 65%)")
    print("  [밝기 향상]")
    print("    밝기 계수: 1.25 (+25%)")
    print("  [랜덤 변화]")
    print("    회전: ±8°, X이동: ±1px, Y이동: ±2px")
    print("\n생성된 파일:")
    print(f"  1. 서명 이미지: {signed_image_path} ({file_size:.1f} KB)")
    print(f"  2. 엑셀 파일:   {excel_file} ({excel_size:.1f} KB)")
    print(f"  3. PDF 파일:    {pdf_file} ({pdf_size:.1f} KB)")
    print("\n서명 이미지와 엑셀 파일을 열어서 위치를 확인하세요.")

if __name__ == "__main__":
    test_signature_position()
