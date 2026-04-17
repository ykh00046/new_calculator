# Manual Input Save/Export E2E — Plan

> **Author**: AI Assistant
> **Created**: 2026-04-17
> **Status**: Plan
> **Cycle**: PDCA #12
> **Parent**: PDCA #11 (manual_input_qa_coverage) Follow-up

---

## 1. Overview & Purpose

### 1.1 배경
PDCA #11에서 `ManualInputInterface`의 순수 로직(Layer A)·UI/테이블 로직(Layer B)·DB 최소 Mock(Layer C)에 대한 19 test case(52/52 pass)를 확보했다. 그러나 다음 경로는 **Out-of-Scope**로 의도적으로 미검증 상태다.

- `_save_and_export` (manual_input_interface.py:309-390) — Save/Export 오케스트레이션 전체
- `ExcelExporter.export_to_excel` — 템플릿 복사 + 셀 매핑 + 자재 행 기입
- `ExcelExporter.export_to_pdf` — 스캔 효과 적용 PDF 생성 (win32com → PyMuPDF → PIL → PDF)

현재 이 3 단계는 **수동 QA에만 의존**한다. 템플릿 경로/셀 매핑/자재 행 시작 행(`data_start_row`) 등 설정 변경 시 회귀를 사전 감지할 방법이 없다.

### 1.2 목적
`_save_and_export` 흐름의 **파일 생성·문서 구조·에러 경로**를 자동화 테스트로 방어. 단, Windows/Excel COM(win32com) 실제 호출은 CI 비친화적이며 PDCA #11 원칙("프로덕션 코드 무변경, Headless Qt")과 충돌 — **경계(boundary) Mock** 전략으로 우회한다.

### 1.3 Non-Goals (이번 사이클에서 하지 않는 것)
- 실제 Excel.Application 호출 / 실제 PDF 변환 / 스캔 효과 픽셀 검증
- `image_processor.create_signed_image` 검증 — 현재 `_save_and_export`는 `include_image=False`로 서명 합성 미호출 (manual input 경로에서는 미사용). 서명 QA는 별도 사이클 필요 시 분리.
- dhr_bulk_generator 경로 (PDCA #8 관련, 다른 후보로 분리)

---

## 2. Scope

### 2.1 In-Scope

**1) Integration Orchestration 테스트** (`test_manual_input_save_export.py` 신규, 또는 기존 `test_manual_input_interface.py`에 Layer D 확장)
- `_save_and_export` 정상 흐름: 검증 → DB save → Excel export → PDF export 순서 호출
- DB 저장 데이터 구조 검증 (`record_data`, `details_data`)
- Excel 호출 인자 검증 (`export_data` dict, `include_work_time` 플래그)
- PDF 호출 인자 검증 (`scan_effects_panel.get_data()` 전달)
- `product_lot_edit`이 DB가 반환한 LOT로 갱신되는지 확인

**2) Excel Content 테스트** (openpyxl 직접, win32com 불필요)
- `ExcelExporter.export_to_excel`이 `resources/template.xlsx`를 복사하여 `{product_lot}.xlsx` 생성
- `cell_mapping` 기반으로 `date`, `product_lot`, `total_amount`, `work_time`(on/off) 셀 기입
- `data_start_row`부터 자재 N행이 `material_name_col`·`ratio_col`·`theory_amount_col` 등에 기입되는지 검증
- `include_work_time=False`일 때 `work_time` 셀이 공백 처리되는지

**3) Error Path 테스트**
- DB save 실패 → `QMessageBox.critical` 호출 + 함수 조기 종료 (Excel/PDF 미호출)
- Excel export 실패 (`export_to_excel` returns `None`) → `Partial Success` 경고
- PDF export 실패 (`export_to_pdf` returns `None`) → `Partial Success` 경고 + Excel 결과는 유지

### 2.2 Out-of-Scope
- `_excel_to_temp_pdf` (win32com Excel.Application) — 실 호출 불가
- `_pdf_to_images` / `_apply_scan_effects` / `_images_to_final_pdf` — PyMuPDF/PIL 실 호출, 효용 대비 비용 큼
- `image_processor.create_signed_image` — manual input에서 미호출 경로
- Excel Formula 재계산 (openpyxl은 값 재계산 안 함, 실제 확인은 Excel 필요)

---

## 3. Requirements

### 3.1 Functional
1. `_save_and_export`의 흐름 제어(검증→DB→Excel→PDF) 자동 검증
2. `ExcelExporter.export_to_excel`의 템플릿 복사·셀 기입 검증 (헤드리스)
3. 각 단계 실패 시 사용자 알림·로그 경로 검증

### 3.2 Non-Functional
- **프로덕션 코드 무변경 원칙 유지** (PDCA #11 feedback). 필요 시 기존 DI 인자(`dhr_db`, `lot_manager`)와 `monkeypatch`/`patch`만 사용.
- Python 3.9 호환성
- 테스트 Headless: `QT_QPA_PLATFORM=offscreen`
- 테스트 실행 시간 증가 ≤ 1.0초 (현재 0.669초 → 목표 < 1.7초)
- 총 테스트 수 52 → **65± (+13 내외)**
- win32com / 실제 Excel / 실제 PDF 변환 불필요

### 3.3 Risks

| 리스크 | 영향 | 완화 |
|---|---|---|
| `resources/template.xlsx` 부재/변경 시 Excel 테스트 실패 | Medium | `os.path.exists(template_file)` 선검사 → 없으면 SkipTest (PDCA #11 `_ensure_ui_test_dependencies` 패턴 재사용) |
| `cell_mapping`이 `config.json`에서 런타임 로드되어 테스트 환경에 따라 달라짐 | Medium | 테스트 전용 `cell_mapping`을 주입하거나, 실 config를 읽되 "매핑에 존재하는 키만 검증" 방식으로 유연화 |
| `ExcelExporter.__init__`이 `config.get("paths.output", "실적서")` 폴더를 생성 | Low | `tempfile.TemporaryDirectory`로 `paths.output` 임시 override (monkeypatch) |
| win32com import 자체가 non-Windows에서 실패 | Low | 이미 파일 상단 import, 현재 개발자 환경이 Windows 고정이므로 기존 정책 유지. 필요 시 `try/except ImportError` 가드는 별도 사이클 |
| `_save_and_export` 내부에서 `from models.excel_exporter import ExcelExporter`를 지연 import | Low | `patch("ui.panels.manual_input_interface.ExcelExporter", ...)` 대신 `patch("models.excel_exporter.ExcelExporter", ...)` 또는 함수 내 import를 감안한 `patch` 경로 확인 필요 |

---

## 4. Test Strategy

### 4.1 Layer 구조 (PDCA #11 연속성)

| Layer | 범위 | 기법 | 예상 테스트 수 |
|---|---|---|---|
| D1 — Orchestration | `_save_and_export` 흐름 | `MagicMock` + `patch` (ExcelExporter 전체 Mock) | 4~5 |
| D2 — Excel Content | `export_to_excel` 실 호출 | 실 템플릿 + `tempfile` + openpyxl 재로드 검증 | 4~5 |
| D3 — Error Paths | 각 단계 실패 | `side_effect` / `return_value=None` | 3 |

### 4.2 핵심 기법

**D1 — `ExcelExporter` Mock 주입 지점**:
```python
# _save_and_export 내부에 "from models.excel_exporter import ExcelExporter"가 있으므로
with patch("models.excel_exporter.ExcelExporter") as mock_cls:
    mock_instance = mock_cls.return_value
    mock_instance.export_to_excel.return_value = "/tmp/X.xlsx"
    mock_instance.export_to_pdf.return_value = "/tmp/X.pdf"
    panel._save_and_export()
    # assertions
```

**D2 — 실 템플릿 사용 + 임시 출력 경로**:
```python
def setUp(self):
    self.tmp = tempfile.mkdtemp()
    self.cfg_patch = patch("models.excel_exporter.config")
    mock_cfg = self.cfg_patch.start()
    mock_cfg.get.side_effect = lambda k, d=None: {
        "paths.output": self.tmp,
        "excel.cell_mapping": {...},
    }.get(k, d)
```

**D3 — 에러 경로**:
```python
mock_db.save_dhr_record.side_effect = RuntimeError("simulated")
with patch("ui.panels.manual_input_interface.QMessageBox") as qmb:
    panel._save_and_export()
    qmb.critical.assert_called_once()
    mock_cls.return_value.export_to_excel.assert_not_called()
```

---

## 5. Plan Steps

1. **조사** (0.5h)
   - `_save_and_export`의 `ExcelExporter` import 경로 정확히 확인 (함수 내 지연 import)
   - `config.get("excel.cell_mapping", {})`의 실제 키 목록 확인 (`config.json` 또는 기본값)
   - `resources/template.xlsx` 존재 확인 및 셀 배치 파악 (이미 존재 확인 ✅)

2. **D1 Orchestration 테스트 작성** (1h)
   - `test_manual_input_save_export.py` 신규 파일 (또는 기존 파일에 `class TestSaveAndExport` 추가)
   - 4~5 케이스: 정상 흐름, DB save 호출 인자, Excel 호출 인자, PDF 호출 인자, LOT 갱신

3. **D2 Excel Content 테스트 작성** (1h)
   - 실 템플릿 + tempfile로 `export_to_excel` 호출
   - openpyxl로 결과 재로드 후 주요 셀·자재 행 N줄 검증

4. **D3 Error Path 테스트 작성** (0.5h)
   - DB 실패 / Excel 실패 / PDF 실패 3 케이스

5. **실행 및 조정** (0.5h)
   - `QT_QPA_PLATFORM=offscreen python v3/tests/run_tests.py`
   - Qt/Mock 시그니처 이슈(PDCA #11 F-01 교훈) 재발 여부 확인
   - 총 카운트 52 → 65± 확인

6. **커밋** (경계 단위)
   - `test: add manual input save/export orchestration tests` (D1)
   - `test: add Excel content verification with real template` (D2)
   - `test: add save/export error path coverage` (D3)

7. **Check/Report** (1h)
   - `/pdca analyze manual_input_save_export_e2e`
   - `/pdca report manual_input_save_export_e2e`
   - `/pdca archive manual_input_save_export_e2e`

**총 예상 소요**: 4~5시간 (1 세션)

---

## 6. Success Criteria (DoD)

- [ ] D1/D2/D3 3 레이어 신규 테스트 12~13 케이스 추가
- [ ] 총 테스트 52 → 64 이상 (+12±)
- [ ] 테스트 실행 시간 < 1.7초
- [ ] 프로덕션 코드 변경 0 라인 (DI·patch만 활용)
- [ ] `resources/template.xlsx` 부재 시 graceful skip
- [ ] Match Rate ≥ 90% (정식 PDCA, Design/Analysis 생략 없이 전체 단계 수행)
- [ ] 새 Qt Mock 이슈가 발견되면 `project_pdca_status.md` 교훈 블록 갱신

---

## 7. Appendix — 관련 파일

| 파일 | 역할 |
|---|---|
| `v3/ui/panels/manual_input_interface.py:309-390` | `_save_and_export` 대상 |
| `v3/models/excel_exporter.py:38-74` | `export_to_excel` 대상 |
| `v3/models/excel_exporter.py:76-114` | `export_to_pdf` (외부 경계는 Mock) |
| `v3/tests/unit/test_manual_input_interface.py` | PDCA #11 기 테스트 (참고 + 패턴 재사용) |
| `v3/resources/template.xlsx` | D2 실 입력 자원 |
| `v3/config/config.json` | `excel.cell_mapping` 출처 |

---

## 8. Next Phase

- **다음**: `/pdca design manual_input_save_export_e2e`
- Design 문서에서 확정할 내용:
  - 정확한 테스트 파일 배치 (신규 파일 vs 기존 확장)
  - `cell_mapping` 주입 전략 (실 config 사용 vs 테스트 전용 매핑)
  - 각 테스트 케이스 시그니처 목록
