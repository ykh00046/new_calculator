# 배합 프로그램 v3

> 제조업 원료 배합 관리 및 품질 보증을 위한 Windows 데스크톱 애플리케이션

## 개요

- 버전: `v3`
- 주요 기술: Python, PySide6, PySide6-Fluent-Widgets, SQLite
- 개발 작업 폴더: `v3/`
- 현재 저장소 기준 검증 인터프리터: 루트 `.venv/Scripts/python.exe` (`Python 3.13.0`)

## 실행 방법

### 배포본 실행

현재 배포 계약의 기준 실행 파일은 `v3/dist/DHR_Generator.exe`입니다.

- 단일 산출물 확인: `v3/dist/DHR_Generator.exe`
- 사용자 전달용 패키지: `v3/DHR_Generator_v3.0.0_YYYYMMDD.zip`
- 패키지 내부 기본 구성: `DHR_Generator.exe`, `resources/`, `README.md`, `DEPLOY_GUIDE.md`, `RELEASE_SMOKE_CHECKLIST.md`
- 자동 검증 스크립트: `v3/check_release_artifacts.py`

배포 패키지를 받은 사용자는 압축을 해제한 뒤 `DHR_Generator.exe`를 실행합니다. 자세한 절차와 포함 규약은 [DEPLOY_GUIDE.md](/mnt/c/X/Program-estimation/DEPLOY_GUIDE.md)를 따르고, 사용자 전달 직전 검증은 [RELEASE_SMOKE_CHECKLIST.md](/mnt/c/X/Program-estimation/RELEASE_SMOKE_CHECKLIST.md)를 기준으로 수행합니다.

릴리스 직전에는 아래 명령으로 exe/zip 최신성과 패키지 구성을 함께 확인합니다.

```bash
cd v3
../.venv/Scripts/python.exe check_release_artifacts.py
```

### 개발 환경 실행

루트 가상환경을 기준으로 `v3/`에서 실행합니다.

```bash
cd v3
../.venv/Scripts/python.exe main.py
```

개발용 런처는 루트 `run_dev.bat`입니다. 호환성용 `run.bat`도 동일하게 `run_dev.bat`를 호출하며, 먼저 루트 `.venv\Scripts\python.exe`를 찾고 없을 때만 `py -3`, `python` 순서로 폴백합니다.

## 개발 환경 기준

이 저장소에는 루트 `.venv/`가 존재할 수 있지만, 패키지가 항상 완비되어 있지는 않습니다. 실제 점검 시 `pytest`, `pandas`, `pdf2image`, `pywin32`는 설치되어 있었고 `PySide6`, `qfluentwidgets`는 누락되어 있었습니다. 따라서 체크인된 `.venv`를 신뢰하지 말고 아래 절차로 다시 맞추는 것을 기준으로 삼습니다.

1. Python `3.13.x`를 준비합니다.
2. 루트에서 가상환경을 생성하거나 기존 `.venv`를 재사용합니다.
3. `v3/requirements.txt`를 설치합니다.
4. `v3/`에서 애플리케이션/테스트를 실행합니다.

```bash
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r v3\requirements.txt
cd v3
..\.venv\Scripts\python.exe main.py
```

자세한 부트스트랩, 설정 위치, 검증 체크리스트는 [v3/docs/SETUP.md](/mnt/c/X/Program-estimation/v3/docs/SETUP.md)를 참조합니다.
