"""
Release pipeline single entrypoint.

build.py -> deploy.py -> check_release_artifacts.py 를 순차 실행하고
중간 단계 실패 시 즉시 종료한다. 기존 스크립트들은 독립 실행을 그대로
지원하며, 이 스크립트는 얇은 오케스트레이터일 뿐이다.

사용법 (v3/ 디렉터리에서 실행):
    python release.py
    python release.py --skip-build      # 기존 dist/EXE 재사용
    python release.py --skip-package    # 기존 ZIP 재사용
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parent
if str(V3_ROOT) not in sys.path:
    sys.path.insert(0, str(V3_ROOT))

import build
import deploy
import check_release_artifacts as checker


EXIT_OK = 0
EXIT_BUILD_FAILED = 10
EXIT_DEPLOY_FAILED = 20
EXIT_CHECK_FAILED = 30


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DHR Generator release pipeline (build -> package -> verify)"
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="기존 dist/DHR_Generator.exe 재사용",
    )
    parser.add_argument(
        "--skip-package",
        action="store_true",
        help="기존 배포 ZIP 재사용",
    )
    return parser.parse_args()


def run_pipeline(args: argparse.Namespace) -> int:
    os.chdir(V3_ROOT)
    print("== Release Pipeline ==")
    print(f"- cwd: {V3_ROOT.as_posix()}")

    if args.skip_build:
        print("\n[1/3] Build -- skipped")
    else:
        print("\n[1/3] Build")
        if not build.build_exe():
            print("[FAIL] build step failed")
            return EXIT_BUILD_FAILED

    if args.skip_package:
        print("\n[2/3] Package -- skipped")
    else:
        print("\n[2/3] Package")
        if not deploy.create_deployment_package():
            print("[FAIL] deploy step failed")
            return EXIT_DEPLOY_FAILED

    print("\n[3/3] Verify")
    check_result = checker.main()
    if check_result != 0:
        print("[FAIL] check_release_artifacts reported failures")
        return EXIT_CHECK_FAILED

    print("\n[OK] Release pipeline complete")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(run_pipeline(parse_args()))
