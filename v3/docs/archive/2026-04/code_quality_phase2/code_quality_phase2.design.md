# Code Quality Phase 2 — Design

> **Author**: AI Assistant
> **Created**: 2026-04-15
> **Status**: Design
> **Parent Plan**: `v3/docs/01-plan/features/code_quality_phase2.plan.md`

---

## 1. Goals

작업 트리의 미커밋 변경을 **검토 → 분할 커밋 → 쓰레기 제거** 순으로 정리하여 baseline을 깨끗하게 만든다. 변경 총량은 **+761 / −748 (net +13)** — 코드 간소화 성격이 강하다.

---

## 2. 변경 분석 요약

### 2.1 Python 핵심 변경 (net −119 LOC, 간소화 우세)

| 파일 | +/− | 성격 판단 | 우선순위 |
|---|---|---|---|
| `utils/error_handler.py` | +182/−? (net −) | 에러 처리 경로 단순화 | **High** (쌍으로 검토) |
| `utils/logger.py` | +136/−? (net −) | 로깅 구조 리팩토링 | **High** (쌍으로 검토) |
| `models/dhr_bulk_generator.py` | +134/−? | 기능 확장 + 리팩토링 | High |
| `ui/panels/manual_input_interface.py` | +273/−? (net **−135**) | **대규모 축소** — 로직 추출 가능성 | **Critical** |

### 2.2 기타 Python (net 대략 −10)
- `models/dhr_database.py` (+85), `config/config_manager.py` (+19)
- `utils/bulk_helpers.py` (+9)
- `ui/panels/bulk_creation_interface.py` (+51), `recipe_management_interface.py` (+4)
- `ui/panels/scan_effects_panel.py` (+10), `signature_panel.py` (+8)

### 2.3 테스트
- `tests/run_tests.py` (+28), `tests/unit/test_panels.py` (+27)
- `tests/unit/test_bulk_helpers.py` (신규, 미추적)

### 2.4 빌드/배포
- `v3/build.py` (+10), `v3/deploy.py` (+11), `run.bat` (+6)
- 신규: `v3/check_release_artifacts.py`, `DEPLOY_GUIDE.md`, `RELEASE_SMOKE_CHECKLIST.md`, `run_dev.bat`

### 2.5 문서
- `README.md` (+64), `v3/docs/SETUP.md` (+150, 대규모 보강)
- `v3/docs/README.md` (net −170, 요약/압축 작업)
- `v3/docs/REPORT.md`, `v3/docs/04-report/v3_completion.report.md`

### 2.6 루트 미추적 디렉터리 정체 확인

| 경로 | 내용 | 판단 |
|---|---|---|
| `.agents/skills/` | 로컬 에이전트 설정 | `.gitignore` 추가 |
| `skills/pyside6-ui-architecture-review/` | 로컬 스킬 캐시 | `.gitignore` 추가 |
| `docs/.bkit-memory.json`, `.pdca-status.json`, `.pdca-snapshots/`, `04-report/` | **bkit PDCA 상태 데이터** (삭제 금지!) | `.gitignore`에 `docs/` 추가 — 프로젝트 문서는 `v3/docs/`로 분리됨 |

### 2.7 임시 파일 (제거)
- `.tmp_agentskillsindex_1836.html`
- `.tmp_lorairo_qt_widget.html`, `.tmp_lorairo_qt_widget_skill.md`
- `.tmp_pyside6_mvc_SKILL.md`
- `.tmp_qt_architecture_SKILL.md`, `.tmp_qt_testing.html`, `.tmp_qt_testing_skill.md`
- `.tmp_skillsmp_pyside6_json.txt`

---

## 3. 커밋 분할 전략

**순서 원칙**: 낮은 위험 → 높은 위험 → 독립 기능 → 문서 → 환경 설정.

### Commit 1: `chore: remove tmp scratch files`
- `.tmp_*` 9개 파일 삭제
- 영향: 없음 (추적되지 않은 쓰레기)
- **검증**: 없음

### Commit 2: `chore: ignore local bkit state and agent caches`
- `.gitignore`에 추가:
  ```
  .agents/
  skills/
  docs/
  ```
- 이유: 루트 `docs/`는 bkit 런타임 상태 (`.bkit-memory.json` 등) — 프로젝트 문서는 `v3/docs/`
- **검증**: `git status` 후 해당 항목 사라짐

### Commit 3: `refactor: simplify error handler and logger`
- `v3/utils/error_handler.py`, `v3/utils/logger.py`
- 쌍으로 묶음 (로깅 호출 경로 상호 의존)
- **검증**: `python v3/tests/run_tests.py` (27/27), 앱 실행 후 에러 한 건 트리거해 로그 형식 확인

### Commit 4: `refactor: trim manual input interface`
- `v3/ui/panels/manual_input_interface.py` (−135 LOC)
- **Critical 위험도** — 단독 커밋
- **사전 점검**:
  1. diff 전체를 Read로 읽기
  2. 추출된 헬퍼가 `bulk_helpers.py`나 다른 모듈로 이동했는지 확인
  3. signal/slot 연결 누락 여부 검토
- **검증**: 수기 입력 탭 수동 QA (레시피 로드 → 자재 추가 → 저장)

### Commit 5: `feat: expand dhr bulk generator and database`
- `v3/models/dhr_bulk_generator.py`, `v3/models/dhr_database.py`
- `v3/utils/bulk_helpers.py`, `v3/config/config_manager.py` 동반
- **검증**: `test_bulk_helpers.py` 신규 테스트 포함 실행, 일괄 생성 탭 수동 QA

### Commit 6: `refactor: minor panel cleanups`
- `bulk_creation_interface.py`, `recipe_management_interface.py`
- `scan_effects_panel.py`, `signature_panel.py`
- **검증**: DHR 설정 3-way sync 동작 확인

### Commit 7: `test: add bulk helpers unit test and update suite`
- `tests/run_tests.py`, `tests/unit/test_panels.py`, `tests/unit/test_bulk_helpers.py` (신규 추적)
- **검증**: 27/27 + 신규 테스트 pass

### Commit 8: `build: add release artifact checker and deploy guide`
- `v3/check_release_artifacts.py` (신규)
- `DEPLOY_GUIDE.md`, `RELEASE_SMOKE_CHECKLIST.md`, `run_dev.bat` (신규)
- `v3/build.py`, `v3/deploy.py`, `run.bat` (수정)
- **검증**: `python v3/check_release_artifacts.py` 정상 실행

### Commit 9: `docs: update setup and completion reports`
- `README.md`, `v3/docs/README.md`, `v3/docs/SETUP.md`, `v3/docs/REPORT.md`
- `v3/docs/04-report/v3_completion.report.md`
- **검증**: 링크 유효성 확인 (아카이브된 문서 참조 없는지)

---

## 4. 파일별 검토 체크리스트

### 4.1 각 파일에 공통 적용
- [ ] diff 전체를 Read로 읽기
- [ ] 변경 의도를 한 줄로 메모 (커밋 메시지 재료)
- [ ] Python 3.9 호환성 (`|` 유니온, `typing` 사용) 확인
- [ ] 예외 처리 기본값 (`.get()`) 사용 확인
- [ ] 미사용 import 확인

### 4.2 Critical — `manual_input_interface.py` 전용
- [ ] 273 LOC 감축의 근거 (추출? 삭제? 단순화?)
- [ ] DHR 3-way sync 연결점(`scan_effects_panel`, `signature_panel`) 건재 확인
- [ ] 자재 테이블 컴포넌트 의존성 유지 확인
- [ ] 신호 연결 (signal/slot) 누락 여부 — 특히 저장 버튼, LOT 자동 배정
- [ ] **수동 QA 필수**: 수기 입력 탭 전체 워크플로우

### 4.3 High — `error_handler.py` + `logger.py`
- [ ] 로깅 레벨 체계 (DEBUG/INFO/WARNING/ERROR/CRITICAL) 일관성
- [ ] `logger.log_error_with_context` 시그니처 변경 여부 (MainWindow에서 사용 중)
- [ ] 파일 로테이션 정책 (있다면) 보존
- [ ] f-string 포맷 유지

### 4.4 High — `dhr_bulk_generator.py` + `dhr_database.py`
- [ ] 트랜잭션 경계 확인
- [ ] LOT 생성 알고리즘 회귀 없음
- [ ] `test_bulk_helpers.py` 신규 커버리지 확인

---

## 5. 검증 전략

### 5.1 자동 검증
- **커밋 후 매번**: `python v3/tests/run_tests.py` (27개 이상 pass)
- **최종**: `python v3/check_release_artifacts.py`

### 5.2 수동 QA (Commit 4, 5 후 필수)
1. 앱 실행 (`run_dev.bat` 또는 `run.bat`)
2. 배합 탭: 레시피 선택 → 자재 추가 → 저장
3. 수기 입력 탭: 전체 워크플로우
4. 일괄 생성 탭: 엑셀 붙여넣기 → 생성 실행
5. DHR 관리: 레시피 CRUD
6. 설정 탭: 스캔 효과/서명 옵션 — 3-way sync 확인
7. 기록 조회 → PDF 출력 1건

### 5.3 회귀 방지 체크포인트
- MainWindow 291 LOC 유지 (현재 완성 상태)
- PDCA #7 DHR 3-way sync 동작
- Table edit auto-save 동작

---

## 6. 위험 관리

| 위험 | 가능성 | 영향 | 대응 |
|---|---|---|---|
| `manual_input_interface.py`가 사실상 광범위한 리팩토링 | 높음 | 기능 파손 | diff 전체 이해 후 커밋, 수동 QA 필수 |
| `logger.py` 시그니처 변경으로 전체 콜 사이트 영향 | 중 | import/call error | grep으로 사용처 전수 확인 |
| `error_handler.py` 예외 형식 변경으로 UI 알림 깨짐 | 중 | 사용자 경험 저하 | `notifications.py` 통합 지점 점검 |
| `.gitignore`로 `docs/` 무시 설정 시 기존 PDCA 상태 파일이 여전히 추적 상태일 위험 | 낮음 | git 노이즈 | `git rm --cached`는 **하지 않음** (현재 추적 안 됨 확인됨) |

---

## 7. Definition of Done (Design 관점)

- [ ] 커밋 분할 전략 9개 단계 합의됨
- [ ] 각 커밋마다 검증 방법 명시됨
- [ ] `manual_input_interface.py` 리스크 완화책 마련됨
- [ ] `docs/`가 bkit 상태 디렉터리임을 문서화 (이 design 문서에서)
- [ ] 다음 단계: `/pdca do code_quality_phase2`

---

## 8. Implementation Order (Do 단계 요약)

```
1. Inspect manual_input_interface.py diff (Critical)
2. Commit 1 (tmp files) + Commit 2 (.gitignore)
3. Commit 3 (logger/error_handler)  → test
4. Commit 4 (manual_input)          → test + manual QA
5. Commit 5 (dhr bulk + helpers)    → test + manual QA
6. Commit 6 (minor panels)          → test
7. Commit 7 (tests)                 → test
8. Commit 8 (build/deploy)          → artifact check
9. Commit 9 (docs)                  → link check
10. Final git status == clean
```
