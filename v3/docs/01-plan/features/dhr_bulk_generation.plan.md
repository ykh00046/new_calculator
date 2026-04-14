# DHR Bulk Generation Plan

> **Summary**: 엑셀 붙여넣기 기반 DHR 일괄 생성 기능 계획
>
> **Author**: AI Assistant
> **Created**: 2026-02-03
> **Last Modified**: 2026-04-14
> **Status**: Approved

---

## Overview & Purpose

- 현장 작업자가 엑셀에서 복사한 배합 목록을 DHR 시스템에 일괄 등록할 수 있도록 한다.
- 수기 입력의 반복 작업을 줄이고, 동일 날짜의 다건 기록 입력 시간을 단축한다.

## Scope

- **In Scope**
  - 엑셀 범위 붙여넣기(Ctrl+V) 입력 지원
  - 레시피/작업자 존재 여부 검증
  - 자재 LOT 자동 조회/배정(OUT.xlsx 참조) 및 저장
  - 제품 LOT 순번 자동 부여(01/02/03 …)
  - 부분 실패 허용(실패 건만 스킵)
- **Out of Scope**
  - 수기 입력 단건 흐름(별도 패널)
  - 배합 레시피 관리 자체

## Requirements

### Functional

- 레시피/작업자 필수 검증
- 자재 LOT 조회 실패 시 경고 표시
- DHR LOT 순번 자동 관리
- 작업시간 자동 부여: 기본 09시+순번 20~40초 간격

### Non-Functional

- 대량 입력 시(수십 건) 응답성 유지
- 기존 DHR 수기 저장 로직과 동일한 데이터 정합성 보장

## Success Criteria

- 다건 입력 후 저장 시 LOT 01/02/03 순번 자동 부여
- 동일 날짜 재실행 시 기존 순번 이어 증가
- LOT 조회 실패 건은 스킵 후 나머지 계속 저장

## Risks & Mitigation

- **엑셀 포맷 불일치 시 파싱 실패**
  - 대응: 행 단위 에러 표시, 부분 실패 허용
- **LOT 조회용 OUT.xlsx 누락**
  - 대응: 경고 다이얼로그 표시 후 건너뜀

## Related Documents

- Design: [../../02-design/features/dhr_bulk_generation.design.md](../../02-design/features/dhr_bulk_generation.design.md)
- Report: [../../04-report/features/dhr_bulk_generation.report.md](../../04-report/features/dhr_bulk_generation.report.md)
