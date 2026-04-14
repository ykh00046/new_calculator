# DHR Bulk Generation Design

> **Summary**: 배합 대량 생성 기능 설계
>
> **Author**: AI Assistant
> **Created**: 2026-02-03
> **Last Modified**: 2026-04-14
> **Status**: Approved

---

## Architecture

- UI: `ui/panels/bulk_creation_interface.py` — 엑셀 붙여넣기(Ctrl+V) 기반 테이블 입력
- Service: `models/dhr_bulk_generator.DhrBulkGenerator` — 다건 기록 생성 로직
- Data: DHR DB(`dhr_records`, `dhr_details`), 자재 LOT 조회(OUT.xlsx)

## Data Flow

1. 사용자가 엑셀(레시피/수량) 범위를 복사해 테이블에 붙여넣는다.
2. 레시피명과 작업자, 배합량을 검증한다.
3. 작업일자 기준으로 자재 LOT를 자동 배정한다(OUT.xlsx 조회).
4. 제품 LOT 번호를 생성한다 — `{recipe}{YYMMDD}{순번 2자리}`.
5. DB에 기록을 저장하고 Excel/PDF로 내보낸다.
6. 동일 날짜 재실행 시 기존 순번 뒤에 이어서 부여한다.

## Data Model

- **dhr_records**: `product_lot`, `product_name`, `work_date`, `work_time`, `total_amount`, `worker`
- **dhr_details**: `material_code`, `material_name`, `material_lot`, `ratio`, `theory_amount`, `actual_amount`, `sequence_order`

## UI/UX

- 엑셀 범위 붙여넣기(Ctrl+V)로 다건 입력 지원
- 미리보기 테이블에서 레시피/작업자/배합량을 검증 후 일괄 저장
- 진행 상황 표시: 성공/실패/건너뜀 카운트

## Error Handling

- LOT 조회 실패 시 경고 다이얼로그 후 해당 건 스킵(다른 건은 계속 진행)
- 레시피 미존재 시 행 단위 에러 표시(파란색 하이라이트)
- 작업시간 지정이 없으면 09시 기준, 순번당 20~40초 간격으로 자동 부여

## Test Plan

- 정상/오류/부분 실패 케이스 단위 테스트
- LOT 중복/누락 회귀 테스트
- `tests/unit/test_bulk_helpers.py`의 ratio 검증 게이트

## Implementation Guide

- `models/dhr_bulk_generator.py`: 대량 생성 핵심 로직
- `ui/panels/bulk_creation_interface.py`: 붙여넣기/검증/실행 UI
- `models/dhr_database.py`: DHR LOT 순번 관리

## Related Documents

- Plan: [../01-plan/features/dhr_bulk_generation.plan.md](../../01-plan/features/dhr_bulk_generation.plan.md)
- Report: [../04-report/features/dhr_bulk_generation.report.md](../../04-report/features/dhr_bulk_generation.report.md)
