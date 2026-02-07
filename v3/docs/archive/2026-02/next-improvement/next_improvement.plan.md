# PDCA Cycle #4: 런타임 버그 수정 및 코드 품질 개선

> **Phase**: Plan
> **Date**: 2026-02-07
> **Priority**: CRITICAL (런타임 크래시 2건 포함)

---

## 1. 개요

코드 분석기가 발견한 **2건의 런타임 크래시 버그** + **10건의 WARNING 레벨 코드 품질 이슈**를 수정합니다.

---

## 2. 수정 항목 (CRITICAL — 런타임 크래시)

### Issue 1: admin_signature_panel.py — AttributeError

**파일**: `v3/ui/panels/admin_signature_panel.py` (lines 346-347)

**문제**: `config.config['signature']` 및 `config.save()` 호출하지만 `Config` 클래스에는:
- `_data` 속성 사용 (`.config` 아님)
- `_save_config()` 메서드 사용 (`.save()` 아님)

**수정**:
```python
# Before (line 346-347):
config.config['signature'] = current_sig_config
config.save()

# After:
config._data['signature'] = current_sig_config
config._save_config()
```

### Issue 2: manual_input_interface.py — ImportError

**파일**: `v3/ui/panels/manual_input_interface.py` (line 582)

**문제**: `from models.excel_handler import ExcelHandler` — 모듈 `models.excel_handler` 존재하지 않음. 실제 클래스는 `models.excel_exporter.ExcelExporter`.

**수정**: `_save_and_export()` 메서드 전체의 import 및 API 호출을 `ExcelExporter` 기준으로 수정.

---

## 3. 수정 항목 (WARNING — 코드 품질)

### Issue 3: database.py — 미사용 import 정리

**파일**: `v3/models/database.py` (lines 9, 11, 17-18)

- `Union` import 제거 (미사용)
- `import pandas as pd` 제거 (미사용)
- 고아 주석 `# Google Sheets 백업 관련 임포트 추가` 제거

### Issue 4: lot_manager.py — lazy import → top-level

**파일**: `v3/models/lot_manager.py` (lines 32-33, 37-38, 53)

- `from utils.logger import logger` 를 메서드 내부에서 파일 상단으로 이동

### Issue 5: main_window.py — 비활성 상태 스타일 미구분

**파일**: `v3/ui/main_window.py` (lines 385-392)

- `_set_save_button_state()` if/else 분기가 동일 → disabled일 때 다른 스타일/텍스트 적용
```python
# After:
if enabled:
    self.save_btn.setText("배합 저장")
    self.save_btn.setStyleSheet(UIStyles.get_primary_button_style())
else:
    self.save_btn.setText("배합 저장")
    self.save_btn.setStyleSheet(UIStyles.get_disabled_button_style())
```
(UIStyles에 `get_disabled_button_style`이 없으면 opacity/색상 변경으로 구분)

### Issue 6: image_processor.py — traceback.print_exc() 제거

**파일**: `v3/models/image_processor.py` (lines 297-300)

```python
# Before:
except Exception as e:
    import traceback
    logger.error(f"Image composition error: {e}")
    traceback.print_exc()

# After:
except Exception as e:
    logger.error(f"Image composition error: {e}", exc_info=True)
```

### Issue 7: config_manager.py — 타입 힌트 수정

**파일**: `v3/config/config_manager.py` (line 170)

```python
# Before:
def _hash_password(self, password: str, salt: bytes = None) -> Tuple[str, str]:

# After:
def _hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
```

`from typing import Any, Dict, Optional, Tuple` 로 import 수정 (line 15)

### Issue 8: settings.py — RECIPE_FILE/TEMPLATE_FILE 이중 정의

**파일**: `v3/config/settings.py`

- `RECIPE_FILE`, `TEMPLATE_FILE` 최초 정의(lines 60, 62)가 `_first_existing()` (lines 137+)에서 재정의됨
- 최초 정의 제거하여 혼란 방지

### Issue 9: settings.py — os.listdir 안전 가드

**파일**: `v3/config/settings.py` (lines 138-157)

- `os.listdir(RESOURCES_FOLDER)` 호출 전 `os.path.isdir()` 가드 추가

### Issue 10: lot_manager.py — list[tuple] 타입 힌트 호환성

**파일**: `v3/models/lot_manager.py` (line 41)

```python
# Before (Python 3.10+ 문법):
def get_lot(self, item_code: str, work_date: str) -> list[tuple[str, str]]:

# After (Python 3.9 호환):
def get_lot(self, item_code: str, work_date: str) -> List[Tuple[str, str]]:
```

`from typing import List, Tuple` import 추가

### Issue 11: database.py — 미사용 Union import 후 Optional 누락 확인

- `Union` 제거 후 `Optional` 이 필요한지 확인

### Issue 12: test_runner.py 파일명 오해 소지

- `tests/test_runner.py`는 실제로 PDF 재출력 도구이지만 파일명이 테스트 러너로 오해됨
- 파일명을 `pdf_reexport_tool.py`로 변경 (import 참조 없음 확인 필요)

---

## 4. 제외 항목 (다음 사이클로 연기)

| 항목 | 사유 |
|------|------|
| DRY: PasteableTable 중복 추출 | 대규모 리팩토링 — 별도 사이클 |
| SRP: DhrBulkGenerator.generate() 분해 | 대규모 리팩토링 — 별도 사이클 |
| 테스트 커버리지 확대 | 별도 테스트 전용 사이클 |
| 타입 힌트 일괄 추가 | 별도 사이클 |
| BaseDatabaseManager 추출 | 대규모 리팩토링 — 별도 사이클 |

---

## 5. 검증 기준

- [ ] `python -m pytest tests/ -v` → 25/25 통과
- [ ] `admin_signature_panel.py` 설정 저장 시 AttributeError 없음
- [ ] `manual_input_interface.py` import 정상 확인
- [ ] `grep -rn "import pandas" v3/models/database.py` → 0건
- [ ] `grep -rn "traceback.print_exc" v3/models/` → 0건
- [ ] Python 3.9 호환 타입 힌트 확인

---

## 6. 영향 범위

- 총 수정 파일: **8개**
- 기능 변경: 없음 (버그 수정 + 코드 정리)
- 신규 파일: 없음
- 삭제 파일: 없음 (test_runner.py → 이름 변경만)
