설치 및 실행 안내

필수 환경
- Python 3.9 이상(권장 3.11+)
- Windows (MS Excel 설치 필요: Excel COM을 이용한 PDF 내보내기)

권장 도구
- Poppler (pdf2image 래스터화용). 설치 후 `config/config.json`의 `excel.poppler_path`에 Poppler의 `bin` 경로를 지정합니다.

패키지 설치
- 전체 의존성: `pip install -r requirements.txt`
- 최소 의존성(핵심 실행): `pip install -r requirements-min.txt`

설정(`config/config.json`)
- `excel.poppler_path`: Poppler `bin` 경로. 미지정 시 시스템 PATH 사용 시도
- `mixing.default_scale`, `mixing.tolerance`: 기본 스케일/허용오차
- `logging.level`: INFO/DEBUG 등 로그 레벨

출력 경로
- PDF/엑셀 파일은 `실적서/` 하위(`excel/`, `pdf/`)에 저장됩니다(정규화 처리).

실행
- 개발: `python main.py`

