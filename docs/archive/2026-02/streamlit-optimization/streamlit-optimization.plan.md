# Plan: Streamlit Dashboard Optimization

## Feature Overview

Streamlit agent-skills 권장사항을 적용하여 Dashboard UI/UX 및 성능 최적화

## Background

Streamlit agent-skills 저장소 검토 결과, 현재 Dashboard 구현에서 개선할 수 있는 4가지 항목을 식별함:

1. KPI 스파크라인 미사용
2. 반응형 레이아웃 미적용
3. 테마를 Python CSS가 아닌 config.toml로 관리
4. Tabs 조건부 렌더링 미적용

## Goals

### Primary Goals
- KPI 카드에 스파크라인 추가로 트렌드 시각화
- 반응형 레이아웃으로 모바일 호환성 향상
- 테마 관리를 config.toml로 이관하여 유지보수성 향상

### Non-Goals
- 기존 기능 변경 없음
- API 서버 수정 없음

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| F1 | KPI 카드에 지난 7일 트렌드 스파크라인 표시 | High |
| F2 | KPI 행이 작은 화면에서 자동 줄바꿈 | High |
| F3 | 다크/라이트 모드가 config.toml 기반으로 동작 | High |
| F4 | config.toml 테마 설정 시 시스템 테마 연동 지원 | Medium |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| N1 | 기존 대시보드 로딩 속도 유지 | High |
| N2 | CSS 제거로 Streamlit 버전 호환성 향상 | Medium |

## Success Criteria

- [ ] KPI 4개에 스파크라인 표시
- [ ] `st.container(horizontal=True, border=True)` 적용
- [ ] `.streamlit/config.toml` 생성 및 테마 설정
- [ ] Python CSS 주입 코드 제거
- [ ] 다크/라이트 모드 정상 동작

## Scope

### In Scope
- `dashboard/components/kpi_cards.py` 수정
- `dashboard/components/theme.py` 단순화
- `.streamlit/config.toml` 신규 생성

### Out of Scope
- API 서버 변경
- 데이터베이스 스키마 변경
- 새로운 기능 추가

## Timeline

| Phase | Duration |
|-------|----------|
| Design | 즉시 |
| Implementation | Design 완료 후 |
| Testing | Implementation 완료 후 |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| config.toml 테마가 일부 커스텀 스타일 미지원 | Medium | 필요시 최소 CSS 유지 |
| 스파크라인 데이터 로딩 추가 오버헤드 | Low | 캐싱 활용 |

## Dependencies

- Streamlit >= 1.40 (horizontal container, sparklines 지원)
- 기존 `load_daily_summary()` 함수 활용

## References

- Streamlit agent-skills: `building-streamlit-dashboards`
- Streamlit agent-skills: `creating-streamlit-themes`
- Streamlit agent-skills: `displaying-streamlit-data`
