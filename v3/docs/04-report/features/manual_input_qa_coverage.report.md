# PDCA #11 완료 보고서 — manual_input_qa_coverage

> **Author**: AI Assistant
> **Created**: 2026-04-17
> **Cycle**: PDCA #11
> **Status**: Completed (Match Rate 100%)
> **Feature**: ManualInputInterface QA 커버리지 보강

---

## 1. Overview

PDCA #8 Commit 4(`refactor: trim manual input interface`, −135 LOC Critical 리팩토링)는 수동 QA만 거친 상태로 아카이브됐다. PDCA #10에서 수동 QA의 한계가 실증된 이후, 이 파일의 핵심 로직을 자동화된 안전망으로 덮는 것이 목표였다.

결과: **19 cases 신규 추가, 전체 52/52 pass, 프로덕션 코드 무변경, DB 파일 미접근**. Match Rate 100%.

---

## 2. Goals vs Results

| 목표 | 결과 |
|---|---|
| 신규 테스트 파일 생성 | ✅ `v3/tests/unit/test_manual_input_interface.py` (264 LOC) |
| 최소 12 cases (Layer A/B/C 혼합) | ✅ **19 cases** (A=5, B=12, C=2) |
| 프로덕션 코드 무변경 | ✅ `manual_input_interface.py` 미변경, DI 활용 |
| 기존 33/33 무회귀 | ✅ 52/52 pass |
| 실행 시간 증가 ≤ 2초 | ✅ 0.669초 (전체 스위트) |
| 실제 DB/파일 미접근 | ✅ MagicMock 주입 |
| Match Rate ≥ 90% | ✅ **100%** |
| 문서 4종 생성 | ✅ plan / design / analysis / report |

---

## 3. Commit Log

| # | Commit | SHA |
|---|---|---|
| 1 | test: add unit tests for ManualInputInterface | `0ccd9d2` |
| 2 | docs: add PDCA #11 plan and design for manual_input_qa_coverage | `55375a1` |
| 3 | docs: add PDCA #11 analysis and completion report | (이 커밋) |

---

## 4. Key Changes

### 4.1 `v3/tests/unit/test_manual_input_interface.py` (신규, 264 LOC)

8개 TestCase 클래스, 19 cases:

| TestCase | Cases | 대상 |
|---|---|---|
| `TestToFloat` | 3 | `_to_float` 정상/공백/비숫자 |
| `TestWorkerName` | 2 | `worker_name` 프로퍼티, `config.last_worker` 폴백 |
| `TestTableHelpers` | 3 | `_is_empty_material_row`, `_get_effective_material_row_count` |
| `TestValidate` | 4 | `_validate` 3가지 실패 + 1 성공 (QMessageBox 패치) |
| `TestRecalcAndCollect` | 2 | `_recalc_theory`, `_collect_data` 구조 |
| `TestRowOps` | 2 | `_add_row`, `_remove_row` (선택 없을 때 마지막 행 삭제) |
| `TestLoadRecipe` | 1 | `load_recipe` 테이블 재구성 + 이론계량 |
| `TestUpdateProductLot` | 2 | `_update_product_lot` DB 성공/예외 폴백 |

### 4.2 헬퍼 유틸
- `_make_panel(dhr_db, lot_manager)` — Mock 주입 + `generate_product_lot.return_value=""` 기본값으로 Qt TypeError 노이즈 차단
- `_fill_row(panel, row, values)` — 테이블 셀 채우기 (QTableWidgetItem 생성 포함)

### 4.3 프로덕션 코드
**변경 없음**. `ManualInputInterface.__init__(self, parent=None, dhr_db=None, lot_manager=None)`에 이미 DI 여지가 있어 테스트 측에서 활용만 했다.

---

## 5. Metrics

| 지표 | 값 |
|---|---|
| 커밋 수 | 2 (구현 + 문서) + 1 (본 리포트 커밋) |
| 신규 파일 | 1 (테스트) + 3 (문서) |
| 수정 파일 | 0 (프로덕션) |
| 추가 LOC | 264 (테스트) + 298 (plan/design 문서) + ~200 (analysis/report) |
| 테스트 | 33 → **52** (+19, +57.6%) |
| 실행 시간 | 0.669초 (전체) |
| Match Rate | **100%** |
| 작업 시간 | 1 세션 (~1시간) |
| 사용자 승인 모드 | 일괄 진행 (저위험, 프로덕션 무변경) |

---

## 6. Risks Mitigated

| 리스크 (Plan) | 대응 결과 |
|---|---|
| 테스트 시 실제 DB 파일 접근 | ✅ `MagicMock` 주입으로 `DhrDatabaseManager()` 미인스턴스화 확인 |
| UI 테스트 플레이키 | ✅ `test_panels.py`의 `_ensure_ui_test_dependencies` 패턴 재사용, 0 flake |
| `config.last_worker` 전역 상태 누수 | ✅ `patch('ui.panels.manual_input_interface.config')` 사용 |
| QMessageBox 팝업이 테스트 차단 | ✅ `patch('...QMessageBox')` 적용, 4 cases 모두 통과 |

---

## 7. Findings (Analyze 단계 발견)

### F-01: MagicMock 기본 `return_value`가 Qt 시그니처를 깸
`dhr_db.generate_product_lot()`의 반환값 기본 MagicMock이 `QLineEdit.setText(str)` 시그니처와 충돌 → stderr에 TypeError traceback 출력(테스트 결과는 pass). Do 단계에서 `_make_panel`에 `return_value = ""` 기본값 추가로 해결.

**교훈**: Qt 기반 UI 테스트에서 MagicMock을 쓸 때는 **Qt 시그니처가 요구하는 타입(str, int, bool 등)을 명시적으로 반환하도록 기본값을 설정**하는 것이 표준 관례가 되어야 한다.

---

## 8. Lessons Learned

1. **생성자 DI는 테스트 가능성의 지름길**
   - PDCA #8 Commit 4에서 `dhr_db=None, lot_manager=None` 인자를 넣어둔 선택이 이번 PDCA의 프로덕션 무변경 원칙을 가능하게 했다.
   - 교훈: 외부 의존성을 갖는 UI 컨트롤러는 생성자에서 **Optional DI** 인자를 받는 설계를 기본값으로.

2. **Qt Mock 주입 시 기본 반환값 명시**
   - F-01이 보여주듯 MagicMock의 기본 반환값(MagicMock 자체)은 Qt C++ 바인딩에서 런타임 에러를 일으킨다.
   - 교훈: 테스트 헬퍼에서 "Qt가 요구하는 타입"을 return_value로 사전 세팅.

3. **19 cases는 `manual_input_interface.py` 전체 커버리지가 아님**
   - `_save_and_export` (Excel/PDF 통합)는 의도적으로 제외. 단위 테스트가 아닌 통합/E2E 영역.
   - 교훈: 커버리지 목표는 "파일 100%"가 아니라 "**리팩토링 시 회귀를 감지하는 경로**"에 집중.

4. **메모리 기반 Critical 이력 관리의 가치**
   - PDCA #8의 `manual_input_interface.py` −135 LOC가 메모리 `project_pdca_status.md`에 Critical로 기록되어 있었기에 이번 후보 1번으로 자동 우선순위화 가능.
   - 교훈: 메모리의 "follow-up/후보" 섹션은 단순 메모가 아니라 **PDCA 스케줄러**의 역할.

---

## 9. Follow-ups

1. **`_save_and_export` E2E 테스트** — 후속 PDCA 후보. Excel/PDF 생성 → 파일 존재 검증 수준의 통합 테스트. 난이도 Medium-Large.
2. **`config` 전역 상태 패치 패턴 통일** — 현재 `test_manual_input_interface`와 `test_panels`의 `config` 모킹 방식이 조금 다름. 테스트 헬퍼 모듈 분리 검토 가치 있음.
3. **다른 Critical 리팩토링 파일의 QA 커버리지 스캔** — `dhr_bulk_generator.py` (+134 LOC, PDCA #8 Commit 5)도 `test_bulk_helpers.py`가 있지만 커버리지 점검 권장.

---

## 10. 결론

**PDCA #11 manual_input_qa_coverage는 100% Match Rate로 완료되었습니다.**

- ✅ PDCA #8 Critical 커밋의 **자동화 안전망 확보**
- ✅ 프로덕션 코드 무변경 원칙 준수
- ✅ 33 → 52 tests (+57.6%), 실행 시간 유지(0.669초)
- ✅ Qt Mock 주입의 표준 패턴 학습 + 문서화 (F-01)

다음 PDCA는 **#12**. 후보는 `config_and_logs_observability` 또는 `release_smoke_automation` 또는 본 리포트 Follow-up의 `_save_and_export_e2e`.

---

## Archive

- 위치: 완료 후 `v3/docs/archive/2026-04/manual_input_qa_coverage/` 로 이동 예정
- 생성 문서: plan / design / analysis / report (4종 모두)
- 다음 사이클 번호: **PDCA #12**
