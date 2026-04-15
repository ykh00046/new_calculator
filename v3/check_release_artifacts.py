"""
배포 산출물 최신성과 패키지 구성을 점검하는 릴리스 검증 스크립트.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path


APP_NAME = "DHR_Generator"
RELEASE_VERSION = "v3.0.0"
MIN_EXE_SIZE_MB = 10
ZIP_PATTERN = re.compile(
    rf"^{re.escape(APP_NAME)}_{re.escape(RELEASE_VERSION)}_(\d{{8}})\.zip$"
)
REQUIRED_PACKAGE_ITEMS = [
    f"{APP_NAME}.exe",
    "resources/",
    "README.md",
    "DEPLOY_GUIDE.md",
    "RELEASE_SMOKE_CHECKLIST.md",
]
ROOT_DOCS = ["README.md", "DEPLOY_GUIDE.md", "RELEASE_SMOKE_CHECKLIST.md"]


def format_path(path: Path) -> str:
    return path.as_posix()


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    v3_root = repo_root / "v3"
    exe_path = v3_root / "dist" / f"{APP_NAME}.exe"
    zip_candidates = sorted(
        (
            path
            for path in v3_root.glob(f"{APP_NAME}_{RELEASE_VERSION}_*.zip")
            if ZIP_PATTERN.match(path.name)
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    latest_zip = zip_candidates[0] if zip_candidates else None
    failures: list[str] = []
    warnings: list[str] = []

    print("== Release Artifact Check ==")
    print(f"- Repo root: {format_path(repo_root)}")
    print(f"- v3 root: {format_path(v3_root)}")
    print(f"- Expected exe: {format_path(exe_path)}")
    print(f"- Expected zip pattern: {APP_NAME}_{RELEASE_VERSION}_YYYYMMDD.zip")

    for doc_name in ROOT_DOCS:
        doc_path = repo_root / doc_name
        if doc_path.exists():
            print(f"[PASS] Root doc present: {doc_name}")
        else:
            failures.append(f"루트 문서 누락: {doc_name}")

    if exe_path.exists():
        exe_mtime = exe_path.stat().st_mtime
        exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"[PASS] EXE present: {format_path(exe_path)}")
        if exe_size_mb < MIN_EXE_SIZE_MB:
            failures.append(
                f"EXE 크기가 하한({MIN_EXE_SIZE_MB}MB) 미만입니다: {exe_size_mb:.1f}MB"
            )
        else:
            print(f"[PASS] EXE size OK: {exe_size_mb:.1f} MB")
    else:
        exe_mtime = None
        failures.append(f"실행 파일 누락: {format_path(exe_path)}")

    if latest_zip is None:
        failures.append(
            f"배포 ZIP 누락: {APP_NAME}_{RELEASE_VERSION}_YYYYMMDD.zip 형식의 파일이 없습니다."
        )
    else:
        print(f"[PASS] Latest ZIP found: {latest_zip.name}")
        zip_mtime = latest_zip.stat().st_mtime
        if exe_mtime is not None and zip_mtime < exe_mtime:
            failures.append(
                "최신 ZIP이 EXE보다 오래되었습니다. build.py 이후 deploy.py를 다시 실행해야 합니다."
            )

        try:
            with zipfile.ZipFile(latest_zip) as archive:
                archive_names = archive.namelist()
        except zipfile.BadZipFile:
            failures.append(f"ZIP 파일을 열 수 없습니다: {latest_zip.name}")
            archive_names = []

        package_root = latest_zip.stem
        for item in REQUIRED_PACKAGE_ITEMS:
            expected_name = f"{package_root}/{item}"
            if item.endswith("/"):
                exists = any(name.startswith(expected_name) for name in archive_names)
            else:
                exists = expected_name in archive_names

            if exists:
                print(f"[PASS] ZIP contains: {expected_name}")
            else:
                failures.append(f"ZIP 내부 누락: {expected_name}")

        if not any(name.endswith(".exe") for name in archive_names):
            warnings.append("ZIP 내부에 실행 파일 엔트리가 보이지 않습니다.")

    if failures:
        print("\n[FAIL] Release artifact check failed")
        for failure in failures:
            print(f"- {failure}")
        for warning in warnings:
            print(f"- 경고: {warning}")
        return 1

    print("\n[PASS] Release artifact check passed")
    for warning in warnings:
        print(f"- 경고: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
