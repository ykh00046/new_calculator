# Release Pipeline Hardening — Design

> **Author**: AI Assistant
> **Created**: 2026-04-15
> **Status**: Design
> **Parent Plan**: `v3/docs/01-plan/features/release_pipeline_hardening.plan.md`

---

## 1. Goals

1. `python v3/release.py` **단일 명령**으로 빌드 → 패키지 → 검증 수행
2. `check_release_artifacts.py`에 **EXE 크기 하한** + **ZIP 내부 핵심 리소스 검증** 추가
3. 계약 상수 회귀 방지 단위 테스트 (`test_release_contract.py`)
4. 기존 `build.py` / `deploy.py` 단독 실행 인터페이스 **보존**

---

## 2. Architecture

```
┌─────────────────────────────────────────────┐
│ v3/release.py (NEW)                         │
│  ├─ parse_args() — --skip-build, --skip-zip │
│  ├─ step 1: build.build_exe()     → fail→2  │
│  ├─ step 2: deploy.create_deployment_package│
│  └─ step 3: check.main()          → exit    │
└─────────────────────────────────────────────┘
         │        │         │
         ▼        ▼         ▼
   build.py  deploy.py  check_release_artifacts.py
   (unchanged signatures — still runnable solo)
```

**원칙**: `release.py`는 얇은 오케스트레이터. 기존 스크립트의 `build_exe()` / `create_deployment_package()` / `main()`를 import해서 호출. 각 단계 실패 시 `sys.exit(N)`으로 **Fail-Fast**.

---

## 3. Module Design

### 3.1 `v3/release.py` (신규, ~80 LOC)

```python
"""
Release pipeline single entrypoint.
빌드 → 패키지 → 검증을 순차 실행하고 중간 실패 시 즉시 종료한다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import build
import deploy
import check_release_artifacts as checker


EXIT_OK = 0
EXIT_BUILD_FAILED = 10
EXIT_DEPLOY_FAILED = 20
EXIT_CHECK_FAILED = 30


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DHR Generator release pipeline")
    parser.add_argument("--skip-build", action="store_true", help="기존 dist/EXE 재사용")
    parser.add_argument("--skip-package", action="store_true", help="기존 ZIP 재사용")
    return parser.parse_args()


def run_pipeline(args: argparse.Namespace) -> int:
    print("== Release Pipeline ==")

    if not args.skip_build:
        print("\n[1/3] Build")
        if not build.build_exe():
            return EXIT_BUILD_FAILED
    else:
        print("\n[1/3] Build — skipped")

    if not args.skip_package:
        print("\n[2/3] Package")
        if not deploy.create_deployment_package():
            return EXIT_DEPLOY_FAILED
    else:
        print("\n[2/3] Package — skipped")

    print("\n[3/3] Verify")
    check_result = checker.main()
    if check_result != 0:
        return EXIT_CHECK_FAILED

    print("\n[OK] Release pipeline complete")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(run_pipeline(parse_args()))
```

**주의**:
- `build.py` / `deploy.py`는 `os.getcwd()` 기반으로 `dist/` 등을 탐색 → `release.py`도 `v3/` cwd 전제. README에 명시.
- `check_release_artifacts.main()` 기존 시그니처 (`() -> int`) 그대로 사용.

### 3.2 `check_release_artifacts.py` 강화

추가 상수:
```python
MIN_EXE_SIZE_MB = 10  # PyInstaller onefile 최소 기준 (경험적 하한)
REQUIRED_ZIP_RESOURCES = [
    "resources/",  # 이미 확인됨
    # 핵심 하위 자원 — 존재하면 확인, 없으면 warning
]
```

추가 검증 블록 (EXE 검증 부분에):
```python
if exe_path.exists():
    exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
    if exe_size_mb < MIN_EXE_SIZE_MB:
        failures.append(
            f"EXE 크기가 하한({MIN_EXE_SIZE_MB}MB) 미만입니다: {exe_size_mb:.1f}MB"
        )
    else:
        print(f"[PASS] EXE size OK: {exe_size_mb:.1f} MB")
```

종료 코드:
- `0`: pass
- `1`: fail (기존 유지)

`warnings`는 체결 상태에 영향 없음 (기존 동작 보존).

### 3.3 `v3/tests/unit/test_release_contract.py` (신규)

```python
"""
Release contract regression tests.
APP_NAME / RELEASE_VERSION / ZIP_PATTERN 변경 시 즉시 감지한다.
"""
import re
import unittest
import sys
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parents[2]
if str(V3_ROOT) not in sys.path:
    sys.path.insert(0, str(V3_ROOT))

import check_release_artifacts as checker


class TestReleaseContract(unittest.TestCase):
    def test_app_name_is_dhr_generator(self):
        self.assertEqual(checker.APP_NAME, "DHR_Generator")

    def test_release_version_semver(self):
        self.assertRegex(checker.RELEASE_VERSION, r"^v\d+\.\d+\.\d+$")

    def test_zip_pattern_matches_canonical_name(self):
        name = f"{checker.APP_NAME}_{checker.RELEASE_VERSION}_20260415.zip"
        self.assertIsNotNone(checker.ZIP_PATTERN.match(name))

    def test_zip_pattern_rejects_other_versions(self):
        name = "DHR_Generator_v2.9.9_20260415.zip"
        self.assertIsNone(checker.ZIP_PATTERN.match(name))

    def test_required_package_items_include_exe_and_resources(self):
        items = checker.REQUIRED_PACKAGE_ITEMS
        self.assertIn("DHR_Generator.exe", items)
        self.assertIn("resources/", items)
        self.assertIn("DEPLOY_GUIDE.md", items)

    def test_min_exe_size_reasonable(self):
        # 하한이 지나치게 낮거나 높지 않은지 방어
        self.assertGreaterEqual(checker.MIN_EXE_SIZE_MB, 5)
        self.assertLessEqual(checker.MIN_EXE_SIZE_MB, 200)
```

### 3.4 `DEPLOY_GUIDE.md` 갱신

릴리스 절차 섹션을 단일 명령 기반으로 축약:

```bash
cd v3
../.venv/Scripts/python.exe release.py
```

기존 3단계 수동 실행은 "고급/부분 실행" 섹션으로 보존.

---

## 4. Implementation Order

1. **`check_release_artifacts.py` 강화** — `MIN_EXE_SIZE_MB` 추가, EXE 크기 검증
2. **`test_release_contract.py` 신규** — 위 계약 테스트
3. **`v3/release.py` 신규** — 오케스트레이터
4. **`DEPLOY_GUIDE.md` 갱신** — 단일 명령 우선, 수동 절차는 advanced로 이동
5. **테스트 실행** — 27 + 6 신규 = 33/33 pass 기대
6. **(수동 QA)** — 실제 `python v3/release.py` 실행해 GREEN 확인 (PyInstaller 사용 가능 환경)

---

## 5. Commit Split Strategy

| # | Commit | 파일 |
|---|---|---|
| 1 | `feat: add MIN_EXE_SIZE check and release contract tests` | `v3/check_release_artifacts.py`, `v3/tests/unit/test_release_contract.py`, `v3/tests/run_tests.py` (테스트 등록 확인) |
| 2 | `feat: add release.py pipeline orchestrator` | `v3/release.py` |
| 3 | `docs: switch DEPLOY_GUIDE to single-command release` | `DEPLOY_GUIDE.md` |
| 4 | `docs: add PDCA #9 plan and design for release_pipeline_hardening` | plan/design 문서 |

---

## 6. Risks & Mitigations

| 위험 | 완화 |
|---|---|
| `release.py`가 `v3/` cwd 전제 → 루트에서 실행 시 실패 | 시작부에 `os.chdir(Path(__file__).parent)` 또는 명시적 에러 |
| `build.build_exe()` 반환값이 bool → 예외 전파 안 됨 | 반환값 엄격 체크 (이미 설계됨) |
| 테스트가 `check_release_artifacts` import 시 루트 경로 계산에 부작용 없도록 | 함수 호출 없이 상수만 참조 |
| `MIN_EXE_SIZE_MB = 10` 이 미래 빌드 옵션 변화에 부정확 | 디자인 문서에 근거 기록, 필요 시 조정 |

---

## 7. Definition of Done (Design 관점)

- [ ] `release.py` 인터페이스 확정 (args, exit codes)
- [ ] `check_release_artifacts.py` EXE 크기 검증 추가 사양 확정
- [ ] 계약 테스트 6개 케이스 정의
- [ ] 4개 커밋 분할 전략 합의
- [ ] 다음 단계: `/pdca do release_pipeline_hardening`

---

## 8. Open Questions

- `release.py`에 `--version` 오버라이드를 넣을지? → **No** (상수 계약 유지가 본 feature 목적)
- 스모크 자동화 (Plan 분류 D)는 이번 사이클에 포함할지? → **이번은 제외**. 별도 PDCA로 분리해 스코프 제어.
