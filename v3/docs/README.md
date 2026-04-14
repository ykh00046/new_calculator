# Program-estimation v3 문서 개요

`v3/`는 Windows 데스크톱 배합 프로그램의 현재 개발/운영 기준 디렉터리입니다. 이 문서는 운영자와 개발자가 먼저 봐야 하는 최신 안내만 정리합니다.

## 기준 경로와 이름

- 저장소 루트: `C:\X\Program-estimation`
- 애플리케이션 루트: `C:\X\Program-estimation\v3`
- 개발 실행 진입점: `v3/main.py`
- 배포 실행 파일: `v3/dist/DHR_Generator.exe`

과거 문서에 남아 있는 `PythonProject3-program`, `PythonProject1-stock` 같은 명칭은 현재 기준 경로가 아닙니다.

## 우선 참조 문서

- 환경 준비: [`SETUP.md`](./SETUP.md)
- 배포 절차: [`../../DEPLOY_GUIDE.md`](../../DEPLOY_GUIDE.md)
- 릴리스 스모크 체크: [`../../RELEASE_SMOKE_CHECKLIST.md`](../../RELEASE_SMOKE_CHECKLIST.md)
- 완료/개선 보고서: `04-report/` 하위 문서

`04-report/` 문서는 당시 작업 결과를 남긴 보고서입니다. 현재 실행 경로, 현재 테스트 수, 현재 릴리스 게이트는 이 문서와 `SETUP.md`, 루트 `README.md`를 우선 기준으로 삼습니다.

## 실행

```powershell
cd C:\X\Program-estimation\v3
..\.venv\Scripts\python.exe .\main.py
```

루트 `run_dev.bat`는 개발용 런처입니다. 호환성용 `run.bat`는 내부적으로 `run_dev.bat`를 호출합니다.

## 개발 환경 기준

- 운영체제: Windows
- 권장 Python: `3.13.x`
- GUI 필수 패키지: `PySide6`, `PySide6-Fluent-Widgets`
- 테스트/유틸 패키지: `pytest`, `pytest-mock`, `pytest-timeout`

체크인된 `.venv/`는 패키지 구성이 항상 완전하다고 가정하지 않습니다. 새 환경에서는 `v3/requirements.txt` 재설치를 기본 절차로 사용합니다.

```powershell
cd C:\X\Program-estimation
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\v3\requirements.txt
```

전체 부트스트랩과 설정 경로는 [`SETUP.md`](./SETUP.md)에 정리되어 있습니다.

## 테스트 기준

빠른 검증:

```powershell
cd C:\X\Program-estimation\v3
..\.venv\Scripts\python.exe -m pytest tests/unit/test_config_manager.py -q
```

기본 회귀 검증:

```powershell
cd C:\X\Program-estimation\v3
..\.venv\Scripts\python.exe .\tests\run_tests.py
```

해석 기준:

- 기본 게이트는 `tests/run_tests.py`가 종료 코드 `0`으로 끝나는지 여부입니다.
- GUI 의존성이 빠진 환경에서는 `tests/unit/test_panels.py`가 `skip`될 수 있습니다.
- 릴리스 전에는 `PySide6`, `qfluentwidgets`가 모두 설치된 환경에서 전체 스위트를 다시 확인해야 합니다.

현재 테스트 총 개수나 커버리지 수치는 코드/테스트 추가에 따라 변할 수 있으므로, 문서에 고정 수치로 관리하지 않습니다.

## 설정 파일 위치

앱은 아래 순서로 `config.json`을 찾습니다.

1. `%LOCALAPPDATA%\MixingProgram\config\config.json`
2. `%MIXING_APP_DATA_DIR%\config\config.json`
3. `v3/config/config.json`

즉, `v3/config/config.json`만 수정한다고 항상 실제 실행 설정이 바뀌는 것은 아닙니다.

## 배포 기준

- 빌드 스크립트: `v3/build.py`
- 패키지 스크립트: `v3/deploy.py`
- 배포 ZIP 형식: `DHR_Generator_v3.0.0_YYYYMMDD.zip`
- 사용자 실행 파일: `DHR_Generator.exe`

실제 배포 계약과 전달 전 확인 항목은 루트 문서를 사용합니다.

- [`README.md`](../../README.md)
- [`DEPLOY_GUIDE.md`](../../DEPLOY_GUIDE.md)
- [`RELEASE_SMOKE_CHECKLIST.md`](../../RELEASE_SMOKE_CHECKLIST.md)

## 지원

- 실행/설치 문제: `SETUP.md`의 import 체크와 설치 절차를 먼저 확인
- 배포 문제: 루트 배포 가이드와 스모크 체크리스트 확인
- 과거 구현 경과 확인: `04-report/` 하위 문서 참조
