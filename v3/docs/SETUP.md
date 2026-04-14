# 설치 및 실행 안내

## 기준 환경

- 운영체제: Windows
- 권장 인터프리터: Python `3.13.x`
- 현재 저장소에서 확인한 가상환경: 루트 `.venv/Scripts/python.exe` = `Python 3.13.0`
- GUI 필수 패키지: `PySide6`, `PySide6-Fluent-Widgets`
- 테스트/유틸 패키지: `pytest`, `pytest-mock`, `pytest-timeout`
- OS 의존성: `pywin32`, MS Excel 설치 권장

기존 문서의 `Python 3.9+` 표기는 현재 검증 기준과 다릅니다. 이번 저장소 점검 기준으로는 `3.13.x`를 표준 개발 인터프리터로 사용합니다.

## 작업 디렉터리와 인터프리터

- 프로젝트 루트: `Program-estimation/`
- 애플리케이션 루트: `Program-estimation/v3/`
- 권장 인터프리터 경로: `Program-estimation/.venv/Scripts/python.exe`

체크인된 `.venv/`가 있어도 패키지가 누락될 수 있습니다. 실제 점검에서는 `PySide6`, `qfluentwidgets` import가 실패했습니다. 따라서 새 작업자는 아래 절차로 의존성을 다시 맞추는 것을 기본으로 합니다.

## 부트스트랩

루트에서 가상환경을 만들고, `v3/requirements.txt`를 설치한 뒤 `v3/`에서 실행합니다.

```powershell
cd C:\X\Program-estimation
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\v3\requirements.txt
cd .\v3
..\.venv\Scripts\python.exe .\main.py
```

이미 `.venv`가 있다면 재생성 대신 아래처럼 바로 재설치해도 됩니다.

```powershell
cd C:\X\Program-estimation
.\.venv\Scripts\python.exe -m pip install -r .\v3\requirements.txt
```

## 최소 설치와 전체 설치

- 전체 개발/테스트/빌드: `v3/requirements.txt`
- 최소 실행 전용: `v3/requirements-min.txt`

```powershell
cd C:\X\Program-estimation
.\.venv\Scripts\python.exe -m pip install -r .\v3\requirements.txt
```

```powershell
cd C:\X\Program-estimation
.\.venv\Scripts\python.exe -m pip install -r .\v3\requirements-min.txt
```

주의:

- 최소 설치에는 `pytest`가 포함되지 않습니다.
- 최소 설치만으로는 일부 문서 예시, QA 도구, 테스트 실행이 되지 않을 수 있습니다.
- 메인 앱은 `from qfluentwidgets import ...`를 사용하므로 pip 패키지명 `PySide6-Fluent-Widgets`가 반드시 필요합니다.

## 설정 파일 위치

현재 코드는 설정 파일을 우선 아래 사용자 데이터 경로에서 찾습니다.

- `%LOCALAPPDATA%\MixingProgram\config\config.json`
- `MIXING_APP_DATA_DIR` 환경변수를 지정한 경우: `%MIXING_APP_DATA_DIR%\config\config.json`
- 레거시 폴백: `v3/config/config.json`

즉, `v3/config/config.json`만 편집하면 항상 반영된다고 가정하면 안 됩니다. 로컬 PC에서 어떤 설정 파일이 실제로 사용되는지 먼저 확인해야 합니다.

주요 경로는 `v3/config/settings.py`, `v3/config/config_manager.py` 기준으로 정해집니다.

## 외부 도구

### Excel

- 일부 기능은 Excel COM을 사용하므로 Windows와 MS Excel이 필요합니다.

### Poppler

- `pdf2image` 기반 래스터화가 필요한 경우 Poppler 설치를 권장합니다.
- 설정 키: `excel.poppler_path`
- 값: Poppler `bin` 폴더 경로
- 미지정 시 시스템 PATH를 사용하도록 시도합니다.

## 빠른 검증 체크리스트

### 1. 핵심 import 확인

```powershell
cd C:\X\Program-estimation\v3
..\.venv\Scripts\python.exe -c "import PySide6, qfluentwidgets, pytest, win32api"
```

이 명령이 실패하면 GUI 실행이나 전체 테스트 전에 먼저 의존성 설치를 다시 해야 합니다.

### 2. 최소 단위 테스트 확인

```powershell
cd C:\X\Program-estimation\v3
..\.venv\Scripts\python.exe -m pytest tests/unit/test_config_manager.py -q
```

현재 저장소 점검 시 위 명령은 통과했습니다.

### 3. 전체 테스트 러너 확인

```powershell
cd C:\X\Program-estimation\v3
..\.venv\Scripts\python.exe tests/run_tests.py
```

`tests/run_tests.py`는 기본적으로 `QT_QPA_PLATFORM=offscreen`을 적용해 헤드리스 환경에서도 Qt 초기화를 시도합니다.

- `PySide6`와 `qfluentwidgets`가 모두 설치된 환경이면 전체 스위트가 실행되어야 합니다.
- GUI 의존성이 빠진 환경이면 `tests/unit/test_panels.py`는 `skip` 처리되고, 비 GUI 테스트가 계속 실행됩니다.

## 최소 통과 기준

- 로컬/CI 기본 게이트: `..\.venv\Scripts\python.exe tests/run_tests.py` 실행 시 실패 없이 종료
- 허용 가능한 상태
  - 전체 의존성 설치 환경: 모든 테스트 green
  - 최소/부분 의존성 환경: UI 패널 테스트만 skip, 나머지 테스트 green
- 릴리스 전 최종 확인: `PySide6`, `qfluentwidgets`를 포함한 전체 환경에서 `tests/run_tests.py`를 다시 실행

## 실행

```powershell
cd C:\X\Program-estimation\v3
..\.venv\Scripts\python.exe .\main.py
```

`run_dev.bat`는 개발용 소스 실행 진입점이며, 루트 `.venv\Scripts\python.exe`를 우선 사용하고 없을 때만 `py -3`, `python` 순서로 폴백합니다. 호환성용 `run.bat`는 내부적으로 `run_dev.bat`를 호출합니다. 개발 환경 재현이 목적이면 위와 같은 명시 인터프리터 실행을 우선 권장합니다.

## 출력 경로

- 사용자 출력 폴더는 우선 `실적서/`를 사용합니다.
- 실제 기본값은 사용자 데이터 디렉터리 하위 `실적서` 또는 `output`이며, 레거시 경로로 `v3/실적서`, `v3/output`도 폴백합니다.
