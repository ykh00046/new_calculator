# Menu Restructure Design

> **Target**: `v3/ui/main_window.py`, `v3/ui/panels/bulk_creation_interface.py`
> **Goal**: 대시보드 완전 제거 및 기능 중심 사이드바 3단 메뉴 분리
> **Status**: Draft
> **Author**: Antigravity
> **Created**: 2026-02-04

---

## 1. Overview

본 설계는 **대시보드(현황) 제거** 및 **수기/일괄/관리 3단 메뉴 분리**를 통해 작업자 동선을 단순화하고 **One-Click Access**를 제공한다.

---

## 2. Navigation Structure

### 2.1 Sidebar Items (Final)

1. 🧪 배합 (Default)
2. ✍️ 수기 입력
3. 📑 일괄 생성
4. 🧰 DHR 관리
5. 📜 기록 조회
6. 🔧 설정 (구글 시트/PDF 포함)
7. 👤 작업자 변경

> 상단 커맨드바는 사용하지 않으며, **모든 기능 접근은 사이드바로 통합**한다.

---

## 3. Component Changes

### 3.1 Main Window (`v3/ui/main_window.py`)

**Remove**
- Dashboard page (`build_dashboard_page`) 및 관련 UI 호출

**Add / Reorder**
- `BulkCreationInterface` 메뉴 추가
- `RecordViewDialog`를 Sidebar 액션으로 이동
- `Worker` 변경을 Sidebar 액션으로 이동
- `Settings` 메뉴는 기존 유지 (Google Sheets/PDF 설정 포함)

**Expected addSubInterface order**
1. 배합 (Mixing)
2. 수기 입력 (Manual)
3. 일괄 생성 (Bulk)
4. DHR 관리
5. 기록 조회 (Dialog)
6. 설정
7. 작업자 변경 (Dialog)

### 3.2 BulkCreationInterface (`v3/ui/panels/bulk_creation_interface.py`)

이미 존재하므로 **신규 생성 없이 연결만 진행**한다.

---

## 4. Behavior

1. 앱 시작 시 **배합 탭**이 기본 화면
2. 사이드바에서 수기/일괄/DHR 관리 독립 접근 가능
3. 기록 조회는 대시보드 제거 후에도 사이드바에서 접근 가능
4. 작업자 변경은 Sidebar 액션 클릭 시 즉시 다이얼로그 호출

---

## 5. Migration Plan

1. MainWindow 메뉴 구조 변경
2. 대시보드 메뉴 제거
3. BulkCreationInterface 연결
4. 기록 조회 / 작업자 변경 사이드바 이동
5. 기능 정상 동작 확인

---

## 6. Verification Checklist

- [ ] 앱 시작 시 배합 탭 기본 표시
- [ ] 사이드바에서 수기/일괄/DHR 관리 진입 확인
- [ ] 기록 조회 사이드바 진입 확인
- [ ] 작업자 변경 사이드바 호출 확인
- [ ] 설정 메뉴 정상 동작 확인

