# Program-estimation 배포 가이드

## 배포 계약

- 빌드 스크립트: `v3/build.py`
- 패키지 스크립트: `v3/deploy.py`
- 기준 실행 파일명: `DHR_Generator.exe`
- 기준 빌드 산출물 경로: `v3/dist/DHR_Generator.exe`
- 기준 배포 패키지명: `DHR_Generator_v3.0.0_YYYYMMDD.zip`

## 패키지 구성

`v3/deploy.py`가 생성하는 배포 폴더와 ZIP에는 아래 항목이 포함됩니다.

- `DHR_Generator.exe`
- `resources/`
- `README.md`
- `DEPLOY_GUIDE.md`
- `RELEASE_SMOKE_CHECKLIST.md`

`resources/`는 템플릿, 레시피, 서명 이미지 등 런타임 자산을 포함하므로 실행 파일과 같은 패키지 안에 함께 배포해야 합니다.

## 릴리스 절차 (권장: 단일 명령)

1. 루트 가상환경 또는 배포용 Python 환경을 준비합니다.
2. `v3/` 디렉터리에서 `release.py` 한 번으로 빌드 → 패키지 → 검증을 실행합니다.
3. 종료 코드 `0`을 확인한 뒤 생성된 ZIP 파일을 사용자에게 전달합니다.

```bash
cd v3
../.venv/Scripts/python.exe release.py
```

**종료 코드 규약**

| 코드 | 의미 |
| --- | --- |
| `0` | 전체 파이프라인 성공 |
| `10` | build 단계 실패 |
| `20` | deploy(패키지) 단계 실패 |
| `30` | 산출물 검증 실패 |

### 부분 실행 (고급)

기존 산출물을 재사용해 일부 단계만 다시 수행할 수 있습니다.

```bash
cd v3
../.venv/Scripts/python.exe release.py --skip-build     # dist 재사용
../.venv/Scripts/python.exe release.py --skip-package   # 최신 ZIP 재사용
```

또는 각 스크립트를 단독으로 실행해도 동작은 동일하게 유지됩니다.

```bash
cd v3
../.venv/Scripts/python.exe build.py
../.venv/Scripts/python.exe deploy.py
../.venv/Scripts/python.exe check_release_artifacts.py
```

## 사용자 실행 절차

1. 전달받은 `DHR_Generator_v3.0.0_YYYYMMDD.zip` 파일을 압축 해제합니다.
2. 압축 해제 폴더 안에서 `DHR_Generator.exe`를 실행합니다.
3. `resources/` 폴더는 삭제하거나 다른 위치로 이동하지 않습니다.

## 확인 체크리스트

- `v3/dist/DHR_Generator.exe`가 실제로 생성되었는가
- `v3/check_release_artifacts.py`가 성공 종료 코드(`0`)로 끝났는가
- 배포 ZIP 내부에 `DHR_Generator.exe`와 `resources/`가 모두 포함되었는가
- 패키지 내부 문서(`README.md`, `DEPLOY_GUIDE.md`)가 최신 실행 계약과 일치하는가
- 사용자 전달 전 [RELEASE_SMOKE_CHECKLIST.md](/mnt/c/X/Program-estimation/RELEASE_SMOKE_CHECKLIST.md) 기준 스모크 체크를 완료했는가
