# PDCA #12 완료 보고서 — manual_input_save_export_e2e

> **Author**: AI Assistant
> **Created**: 2026-04-17
> **Cycle**: PDCA #12
> **Status**: Completed
> **Feature**: Manual Input Save/Export E2E 검증 안전망
> **Match Rate**: 100%

---

## 1. Overview

PDCA #11에서 Out-of-Scope로 남겨둔 `ManualInputInterface._save_and_export` 흐름과 `ExcelExporter.export_to_excel`에 대한 경계(boundary) Mock 기반 E2E 테스트를 13개 추가. 프로덕션 코드 변경 없이 **Save/Export 오케스트레이션 + 실 템플릿 기반 셀 매핑 + 에러 경로 3종**을 자동화 안전망으로 확보했다. 테스트 총수 52 → **65** (+25%), 실행시간 0.894s → **1.346s** (<1.7초 목표 충족).

## 2. Goals vs Results

| 목표 | 결과 |
|---|---|
| `_save_and_export` DB→Excel→PDF 흐름 자동 검증 | ✅ D1 5 cases (TestSaveAndExportOrchestration) |
| `ExcelExporter.export_to_excel` 실 템플릿 셀 매핑 검증 | ✅ D2 5 cases (TestExcelExporterExportToExcel) |
| DB/Excel/PDF 각 단계 실패 경로 검증 | ✅ D3 3 cases (TestSaveAndExportErrorPaths) |
| 테스트 52 → 65 (+13) | ✅ 65/65 pass |
| 실행 시간 < 1.7초 | ✅ 1.346s (+0.452s) |
| 프로덕션 코드 변경 0 라인 | ✅ DI + patch만 사용 |
| Match Rate ≥ 90% | ✅ **100%** |
| `config.json` 변경 감지 메커니즘 | ✅ REAL_CELL_MAPPING sync 활성화 |

## 3. Commit Log

| # | Commit | Subject | LOC |
|---|---|---|---|
| 1 | `c8dd7e9` | test: add save/export orchestration and error-path tests | +186 |
| 2 | `d32de35` | test: add excel_exporter content verification with real template | +201 |
| 3 | `d4fa928` | docs: add PDCA #12 plan and design for manual_input_save_export_e2e | +575 |

순 코드 추가: **+387 LOC** (테스트 전용, 프로덕션 무변경)

## 4. Key Changes

### 4.1 `v3/tests/unit/test_manual_input_save_export.py` 신규 (186 LOC)

**Layer D1 — Orchestration (5 cases)**
- `test_save_and_export_calls_db_then_excel_then_pdf`
- `test_save_and_export_passes_resolved_lot_from_db`
- `test_save_and_export_passes_include_time_flag`
- `test_save_and_export_passes_materials_list_structure`
- `test_save_and_export_passes_scan_effects_to_pdf`

**Layer D3 — Error Paths (3 cases)**
- `test_db_failure_shows_critical_and_skips_export`
- `test_excel_failure_shows_partial_success_warning`
- `test_pdf_failure_keeps_excel_and_shows_partial_success`

**핵심 기법**:
- `_make_panel_with_data` 헬퍼로 제품명/수량/자재 2행이 채워진 패널 생성
- `_SaveExportTestBase` 공통 클래스로 D1/D3가 setUp/tearDown 공유
- `patch("models.excel_exporter.ExcelExporter")`로 지연 import 대응
- `patch("ui.panels.manual_input_interface.QMessageBox")`로 팝업 가드

### 4.2 `v3/tests/unit/test_excel_exporter.py` 신규 (201 LOC)

**Layer D2 — Excel Content (5 cases)**
- `test_creates_file_with_product_lot_name`
- `test_returns_none_when_template_missing`
- `test_writes_key_cells`
- `test_writes_material_rows_from_data_start_row`
- `test_omits_work_time_when_flag_false`

**핵심 기법**:
- `REAL_CELL_MAPPING` 상수로 `config.json`의 `excel.cell_mapping` 하드카피 — 불일치 시 D2 실패로 config 변경 감지
- `tempfile.TemporaryDirectory`로 `paths.output` 격리 (실적서 폴더 오염 방지)
- `patch("models.excel_exporter.config")` + `_cfg_side_effect`로 런타임 config 주입
- `_new_exporter()` 헬퍼에서 `template_file`을 절대 경로로 override

### 4.3 발견한 이슈 1건 (테스트 전용 보정)

**ExcelExporter.template_file 상대 경로** (excel_exporter.py:35)
- `self.template_file = os.path.join("resources", "template.xlsx")` — CWD 의존
- 실제 앱 실행 시 CWD=PROJECT_ROOT이므로 프로덕션 문제 없음
- 테스트에서는 `run_tests.py` 실행 위치에 따라 실패 가능 → `_new_exporter()` 헬퍼에서 절대 경로 override
- 프로덕션 코드 변경 불요

## 5. Metrics

| 지표 | PDCA #11 종료 | PDCA #12 종료 | 변화 |
|---|---|---|---|
| 테스트 총수 | 52 | **65** | +13 (+25%) |
| 실행 시간 | 0.669s | **1.346s** | +0.677s |
| 테스트 파일 | 6 | **8** | +2 |
| D1 Orchestration cases | 0 | 5 | +5 |
| D2 Excel Content cases | 0 | 5 | +5 |
| D3 Error Path cases | 0 | 3 | +3 |
| test LOC (이 feature) | 264 | 651 | +387 |
| 프로덕션 코드 변경 | 0 | 0 | 0 |
| Match Rate | 100% | **100%** | 유지 |

## 6. Gap Analysis Summary

| Severity | Count | 대응 |
|---|---|---|
| HIGH | 0 | N/A |
| MEDIUM | 0 | N/A |
| LOW | 4 | 전부 문서 미세 보강 권고, 기능 영향 없음 (Report §8 Lessons Learned에 기록) |

상세: `docs/03-analysis/manual_input_save_export_e2e.analysis.md`

## 7. Root Cause of Zero-Gap

PDCA #11에서 확립한 세 가지 원칙이 #12에서도 정확히 재작동:

1. **DI 기반 주입** (`dhr_db`, `lot_manager` 생성자 인자) — 프로덕션 코드 무변경 유지 가능
2. **Qt Mock 시그니처 보호** (`generate_product_lot.return_value` 명시) — PDCA #11 F-01 교훈 재적용
3. **Headless Qt** (`QT_QPA_PLATFORM=offscreen`) — CI/배치 실행 친화

Design 단계에서 `ExcelExporter` 지연 import 패치 경로 / `cell_mapping` 런타임 주입 / win32com 비의존을 사전 결정해둔 덕분에 Do 단계에서 추가 설계 변경이 없었다.

## 8. Lessons Learned

### 8.1 테스트 전용 헬퍼의 가치
`_new_exporter()`가 `template_file` 절대 경로 override를 전담하면서, 프로덕션 코드의 상대 경로 관례(한글/PyInstaller 경로 전략)를 건드리지 않고 테스트만 격리할 수 있었다. "프로덕션 코드 무변경 = 테스트 측 어댑터 활용"의 좋은 예.

### 8.2 config 리터럴 하드카피의 양방향 가치
`REAL_CELL_MAPPING`은 config.json 변경을 감지하는 **sentinel** 역할을 한다. 개발자가 실수로 `cell_mapping`의 키 이름을 바꾸면 D2가 실패하여 명시적으로 sync 작업을 강제한다. "config는 런타임 계약이므로 테스트에서도 동결"이라는 원칙.

### 8.3 Agent 파일 쓰기 재확인 (#11 교훈 재검증)
메모리 `feedback_pdca_agent_file_write.md`의 경고대로, `bkit:gap-detector`와 `bkit:report-generator` 모두 이번 사이클에서도 파일을 직접 쓰지 못했다 (Write 도구 권한 없음). 대응:
- gap-detector는 본문 텍스트를 반환 → 호출자가 Write로 직접 저장
- report-generator는 이번 사이클에서 아예 호출하지 않고 직접 작성 (속도·신뢰성 둘 다 우위)
- **다음 사이클부터는 Analysis/Report 단계에서 처음부터 직접 작성하는 것을 기본 플로우로 삼을 것**

### 8.4 Design Step 단위 커밋 분할
Design §7 "구현 순서"의 Commit #1(D1+D3)/Commit #2(D2) 분할이 그대로 적용되었다. 테스트 전용 저위험 작업이지만, 기능 단위 커밋 분할이 후속 롤백/리뷰/재구성에 유리.

### 8.5 Follow-up 권고 (optional)
- Design §2.3의 메서드명을 실제 구현명(`test_creates_file_*` prefix 없음)과 동기화 — 다음 PDCA 시작 전 1줄 수정
- Design §5.1 "공통 헤더 패턴" 예시의 `openpyxl` 의존성에 "D2 전용" 주석 덧붙이기

## 9. Next Steps

1. **Analysis + Report 문서 커밋** (예정)
   - `docs: add PDCA #12 analysis and completion report`
2. **Archive**
   - `/pdca archive manual_input_save_export_e2e`
   - 이동: `plan`, `design`, `analysis`, `report` → `v3/docs/archive/2026-04/manual_input_save_export_e2e/`
   - `_INDEX.md` 갱신 (PDCA #12 엔트리 추가)
3. **메모리 갱신**
   - `project_pdca_status.md`에 #12 결과 추가
   - 다음 후보에서 `manual_input_save_export_e2e` 제거
   - 다음 사이클 번호: **#13**

## 10. Next Cycle Candidates (PDCA #11 시점 후보 - 1개 선택 반영)

남은 후보 3개 (우선순위는 사용자 상황에 따라):

1. **`config_and_logs_observability`** — PDCA #10에서 체감된 로그 파일 접근성 이슈. `logger.py` 로테이션 정책, `config_manager.get()` deepcopy 비용, 에러 팝업에 로그 파일 경로 표시.
2. **`release_smoke_automation`** — PDCA #9 잔여. `RELEASE_SMOKE_CHECKLIST.md` 수동 항목 자동화.
3. **`dhr_bulk_generator_qa_coverage`** — PDCA #8 Commit 5(+134 LOC) `dhr_bulk_generator.py` 자체 커버리지 점검.

## 11. Archive

- 위치 (예정): `v3/docs/archive/2026-04/manual_input_save_export_e2e/`
- 생성 문서: `manual_input_save_export_e2e.plan.md`, `.design.md`, `.analysis.md`, `.report.md` (4개)
- **다음 사이클 번호: PDCA #13**
