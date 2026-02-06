# PDF 프로세서 GUI - 개발 계획

## 1. 프로젝트 목표

사용자가 엑셀 파일을 선택하고, 다양한 '스캔 효과' 파라미터를 직접 조절하여, 스캔한 문서처럼 보이는 PDF로 변환할 수 있는 독립적인 GUI 애플리케이션을 제작합니다.

## 2. 핵심 기술

- **GUI 프레임워크:** PySide6 (메인 프로젝트와의 일관성 유지)
- **이미지 처리:** Pillow
- **PDF 및 엑셀 처리:** PyMuPDF (fitz), openpyxl
- **윈도우 자동화:** pywin32

## 3. 애플리케이션 구조

프로젝트는 `pdf_processor_gui` 디렉토리 내에 구성되며, 다음과 같은 파일들을 포함합니다:

- `main.py`: 애플리케이션의 메인 진입점. PyQt 애플리케이션과 메인 윈도우를 초기화합니다.
- `ui/`: UI 관련 파일을 위한 디렉토리.
  - `main_window.py`: 메인 윈도우 클래스, 레이아웃, 위젯을 정의합니다.
- `processing/`: 백엔드 로직을 위한 디렉토리.
  - `converter.py`: `test_pdf_quality.py`에서 사용된 핵심 변환 로직을 포함합니다. `excel_to_pdf`, `pdf_to_images`, `apply_effects`, `images_to_pdf` 등의 함수를 포함합니다.
- `worker.py`: 변환 프로세스를 백그라운드에서 실행하여 GUI가 멈추는 것을 방지하는 `QThread` 워커를 정의합니다.

## 4. UI 디자인 (`ui/main_window.py`)

메인 윈도우는 다음과 같은 컴포넌트들을 가집니다:

- **입력 섹션:**
  - `QLineEdit` (읽기 전용): 입력 엑셀 파일 경로 표시.
  - `QPushButton` ("파일 선택..."): 파일 선택 다이얼로그 열기.
- **효과 제어 섹션 (GroupBox 안에配置):**
  - **블러:** `QLabel` + `QDoubleSpinBox` (범위: 0.0-5.0, 단계: 0.1).
  - **노이즈:** `QLabel` + `QSpinBox` (범위: 0-100, 단계: 1).
  - **대비:** `QLabel` + `QDoubleSpinBox` (범위: 0.5-1.5, 단계: 0.01).
  - **밝기:** `QLabel` + `QDoubleSpinBox` (범위: 0.5-1.5, 단계: 0.01).
  - `QPushButton` ("기본값 복원"): 파라미터를 기본값으로 리셋.
- **출력 섹션:**
  - `QLineEdit` (읽기 전용): 출력 PDF 파일 경로 표시.
  - `QPushButton` ("저장 위치..."): 파일 저장 다이얼로그 열기.
- **실행 및 상태 섹션:**
  - `QPushButton` ("PDF 생성 시작"): 프로세스 시작.
  - `QProgressBar`: 진행 상태 표시.
  - `QTextEdit` (읽기 전용): 로그 메시지 표시.

## 5. 백엔드 로직 (`processing/converter.py`)

- 이 모듈은 `test_pdf_quality.py` 스크립트를 클래스 기반으로 리팩토링한 버전입니다.
- `PdfConverter` 클래스가 전체 워크플로우를 캡슐화합니다.
- 클래스는 각 단계에서 GUI 스레드와 통신하기 위해 `progress_updated(int, str)`, `finished(bool, str)`와 같은 시그널을 발생시킵니다.

## 6. 스레딩 (`worker.py`)

- `QThread`를 상속받는 `ConversionWorker` 클래스.
- `PdfConverter` 인스턴스와 사용자가 정의한 파라미터를 입력받습니다.
- `run()` 메소드가 변환 프로세스를 실행합니다.
- 시그널을 사용하여 진행 상황 업데이트와 최종 결과를 메인 GUI 스레드로 전달하여 스레드 안전성을 보장합니다.

## 7. 개발 단계

1.  **[완료]** `pdf_processor_gui` 프로젝트 디렉토리 생성.
2.  **[완료]** 이 내용으로 `PLAN.md` 파일 생성.
3.  **[진행예정]** 기본 파일 구조 생성 (`main.py`, `ui/main_window.py`, `processing/converter.py`, `worker.py`).
4.  **[진행예정]** `ui/main_window.py`에 UI 레이아웃 구현.
5.  **[진행예정]** `test_pdf_quality.py`의 로직을 `processing/converter.py`의 `PdfConverter` 클래스로 리팩토링.
6.  **[진행예정]** `ConversionWorker` 스레드 구현.
7.  **[진행예정]** UI 시그널(버튼 클릭)을 워커 스레드를 생성하고 시작하는 슬롯에 연결.
8.  **[진행예정]** 워커의 시그널을 UI 슬롯에 연결하여 진행률 표시줄과 로그 메시지 업데이트.
9.  **[진행예정]** 오류 처리 및 사용자 피드백(`QMessageBox` 등) 추가.
10. **[진행예정]** 최종 테스트 및 개선.
