# 배합 프로그램 v3 (Manufacturing Batch Recipe Management System)

> 제조업 원료 배합 관리 및 품질 보증을 위한 데스크톱 애플리케이션

## 1. 프로젝트 개요

- **Version**: v3.0
- **Status**: Deployment Ready (Phase 5 Completed)
- **Tech Stack**: Python 3.9+, PySide6, SQLite

## 2. 실행 방법 (Deployment)

### 2.1 실행 파일 (Recommended)

`dist/DHR_Mixing_System` 폴더 내의 실행 파일을 직접 실행합니다.

```bash
dist/DHR_Mixing_System/DHR_Mixing_System.exe
```

### 2.2 배포 패키지

`dist/DHR_Mixing_System_v3.zip` 파일을 복사하여 다른 PC에 배포할 수 있습니다.

- 압축 해제 후 `DHR_Mixing_System.exe` 실행
- 별도의 Python 설치 불필요 (Standalone)

## 3. 개발 환경 설정

- `CLAUDE.md` 참조
- 가상환경: `.venv` (Pure Environment)
- 빌드: `pyinstaller DHR_Mixing_System.spec`
