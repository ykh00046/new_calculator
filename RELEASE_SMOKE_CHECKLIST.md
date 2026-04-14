# Program-estimation 릴리스 스모크 체크리스트

배포본 실행 검증은 소스 실행(`run_dev.bat`)과 분리해서 진행합니다.
이 문서는 사용자 전달 직전 `DHR_Generator.exe` 패키지 기준으로만 점검합니다.

## 1. 빌드 산출물 확인

- `v3/dist/DHR_Generator.exe`가 최신 시각으로 생성되어 있다.
- `v3/build.py` 실행 로그에 실패 메시지가 없다.
- 빌드 직후 `v3/deploy.py`를 다시 실행해 새 패키지를 만들었다.
- `v3/check_release_artifacts.py` 실행 결과가 성공(`0`)이다.

## 2. 패키지 구성 확인

- ZIP 파일 이름이 `DHR_Generator_v3.0.0_YYYYMMDD.zip` 형식이다.
- ZIP 내부 최상위 폴더에 아래 항목이 모두 있다.
- `DHR_Generator.exe`
- `resources/`
- `README.md`
- `DEPLOY_GUIDE.md`
- `RELEASE_SMOKE_CHECKLIST.md`

## 3. 실행 스모크 테스트

- 새 폴더에 ZIP을 압축 해제했다.
- 압축 해제 폴더 안에서 `DHR_Generator.exe`가 실행된다.
- 앱 첫 화면이 오류 팝업 없이 표시된다.
- `resources/`를 같은 폴더 구조로 유지한 상태에서 기본 기능 진입이 가능하다.

## 4. 배포 문서 정합성

- 패키지 내부 `README.md`가 배포 실행 파일을 `DHR_Generator.exe`로 안내한다.
- 패키지 내부 `DEPLOY_GUIDE.md`가 소스 실행이 아닌 배포 실행 절차를 설명한다.
- 개발용 런처 `run_dev.bat`는 배포 경로 문서에 사용자 실행 방법으로 노출되지 않는다.

## 5. 기록

- 실행 성공/실패 여부와 테스트 일시를 릴리스 노트 또는 작업 로그에 남긴다.
- `check_release_artifacts.py` 출력 결과를 함께 남겨 exe/zip 최신성 증빙으로 사용한다.
- 실패 시 배포본을 전달하지 않고 재빌드 후 동일 체크리스트를 다시 수행한다.
