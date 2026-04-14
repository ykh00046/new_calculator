# Code Quality Phase 2 — Plan

> **Author**: AI Assistant
> **Created**: 2026-04-15
> **Status**: Plan
> **Parent**: PDCA #7 completion (working tree hygiene)

---

## 1. Overview & Purpose

### 1.1 배경
PDCA #7 (MainWindow LOC 감축) 완료 직후, 세션 시작 이전부터 누적된 **21개 수정 파일 + 10개 신규 파일**이 작업 트리에 미커밋 상태로 남아 있다. 내용이 검증·정리되지 않은 채 새 사이클을 시작하면 회귀 위험과 변경 의도 추적이 어려워진다.

### 1.2 목적
작업 트리를 **의미 단위로 분할 커밋**하고, 재사용 불가능한 쓰레기 파일을 제거하여 후속 PDCA 사이클이 깨끗한 baseline에서 시작되도록 한다.

---

## 2. Scope

### 2.1 In-Scope

**분류 A — 검증 후 커밋 (Python 코어)**
- `v3/models/dhr_bulk_generator.py` (+134/-?), `v3/models/dhr_database.py` (+85/-?)
- `v3/utils/error_handler.py` (+182/-?), `v3/utils/logger.py` (+136/-?)
- `v3/utils/bulk_helpers.py` (+9/-?)
- `v3/config/config_manager.py` (+19/-?)
- `v3/ui/panels/bulk_creation_interface.py` (+51/-?)
- `v3/ui/panels/manual_input_interface.py` (+273/-?) ← 변경량 최대, 주의
- `v3/ui/panels/recipe_management_interface.py`, `scan_effects_panel.py`, `signature_panel.py`

**분류 B — 테스트**
- `v3/tests/run_tests.py` (수정)
- `v3/tests/unit/test_panels.py` (수정)
- `v3/tests/unit/test_bulk_helpers.py` (신규, 추적 필요)

**분류 C — 빌드/배포**
- `v3/build.py`, `v3/deploy.py`, `run.bat`
- `v3/check_release_artifacts.py` (신규)
- `DEPLOY_GUIDE.md`, `RELEASE_SMOKE_CHECKLIST.md`, `run_dev.bat` (신규)

**분류 D — 문서**
- `README.md`, `v3/docs/README.md`, `v3/docs/REPORT.md`, `v3/docs/SETUP.md`
- `v3/docs/04-report/v3_completion.report.md`

**분류 E — 제거 대상 (임시/쓰레기)**
- `.tmp_agentskillsindex_1836.html`, `.tmp_lorairo_*`, `.tmp_pyside6_mvc_SKILL.md`
- `.tmp_qt_*`, `.tmp_skillsmp_pyside6_json.txt` (9개)
- `.agents/`, `skills/`, `docs/` (루트, 내용 확인 필요)

### 2.2 Out-of-Scope
- 신규 기능 추가 — 기존 변경 검증만 수행
- 리팩토링 — 현재 상태 그대로 커밋 (변경 의도 이해 후)
- 아직 시작하지 않은 개선 (성능/DB 최적화 등)

---

## 3. Requirements

### 3.1 Functional
1. **변경 의도 식별**: 각 수정 파일의 diff를 읽고 "왜 바뀌었는가"를 한 줄로 기록
2. **기능 회귀 테스트**: `python v3/tests/run_tests.py` 27/27 통과 유지
3. **의미 단위 분할 커밋**: 관련 변경을 묶어 3~7개 커밋으로 분할
4. **쓰레기 제거**: `.tmp_*` 파일 전부 삭제
5. **신규 파일 분류**: 유지할 파일은 추적, 나머지는 삭제 또는 gitignore

### 3.2 Non-Functional
- 기존 기능 무회귀 (테스트 + 수동 QA 1회)
- 커밋 메시지 한글/영문 일관성 유지 (현 프로젝트 컨벤션: 영문 `docs:`, `fix:`, `refactor:` 등)
- Python 3.9 호환성 유지 (`typing.Optional`, `|` 유니온 금지)

---

## 4. Risks

| 리스크 | 영향 | 완화 |
|---|---|---|
| 변경 의도를 파악하지 못한 채 커밋 | 회귀 디버깅 곤란 | 각 파일 diff 검토 후 커밋, 불명확하면 사용자에게 확인 |
| `manual_input_interface.py` 273 LOC 변경 — 대규모 리팩토링 가능성 | 큰 기능 손상 가능 | 단독 커밋으로 분리, 수동 테스트 선행 |
| `error_handler.py`, `logger.py`가 동시 수정 | 에러 처리 경로 전반에 영향 | 쌍으로 묶어 커밋, 테스트 후 push |
| 루트 `docs/`, `.agents/`, `skills/` 디렉터리 정체 불명 | 의도치 않은 삭제 위험 | 내용 확인 후 `v3/docs/`와의 중복 여부 판단 |

---

## 5. Definition of Done

- [ ] 작업 트리 `git status`가 "nothing to commit" 상태
- [ ] 27/27 테스트 통과
- [ ] 각 커밋이 의미 단위로 분리되어 `git log`로 변경 의도 파악 가능
- [ ] `.tmp_*` 파일 0개
- [ ] `_INDEX.md`에서 참조 끊긴 문서 없음
- [ ] 완료 보고서: `docs/04-report/features/code_quality_phase2.report.md`

---

## 6. Next Step

`/pdca design code_quality_phase2` — 커밋 분할 전략과 파일별 검토 순서를 설계한다.
