# EXE 실행 파일 만들기 가이드

## 주의사항 ⚠️

Streamlit 앱을 EXE로 만드는 것은 **권장하지 않습니다**. 이유:
- 파일 크기 매우 큼 (300-600MB)
- 실행 속도 느림 (일반 실행 대비 2-3배)
- Streamlit 특성상 브라우저가 필요해 완전한 독립 실행 아님
- 업데이트시 매번 재빌드 필요

**배치 파일(.bat) 사용을 강력히 권장합니다!**

---

## 방법 1: PyInstaller 사용 (고급 사용자용)

### 1단계: PyInstaller 설치

```bash
pip install pyinstaller
```

### 2단계: spec 파일 생성

`dashboard.spec` 파일 생성:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=['C:\\X\\material_box\\production_analysis_dashboard'],
    binaries=[],
    datas=[
        ('components', 'components'),
        ('utils', 'utils'),
        ('data_access', 'data_access'),
        ('config', 'config'),
        ('.streamlit', '.streamlit'),
        ('C:\\X\\material_box\\Raw_material_dashboard_v2\\data\\production_analysis.db', 'data'),
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'altair',
        'sqlite3',
        'streamlit.runtime.scriptrunner.magic_funcs',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ProductionDashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='dashboard.ico'  # 아이콘 있으면
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ProductionDashboard',
)
```

### 3단계: 빌드 실행

```bash
pyinstaller dashboard.spec
```

### 4단계: 결과 확인

`dist/ProductionDashboard/` 폴더에 EXE 파일 생성됨

---

## 방법 2: Auto-PY-to-EXE (GUI 방식)

### 1단계: 설치

```bash
pip install auto-py-to-exe
```

### 2단계: GUI 실행

```bash
auto-py-to-exe
```

### 3단계: 설정

1. **Script Location**: `app.py` 선택
2. **One Directory**: 선택
3. **Console Based**: 선택
4. **Additional Files**: 추가
   - `components` 폴더
   - `utils` 폴더
   - `data_access` 폴더
   - `config` 폴더
   - `.streamlit` 폴더
   - 데이터베이스 파일

### 4단계: 변환

"CONVERT .PY TO .EXE" 버튼 클릭

---

## 방법 3: cx_Freeze (대안)

### 1단계: 설치

```bash
pip install cx_Freeze
```

### 2단계: setup.py 생성

```python
import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["streamlit", "pandas", "altair", "sqlite3"],
    "include_files": [
        ("components", "components"),
        ("utils", "utils"),
        ("data_access", "data_access"),
        ("config", "config"),
        (".streamlit", ".streamlit"),
    ],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="ProductionDashboard",
    version="2.1.1",
    description="Production Analysis Dashboard",
    options={"build_exe": build_exe_options},
    executables=[Executable("app.py", base=base, target_name="ProductionDashboard.exe")],
)
```

### 3단계: 빌드

```bash
python setup.py build
```

---

## 문제 해결

### 문제 1: ModuleNotFoundError

**해결**: spec 파일의 `hiddenimports`에 누락된 모듈 추가

```python
hiddenimports=[
    'streamlit',
    'streamlit.runtime',
    'streamlit.runtime.scriptrunner',
    # 추가...
]
```

### 문제 2: 데이터베이스 경로 오류

**해결**: `config/settings.py` 수정

```python
import os
import sys

if getattr(sys, 'frozen', False):
    # EXE로 실행시
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # 일반 실행시
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(BASE_PATH, 'data', 'production_analysis.db')
```

### 문제 3: 브라우저가 안 열림

**해결**: 배치 파일 래퍼 생성

`ProductionDashboard.bat`:
```batch
@echo off
start ProductionDashboard.exe
timeout /t 3 /nobreak >nul
start http://localhost:8501
```

---

## 권장 사항

### ✅ 배치 파일 사용 (이미 제공됨)
- `start_dashboard.bat` - 간단 버전
- `start_dashboard_advanced.bat` - 고급 버전 (에러 체크)

### ❌ EXE 파일은 다음 경우에만
- Python 설치가 불가능한 환경
- 외부 배포가 필요한 경우
- 보안상 Python 설치가 제한된 경우

---

## 최종 권장 방법

### 회사 내부 사용시

1. **간단한 배포**:
   ```
   start_dashboard_advanced.bat 파일을 각 직원 PC에 복사
   → 더블클릭으로 실행
   ```

2. **바탕화면 바로가기**:
   ```
   create_desktop_shortcut.vbs를 더블클릭
   → 자동으로 바탕화면에 바로가기 생성
   ```

3. **네트워크 공유**:
   ```
   서버 PC 한 대에서만 실행
   → 다른 직원들은 브라우저로 접속 (http://서버IP:8504)
   ```

---

## 도움이 필요하면

- EXE 빌드 중 오류 발생시 오류 메시지 공유
- 특정 환경에 맞는 빌드 방법 문의
