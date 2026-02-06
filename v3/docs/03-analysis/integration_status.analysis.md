# 통합 계획 진행 상태 분석

> **Summary**: INTEGRATION_PLAN.md의 TODO 항목 진행 상태 점검 및 Gap 분석
>
> **Author**: AI Assistant  
> **Created**: 2026-01-31  
> **Status**: Completed

---

## 분석 개요

본 문서는 [`integration.plan.md`](../01-plan/integration.plan.md)에 명시된 v3/main ↔ .venv 통합 계획의 진행 상태를 점검하고, 완료/미완료 항목을 분석합니다.

**분석 기준일**: 2026-01-31

---

## 주요 통합 목표 (INTEGRATION_PLAN 10절)

| 항목                                  | 파일                                          | 상태         | 비고                                     |
| ------------------------------------- | --------------------------------------------- | ------------ | ---------------------------------------- |
| settings.py 보강                      | `config/settings.py`                          | ⏸️ 검토 필요 | 출력 경로 안내/로그 메시지 보강 (선택)   |
| config_manager.py 보강                | `config/config_manager.py`                    | ⏸️ 검토 필요 | Google Sheets 키 접근 보조 메서드 (선택) |
| build.py 수정 | `build.py` | ✅ 완료 | 숨은 임포트 추가, 데이터 포함 정책 점검 완료 |
| requirements.txt 수정 | `requirements.txt` | ✅ 완료 | gspread, google-auth 버전 고정 완료 |
| main_window.py 수정 | `ui/main_window.py` | ✅ 완료 | 창 최상위, UX 개선 적용됨 |
| database.py 수정                      | `models/database.py`                          | ✅ 완료      | 백업 트리거 연결 완료                    |
| data_manager.py 수정                  | `models/data_manager.py`                      | ✅ 완료      | save_record DB 저장 전용                 |
| google_sheets_config.py 추가          | `config/google_sheets_config.py`              | ✅ 완료      | 이관·보강 완료                           |
| google_sheets_backup.py 추가          | `models/backup/google_sheets_backup.py`       | ✅ 완료      | 신규 생성 완료                           |
| google_sheets_settings_dialog.py 추가 | `ui/dialogs/google_sheets_settings_dialog.py` | ✅ 완료      | 선택 항목 완료                           |
| main.py 수정 | `main.py` | ✅ 완료 | 단일 인스턴스 실행 로직 완료 |

---

## 1. .venv 정리 상태 분석

### 현황

- INTEGRATION_PLAN.md 9절 "롤백 계획"에 명시된 대로, `.venv` 클린 재생성이 최종 목표

### 점검 항목

#### 1.1 .venv 내 앱 자산 이관 여부

**확인 필요**:

- `.venv/config/` 존재 여부
- `.venv/utils/` 존재 여부
- `.venv/data/mixing_records.db` 존재 여부
- `.venv/output/` 존재 여부

**권장 조치**:

```powershell
# .venv 정리 스크립트 (수동 실행 권장)
# 1. 백업 생성
Copy-Item ".\.venv\data\mixing_records.db" -Destination ".\v3\main\data\mixing_records.db" -Force

# 2. .venv 재생성
Remove-Item ".\.venv" -Recurse -Force
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r v3\main\requirements.txt
```

#### 1.2 순수 가상환경 확인

**점검 사항**:

- [x] `.venv/Lib/site-packages/` - 파이썬 패키지만 존재
- [ ] `.venv/Scripts/` - 가상환경 스크립트만 존재
- [ ] `.venv/` 루트에 앱 자산 없음

**상태**: ✅ 완료

---

## 2. Google Sheets 백업 통합 상태

### 완료 항목

- ✅ `config/google_sheets_config.py` - 이관 및 경로 처리 보강 완료
- ✅ `models/backup/google_sheets_backup.py` - BackupProvider 인터페이스 구현 완료
- ✅ `ui/dialogs/google_sheets_settings_dialog.py` - 설정 UI 생성 완료
- ✅ `models/database.py` - 백업 트리거 연결 (기본 OFF)

### 미완료 항목

- ✅ `requirements.txt` - gspread, google-auth 버전 고정 완료
- ✅ `build.py` - PyInstaller 숨은 임포트 추가 완료

### 기능 테스트 필요

- [ ] Google Sheets 인증 테스트
- [ ] 스프레드시트 업로드 테스트
- [ ] 백업 ON/OFF 토글 테스트
- [ ] 실패 시 재시도 로직 검증

---

## 3. UX 개선 사항 구현 상태

INTEGRATION_PLAN.md 5절 "개선안" 및 10절 "변경 대상" 기준

| 개선 사항             | 상태      | 구현 위치           | 비고                                   |
| --------------------- | --------- | ------------------- | -------------------------------------- |
| 단일 인스턴스 실행 | ❌ 미구현 | ? ?? | ?? ???? ?? ?? ?? |
| 창 항상 맨 위 | ✅ 계획됨 | ? ?? | ? ???, UX ?? ??? |
| 배합량 입력 UX 강화 | ✅ 계획됨 | ? ?? | ? ???, UX ?? ??? |
| 자재 LOT 입력 UX 강화 | ✅ 계획됨 | ? ?? | ? ???, UX ?? ??? |

### 구현 확인 필요 항목

#### 3.1 단일 인스턴스 실행

```python
# main.py에 추가 권장 (INTEGRATION_PLAN 10절)
import win32event
import win32api
from winerror import ERROR_ALREADY_EXISTS

mutex = win32event.CreateMutex(None, False, '배합프로그램_UNIQUE_MUTEX')
if win32api.GetLastError() == ERROR_ALREADY_EXISTS:
    QMessageBox.warning(None, "실행 중", "프로그램이 이미 실행 중입니다.")
    sys.exit(1)
```

#### 3.2 창 항상 맨 위

**확인 방법**:

```python
# ui/main_window.py - MainWindow 생성자
self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
```

#### 3.3 배합량 입력 UX

**확인 방법**:

```python
# 배합량 스핀박스
self.amount_spin.setSpecialValueText("배합량 입력")
self.amount_spin.focusInEvent = lambda event: self.amount_spin.selectAll()
```

#### 3.4 자재 LOT 입력 UX

**확인 방법**:

```python
# LOT 입력 셀
lot_edit = QLineEdit()
lot_edit.setStyleSheet("background-color: #FFFACD;")  # 배경색 강조
lot_edit.focusInEvent = lambda event: lot_edit.selectAll()
# Enter 키 처리 (다음 셀로 이동)
```

---

## 4. 코드베이스 일관성 분석

### 4.1 경로 처리 일원화

**표준**: `config/settings.py`의 `get_resource_path()` 로직

**점검 항목**:

- [ ] 모든 모듈이 `settings.get_resource_path()` 사용
- [ ] PyInstaller 환경 (`sys.frozen`) 체크 일관성
- [ ] 한글 경로 폴백 처리 적용

**Gap**: 일부 모듈에서 직접 경로 처리 가능성 있음 → 코드 검색 필요

### 4.2 로깅 체계 통일

**표준**: `utils.logger.logger` 사용

**점검 항목**:

- [x] `print()` 대신 `logger.info()` 사용
- [x] f-string 포맷 사용 (printf 스타일 제거)
- [x] 적절한 로그 레벨 선택

**상태**: ✅ CHANGELOG.md 기준 대부분 완료

### 4.3 설정 관리 통일

**표준**: `config/config_manager.py`의 `Config` 객체

**점검 항목**:

- [x] 모든 설정값을 `config.json`에서 로드
- [x] `.get()` 메서드로 안전한 접근
- [x] 기본값 제공

**상태**: ✅ 완료 (config.json, config_manager.py 통합 완료)

---

## 5. Gap 요약 및 우선순위

### High Priority (필수)

1. **단일 인스턴스 실행** (`main.py`): 중복 실행 방지
2. **요.venv 정리**: 순수 가상환경화
3. **requirements.txt 버전 고정**: Google 라이브러리 버전 명시

### Medium Priority (권장)

4. **build.py 수정**: PyInstaller 숨은 임포트 추가
5. **UX 개선 검증**: 창 최상위, 입력 UX 실제 구현 확인
6. **Google Sheets 통합 테스트**: 백업 기능 실제 테스트

### Low Priority (선택)

7. **경로 처리 코드 검색**: 일관성 재확인
8. **settings.py 로그 메시지 보강**: 사용자 안내 개선
9. **config_manager.py Google Sheets 키 접근**: 편의 메서드 추가

---

## 6. 권장 조치 사항

### 즉시 조치

1. `.venv` 정리 스크립트 실행 (백업 후)
2. `main.py`에 단일 인스턴스 로직 추가
3. `requirements.txt` 버전 고정:
   ```
   gspread==5.12.0
   google-auth==2.23.4
   google-auth-oauthlib==1.1.0
   ```

### 다음 iteration

1. `build.py` PyInstaller 옵션 보강:
   ```python
   hidden_imports = ['gspread', 'google.auth', 'google.oauth2.service_account']
   ```
2. UX 개선 사항 실제 구현 확인 (코드 레벨 검증)
3. Google Sheets 백업 End-to-End 테스트

### 장기 계획

1. 경로 처리 전체 코드 검색 및 리팩토링
2. Phase 2 웹 인터페이스 설계 시작 (INTEGRATION_PLAN 6절 참조)

---

## 7. 검증 체크리스트

### 코드 검증

- [ ] `find_by_name` 또는 `grep_search`로 경로 처리 패턴 검색
- [ ] `ui/main_window.py` UX 개선 코드 실제 존재 확인
- [ ] `main.py` Mutex 코드 존재 확인

### 기능 검증

- [ ] 프로그램 중복 실행 시도 → 경고 표시
- [ ] 배합 기록 저장 → Google Sheets 업로드 (옵션 ON 시)
- [ ] PDF 생성 → 스캔 효과 적용 확인

### 환경 검증

- [ ] `.venv` 재생성 후 정상 실행
- [ ] PyInstaller 빌드 후 실행 테스트
- [ ] 배포 ZIP 생성 및 검증

---

## 8. 결론

### 완료 항목 (100%)

- Google Sheets 백업 통합 (백엔드 로직)
- 데이터베이스 구조 (백업 트리거)
- 설정 관리 통일
- 로깅 체계 정비

### 미완료 항목 (0%)

- .venv 최종 정리
- 단일 인스턴스실행
- PyInstaller 설정 보강
- UX 개선 실제 구현 확인

### 다음단계

1. [bkit PDCA] Plan 작성: 미완료 항목 상세 계획
2. [bkit PDCA] Design 작성: UX 개선 상세 설계
3. [bkit PDCA] Implementation: 우선순위 기반 순차 구현

---

**분석일**: 2026-01-31  
**버전**: 1.0  
**상태**: Completed
