# Manual Input QA Coverage — Plan

> **Author**: AI Assistant
> **Created**: 2026-04-17
> **Status**: Plan
> **Cycle**: PDCA #11
> **Parent**: PDCA #8 Commit 4 (`refactor: trim manual input interface`, −135 LOC, Critical 격리 + 수동 QA만)

---

## 1. Overview & Purpose

### 1.1 배경
PDCA #8 Commit 4에서 `v3/ui/panels/manual_input_interface.py`를 DI 패턴으로 −135 LOC 리팩토링했다. 당시 위험도 Critical로 격리 커밋 + 수동 QA만 거쳤고, 자동화된 회귀 안전망이 없는 상태다.

또한 PDCA #10에서 `MainWindow` 기동 경로의 AttributeError가 **수동 QA에서도 포착되지 않은** 사례를 겪었다. 이는 수동 QA의 한계를 실증한다.

### 1.2 목적
`ManualInputInterface`(수기 배합일지 작성 패널)의 **순수 로직**과 **UI 상태 전환 로직**을 unit test로 고정하여, 향후 리팩토링·버그 수정 시 회귀를 자동 감지한다.

---

## 2. Scope

### 2.1 In-Scope
**Target module**: `v3/ui/panels/manual_input_interface.py` (474 LOC, 단일 클래스 `ManualInputInterface`)

**Target methods** (3개 레이어로 분류):

#### Layer A — Pure Logic (UI 의존 없음)
| 메서드 | 라인 | 테스트 포인트 |
|---|---|---|
| `_to_float(s: str) -> float` | 431-435 | 정상 값 / 공백 / 비숫자 / None-like |
| `worker_name` (property) | 44-46 | `config.last_worker` 정상 / `None` / 빈문자 → "Unknown" 폴백 |

#### Layer B — Table/Form Logic (QApplication 필요, 테이블·spinbox 조작)
| 메서드 | 라인 | 테스트 포인트 |
|---|---|---|
| `_is_empty_material_row(row)` | 271-272 | 빈 행 / 부분 채운 행 / 완전 채운 행 |
| `_get_effective_material_row_count()` | 274-275 | 빈 테이블 / 혼합 / 전부 빈 행 |
| `_recalc_theory()` | 277-289 | 비율·배합량 → 이론계량 재계산, 잘못된 값은 무시 |
| `_collect_data()` | 400-429 | 테이블 상태 → dict 변환 정확성 |
| `_validate()` | 291-307 | 제품명 누락 / 배합량 0 / 자재 0행 / 정상 |
| `_add_row()` / `_remove_row()` | 247-265 | 행 수 증감, 선택 없을 때 마지막 행 삭제 |
| `load_recipe(recipe_data, materials)` | 437-473 | 테이블 재구성, 제품명·배합량 세팅, 이론계량 계산 |

#### Layer C — External Dependency (Mock)
| 메서드 | 라인 | 테스트 포인트 |
|---|---|---|
| `_update_product_lot()` | 231-245 | `dhr_db.generate_product_lot` 정상 / 예외 시 폴백 (`product_name+YYMMDD`) |

### 2.2 Out-of-Scope
- `_save_and_export()` — Excel/PDF 출력은 통합 테스트 영역, `QMessageBox` 팝업 의존 → 별도 PDCA 후보
- `_open_recipe_loader()` / `_open_record_view()` — 다이얼로그 띄우기, 수동 QA 유지
- 프로덕션 코드 수정 — 테스트 추가만 허용, 테스트를 위한 리팩토링은 Out (필요시 별도 Plan)

---

## 3. Requirements

### 3.1 Functional
1. **FR-01** 신규 테스트 파일 `v3/tests/unit/test_manual_input_interface.py` 생성
2. **FR-02** Layer A/B/C 전체에서 **최소 12 test cases** (Layer A 3, Layer B 7, Layer C 2 이상)
3. **FR-03** 기존 테스트 러너(`v3/tests/run_tests.py`)가 자동 수집
4. **FR-04** `QT_QPA_PLATFORM=offscreen` 헤드리스 환경에서 통과 (`test_panels.py`와 동일 패턴)
5. **FR-05** 프로덕션 코드 **무변경** — 테스트만 추가

### 3.2 Non-Functional
- Python 3.9 호환성 (타입 힌트 `Optional`, `List` 등)
- 기존 33/33 테스트 무회귀 → 최종 **45+ tests** (33 + 12 신규)
- 테스트 실행 시간 증가 ≤ 2초
- DB 격리: `DhrDatabaseManager` 인메모리 또는 Mock 사용 (실제 DB 파일 미접근)
- LotManager 격리: `LotManager` Mock 또는 tmp 파일 사용

---

## 4. Risks

| 리스크 | 영향 | 완화 |
|---|---|---|
| `ManualInputInterface.__init__`에서 `DhrDatabaseManager()` 기본 인스턴스화 → 테스트 시 실제 DB 파일 접근 | Medium | DI 인자(`dhr_db=Mock()`, `lot_manager=Mock()`)로 주입 — 이미 생성자가 받음, 활용 가능 |
| UI 의존 테스트가 CI/headless에서 플레이키 | Low | `test_panels.py`의 `_ensure_ui_test_dependencies` 패턴 재사용 |
| `config.last_worker` 전역 상태 누수 | Low | `patch('ui.panels.manual_input_interface.config')` 모킹 |
| `QMessageBox.warning`을 호출하는 `_validate` 테스트 시 다이얼로그 차단 | Medium | `patch('ui.panels.manual_input_interface.QMessageBox')` 로 팝업 차단 |
| Excel/PDF export 모듈 import가 테스트 시 필요 | Low | `_save_and_export` 테스트 제외, import 경로 영향 없음 |

---

## 5. Plan Steps

1. **Design** — 테스트 아키텍처 (픽스처 공유 전략, Mock 전략, 파일 구조) 문서화
2. **Do** — `test_manual_input_interface.py` 구현 (Layer A → B → C 순)
3. **Do** — 헤드리스 테스트 실행 (`QT_QPA_PLATFORM=offscreen python v3/tests/run_tests.py`)
4. **Analyze** — 신규 테스트 12+ cases 커버리지 매칭, 기존 33/33 무회귀 확인
5. **Report** — 완료 보고서 + 회고 (+ 다음 후보로 `_save_and_export` E2E 검토)

---

## 6. Success Criteria (DoD)

- [ ] `v3/tests/unit/test_manual_input_interface.py` 파일 존재
- [ ] 테스트 통과: 45+ cases (기존 33 + 신규 12+)
- [ ] 프로덕션 코드 `git diff` 기준 변경 없음 (`manual_input_interface.py` 무수정)
- [ ] 실제 DB 파일 생성/접근 없음 (Mock 검증: `dhr_db.generate_product_lot.assert_called_with(...)`)
- [ ] 문서 4종 생성: plan / design / analysis / report
- [ ] Match Rate ≥ 90%

---

## 7. Estimation

| 단계 | 예상 소요 |
|---|---|
| Design | 10분 (테스트 파일 골격 + 픽스처 설계) |
| Do (테스트 구현) | 30~45분 (12+ cases) |
| Do (헤드리스 실행/디버깅) | 10분 |
| Analyze + Report | 15분 |
| **합계** | **~1~1.5시간 (1 세션)** |

---

## 8. Commit 계획 (Do 단계)

단일 커밋 예상 (테스트 추가, 저위험):
- `test: add unit tests for ManualInputInterface pure logic and UI state transitions`

만약 Layer C에서 Mock 정교화가 커지면 커밋 분할 고려:
- Commit 1: `test: add pure logic tests for ManualInputInterface` (Layer A+B)
- Commit 2: `test: add db-mocked tests for ManualInputInterface LOT generation` (Layer C)

위험도: **Low** (신규 파일만, 프로덕션 코드 무변경) → 메모리 규칙상 **일괄 진행 모드** 적용 가능.
