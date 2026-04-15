# Release Pipeline Hardening — Plan

> **Author**: AI Assistant
> **Created**: 2026-04-15
> **Status**: Plan
> **Cycle**: PDCA #9
> **Parent**: PDCA #8 completion (working tree hygiene)

---

## 1. Overview & Purpose

### 1.1 배경
PDCA #8에서 릴리즈 계약(`DEPLOY_GUIDE.md`, `RELEASE_SMOKE_CHECKLIST.md`, `check_release_artifacts.py`)의 토대를 마련했다. 그러나 현재 상태는:

- `python v3/check_release_artifacts.py` 실행 시 **FAIL** — 배포 ZIP 미생성
- `build.py` → `deploy.py` → `check_release_artifacts.py` 3단계가 **수동 연결**, 중간 실패 시 사용자가 직접 재실행해야 함
- `RELEASE_SMOKE_CHECKLIST.md` 스모크 체크 항목이 **비자동화** 체크리스트 수준
- `run.bat` / `run_dev.bat` / `build.py`가 Python 환경(루트 `.venv`) 전제를 **암묵적으로** 공유

### 1.2 목적
릴리즈 파이프라인을 한 번의 명령으로 실행 가능한 상태로 통합하고, `check_release_artifacts.py`가 **GREEN**이 되는 것을 릴리즈 준비 완료 조건으로 만든다. 릴리즈 사고를 사전 차단한다.

---

## 2. Scope

### 2.1 In-Scope

**분류 A — 파이프라인 통합 스크립트 (신규)**
- `v3/release.py` (신규) — `build → deploy → check` 단일 진입점, 실패 시 조기 종료
- 또는 기존 스크립트 `main()` 노출 후 `release.py`에서 호출

**분류 B — 검증 강화**
- `check_release_artifacts.py`:
  - ZIP 내부 `resources/` 핵심 파일 존재 검증 (현재는 존재 여부만)
  - EXE 크기 하한 검증 (0KB 사고 방지)
  - 종료 코드 의미 명시 (0 pass, 1 fail, 2 partial warning)
- 신규: `v3/tests/unit/test_release_contract.py` — 계약 상수/패턴 회귀 방지

**분류 C — 실행 환경 안정화**
- `run.bat` / `run_dev.bat`: `.venv` 부재 시 명확한 에러 메시지
- `build.py`: PyInstaller 미설치 / Python 버전 불일치 사전 체크

**분류 D — 스모크 자동화 (부분)**
- `RELEASE_SMOKE_CHECKLIST.md` 중 자동화 가능한 항목:
  - EXE 실행 가능 여부 (--version 또는 즉시 종료 옵션)
  - DB 초기화 테스트 (`v3/models/dhr_database.py` import + schema check)
- 나머지 GUI 의존 항목은 체크리스트 유지

### 2.2 Out-of-Scope
- CI/CD 시스템 도입 (GitHub Actions 등)
- 코드 서명 (Authenticode)
- 자동 업데이터 / 델타 배포
- 새 기능 추가

---

## 3. Requirements

### 3.1 Functional
1. **단일 진입점**: `python v3/release.py` 한 번으로 build → deploy → check 실행
2. **Fail-Fast**: 중간 단계 실패 시 즉시 중단 + 원인 명시
3. **GREEN 상태 달성**: 릴리즈 준비 후 `check_release_artifacts.py` 종료 코드 0
4. **계약 회귀 방지**: `APP_NAME`, `RELEASE_VERSION`, `ZIP_PATTERN` 변경 시 테스트로 감지
5. **EXE 무결성 확인**: 0바이트 / 손상 EXE를 체커가 FAIL로 분류

### 3.2 Non-Functional
- 기존 스크립트 인터페이스 보존 (`build.py`, `deploy.py` 단독 실행도 계속 동작)
- Python 3.9 호환성 유지
- 27/27 테스트 무회귀 + 신규 테스트 추가
- 실행 시간 증가 최소 (체크 오버헤드 ≤ 2초)

---

## 4. Risks

| 리스크 | 영향 | 완화 |
|---|---|---|
| 실제 `build.py` 실행이 PyInstaller 의존 → CI 환경 부재 시 검증 곤란 | 수동 검증 한정 | 계약 테스트는 모킹으로, 실빌드는 수동 QA |
| `release.py` 통합 과정에서 기존 `build.py` / `deploy.py` 시그니처 깨짐 | 기존 사용자 스크립트 파손 | `main()` 함수 유지, import 경로 보존 |
| EXE 크기 하한값이 빌드 옵션 변화에 민감 | False positive FAIL | 보수적 하한 (예: 10MB), CLAUDE.md에 근거 기록 |
| 스모크 자동화가 GUI 의존으로 실행 실패 | 헤드리스 환경 파손 | import/schema 레벨만 자동화, GUI는 체크리스트 유지 |

---

## 5. Definition of Done

- [ ] `python v3/release.py` 단일 명령 실행 가능
- [ ] `python v3/check_release_artifacts.py` 종료 코드 0 (수동 QA 환경)
- [ ] `v3/tests/unit/test_release_contract.py` 신규 테스트 통과
- [ ] 27/27 + 신규 테스트 전부 pass
- [ ] `DEPLOY_GUIDE.md` 릴리즈 절차가 단일 명령 기반으로 갱신
- [ ] 완료 보고서: `docs/04-report/features/release_pipeline_hardening.report.md`

---

## 6. Next Step

`/pdca design release_pipeline_hardening` — `release.py` 인터페이스, 검증 강화 항목, 계약 테스트 설계를 정의한다.
