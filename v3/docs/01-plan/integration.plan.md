# v3/main ↔ .venv 통합 계획서

본 문서는 `v3/main` 프로젝트와 `.venv` 내부에 섞여 있는 앱 자산(설정/데이터/유틸 등)을 통합하고, `.venv`는 순수 가상환경으로 정상화하는 것을 목표로 한다. 기능 차이를 정리하고, 이전 절차·리스크·검증·개선안을 상세히 기술한다.

- 대상 경로: `v3/main`, `.venv`
- 최종 목표: 애플리케이션 소스/리소스/출력물은 `v3/main` 트리로 정리, `.venv`는 파이썬 패키지 전용
- 산출물: 본 계획서, 마이그레이션 스크립트 초안, 체크리스트

---

## 1) 현황 요약

- 메인 코드/기능
  - 설정/경로: `v3/main/config/settings.py`는 비ASCII 파일명/경로 호환, `sys.frozen`(PyInstaller) 대응, 출력 폴더 자동 대체 등 방어적 경로 처리 포함.
  - 구성 관리: `v3/main/config/config_manager.py`는 안전한 JSON 로드, dotted key 접근(`Config.get`), `scan_effects` 읽기/저장(`save_scan_effects`) 지원.
  - 기능 설정: `v3/main/config/config.json`에는 `ui`, `excel`, `logging`, `validation` 외에 `signature`, `scan_effects` 등 고급 옵션 존재.
  - 로깅: `v3/main/utils/logger.py` 존재, 파일/에러/콘솔 핸들러 구성.
  - 빌드/배포: `v3/main/build.py`, `v3/main/deploy.py`로 PyInstaller 빌드 및 배포 ZIP 생성.
  - PDF/서명/스캔효과: `pdf_processor_gui`, `signature_qa_tool` 등 품질 제어 및 UI 연동 흔적.

- .venv 쪽에서 발견된 앱 자산(순수 가상환경 범위를 넘어섬)
  - 설정: `.venv/config/settings.py` (기능 축소판, 경로 처리 단순), `.venv/config/config.json` (메인 대비 키 일부 누락: `signature`, `scan_effects` 등)
  - Google Sheets 백업 설정/유틸: `.venv/config/google_sheets_config.py`, `.venv/config/google_sheets_settings.json`
  - 로깅: `.venv/utils/logger.py` (메인과 유사)
  - 데이터/출력물: `.venv/data/mixing_records.db`(= `v3/main/data/mixing_records.db`와 해시 동일), `.venv/output/excel/*.xlsx` 등 실행 산출물

- 중복/차이
  - `settings.py`: 메인은 고급 경로 처리와 폴백 포함, .venv는 단순
  - `config.json`: 메인은 `signature`, `scan_effects`, 큰 폰트/윈도우 기본값 등 최신화; .venv는 일부 섹션 부재
  - Google Sheets: .venv에만 명시적 구성 모듈 존재, 메인은 `gspread`만 의존성에 있고 통합 미완

---

## 2) 통합 원칙

- `.venv`는 앱 자산을 두지 않는다(패키지 전용). 앱 자산은 `v3/main`로 이전.
- 경로/로캘/패키징은 모두 PyInstaller 동작(`sys.frozen`)을 기준으로 안전성 확보.
- 구성은 단일 진실 소스(Single Source of Truth) 원칙: `config/config.json` + 필요한 경우 보안상 별도 파일(자격증명)로 분리.
- 기존 사용 데이터(예: `mixing_records.db`)는 보존·백업 후 이동.
- 변경은 점진적(기능 플래그/환경변수로 단계적 활성화)으로 적용.

---

## 3) 목표 디렉터리 구조(안)

- `v3/main/config/`
  - `settings.py`(메인 유지)
  - `config_manager.py`(메인 유지 + Sheets 연동 키 보강)
  - `config.json`(최신 스키마 유지)
  - `google_sheets_config.py`(신규: .venv 버전 이관·리팩터)
  - `google_sheets_settings.json`(선택: 배포 제외, 사용자 환경에 생성)
- `v3/main/models/backup/`
  - `google_sheets_backup.py`(신규: 실 백업 로직/인터페이스)
- `v3/main/ui/dialogs/`
  - `google_sheets_settings_dialog.py`(선택: UI 설정 다이얼로그)
- `v3/main/data/mixing_records.db`(유지)
- `v3/main/output/`(또는 한글 폴더 병행 지원, 메인 로직은 자동 폴백)

---

## 4) 기능 통합 상세 계획

- 설정/경로 처리
  - 유지: `v3/main/config/settings.py`의 비ASCII/폴백 로직을 표준으로 채택.
  - 정리: `.venv/config/settings.py` 내용은 폐기. 필요한 상수/매핑은 메인에 이미 존재.

- 구성 관리자 강화
  - 유지: `v3/main/config/config_manager.py`의 `get`, `save_scan_effects` 등.
  - 보강: `mixing.workers`, `paths.output` 등 한글 경로/문자깨짐 정합성 검증, 기본값 보정.
  - 추가: Google Sheets 관련 섹션을 단일 `config.json`에 병합할지 여부 결정(권장: 민감 정보는 별도 JSON 유지).

- Google Sheets 백업 기능 이관(+개선)
  - 파일 이관: `.venv/config/google_sheets_config.py` → `v3/main/config/google_sheets_config.py`
    - 로거 종속: `from utils.logger import logger` 유지
    - 경로 해석: `BASE_PATH`/`sys.frozen` 처리 보강(`settings.py`와 동일 기준 사용)
    - 설정 JSON: `google_sheets_settings.json` 파일은 사용자 로컬에만 존재하도록 하고, 배포/버전관리는 제외
  - 백업 로직: `v3/main/models/backup/google_sheets_backup.py` 신설
    - 인터페이스: `BackupProvider` 프로토콜(예: `backup_records(db_path) -> Result`)
    - 구현: `GoogleSheetsBackup`에서 `gspread` 인증(서비스 계정 JSON), 스프레드시트 URL, 워크시트 선택, 업로드 포맷 정의
    - 트리거: 레코드 저장/내보내기 시점에서 비동기 실행(스레드/큐), 실패 시 재시도/로깅
  - UI(선택): `google_sheets_settings_dialog.py`
    - 항목: `credentials_file`, `spreadsheet_url`, `backup_enabled`, `auto_backup_on_save`
    - 검증: 파일 존재/URL 형식/권한 체크 버튼
  - 빌드 반영: PyInstaller에 `gspread`, `google-auth`, `google.oauth2.service_account` 숨은 임포트, 설정 JSON 제외 정책 적용

- 데이터베이스/출력물 정리
  - DB: `.venv/data/mixing_records.db` → `v3/main/data/mixing_records.db` (해시 동일 확인됨)
  - 출력물: `.venv/output/…` → `v3/main/output/…` 또는 메인 로직 폴백 경로 활용
  - `settings.py`의 출력 경로 폴백(`output`/한글 폴더) 로직 확정, 메시지/로그 안내 추가

- 빌드/배포
  - `v3/main/build.py`: 숨은 임포트 추가, `--add-data=config;config` 유지, Sheets 설정 JSON은 런타임 생성/로드이므로 포함하지 않음
  - `v3/main/deploy.py`: 문서/리소스 포함 정책 재검토(민감 정보 제외)
  - `v3/main/requirements.txt`: `gspread`, `google-auth` 버전 고정 및 호환성 표기

---

## 5) 마이그레이션 절차(실행 순서)

1. 백업
   - `v3/main/data/mixing_records.db`와 `.venv/data/mixing_records.db` 추가 백업 생성
   - `.venv/config/google_sheets_settings.json`(존재 시) 별도 백업
2. 코드/설정 이관
   - `.venv/config/google_sheets_config.py` → `v3/main/config/google_sheets_config.py` 복사 후 경로/로거 의존 보강
   - `v3/main/models/backup/google_sheets_backup.py` 신규 생성, `BackupProvider` 설계 및 구현
3. 통합 지점 연결
   - 레코드 저장/내보내기 로직(`v3/main/models/database.py`, `v3/main/models/excel_exporter.py`, `v3/main/ui/main_window.py`)에 백업 트리거 삽입(기본 OFF, 설정 플래그로 ON)
4. 설정 경로/스키마 조정
   - `config.json`의 `paths.output` 등 깨진 값 교정, 누락 키(필요 시) 추가
   - Google Sheets 설정은 별도 JSON 유지, 경로 해석 보강
5. 빌드/의존성
   - `requirements.txt` 재확인, 테스트 설치 후 빌드 스모크테스트
   - PyInstaller 옵션에 Sheets 관련 숨은 임포트 추가
6. 데이터/출력물 정리
   - `.venv/output` 산출물 정리(보존 필요 시 압축 후 보관), `.venv` 내 앱 자산 제거
7. 검증/릴리즈
   - 아래 체크리스트로 로컬/패키징/실행 검증 후 태그/배포 ZIP 생성

---

## 6) 예상 이슈와 대응

- 가상환경 오염: `.venv`에 남아있는 앱 자산
  - 대응: 마이그레이션 시 수집/이관 후 `.venv` 클린 재생성(`python -m venv .venv`), `pip install -r requirements.txt`
- 경로/로캘 이슈: 한글 파일/폴더명, 패키징 시 경로 차이
  - 대응: `settings.py`의 폴백 로직 표준화, 파일 존재 자동 감지, 로깅 강화
- Google 인증/권한
  - 대응: 서비스 계정 JSON 경로 검증, 스프레드시트 공유 설정 가이드, 네트워크 오류 재시도/타임아웃/로그
- 빌드 누락 라이브러리
  - 대응: PyInstaller 숨은 임포트/데이터 포함 점검 리스트화
- Excel → PDF/이미지 처리 환경 의존(Windows COM, Poppler 등)
  - 대응: 옵션화(`config.json`), 환경 체크 유틸/로그 안내, 우회 경로 준비

---

## 7) 개선안(기존 아쉬움 보완)

- 경로 해상도 일원화: 비ASCII/폴백/자동감지 로직 일관 적용
- 설정 일관성: 모든 런타임 옵션을 `config.json` 중심으로 관리, 민감 정보만 별도 JSON
- 백업 신뢰성: 비동기/재시도/상태표시(마지막 성공/실패 카운트) 및 UI 설정 제공
- 로깅 가시성: 에러 시 컨텍스트 포함, 사용자 안내 메시지 개선
- 배포 보안: 자격증명/민감 설정은 배포 제외, 최초 실행 시 안내/설정 마법사 제공(선택)
- **사용자 경험(UX) 개선:**
  - **단일 인스턴스 실행:** 프로그램 중복 실행 방지 및 기존 창 활성화 (Windows Mutex 활용).
  - **창 항상 맨 위:** 로그인 및 메인 창을 항상 맨 위에 표시하여 시인성 및 작업 흐름 집중도 향상.
  - **배합량 입력 UX 강화:**
    - 값이 '0'일 때 "배합량 입력" 텍스트 표시 (`setSpecialValueText`).
    - 포커스 시 기존 값 전체 선택(`selectAll`)으로 즉시 입력 가능.
  - **자재 LOT 입력 UX 강화:**
    - LOT 입력 필드 포커스 시 기존 값 전체 선택(`selectAll`)으로 즉시 입력 가능.
    - Enter 키 입력 시 다음 자재 LOT 셀로 포커스 이동.

---

## 8) 검증 시나리오/체크리스트

- 로컬 실행(스크립트 모드)
  - 앱 구동, 기본 리소스/템플릿 자동 감지, 출력 폴더 생성 확인
  - 레코드 저장 → Google Sheets 백업 OFF 상태에서 정상 동작
  - 설정 다이얼로그에서 자격증명/URL 지정 → 저장/로드 OK
  - 백업 ON → 레코드 저장 시 업로드 성공, 로깅/상태 표시 OK
- 패키징 실행(PyInstaller)
  - `sys.frozen` 경로에서 동일 시나리오 통과
  - 로그/출력/리소스 경로 정상
- 회귀
  - 스캔 효과 기본값 로드/변경/저장(`config.save_scan_effects`) 정상
  - Excel 내보내기/품질 테스트 스모크(`v3/main/tests/test_pdf_quality.py`) 통과

---

## 9) 롤백 계획

- 코드 롤백: 브랜치/태그 기준 즉시 되돌림
- 데이터 롤백: 마이그레이션 전 백업한 DB/설정 JSON 복구
- 가상환경: `.venv` 삭제 후 재생성으로 초기화

---

## 10) 변경 대상(파일 기준 TODO)

- 수정
  - `v3/main/config/settings.py`: 출력 경로 안내/로그 메시지 보강(선택)
  - `v3/main/config/config_manager.py`: Google Sheets 키 접근 보조 메서드(선택)
  - `v3/main/build.py`: 숨은 임포트 추가, 데이터 포함 정책 점검
  - `v3/main/requirements.txt`: `gspread`, `google-auth` 버전 확정
  - `v3/main/ui/main_window.py`:
    - 백업 트리거 연결(기본 OFF) 로직 제거 (DataManager로 이관됨)
    - **창 항상 맨 위(`Qt.WindowStaysOnTopHint`) 설정 추가 (로그인 다이얼로그 및 메인 창)**
    - **배합량 입력 UX 개선 (초기값 '배합량 입력' 표시, 포커스 시 전체 선택)**
    - **자재 LOT 입력 UX 개선 (배경색 강조, 엔터 키 이동, 포커스 시 전체 선택)**
    - **_save_record 로직 변경 (DB 저장 전용)**
    - `_recalc_theory` 방어 코드 추가
  - `v3/main/models/database.py`: 백업 트리거 연결(기본 OFF) (완료)
  - `v3/main/models/excel_exporter.py`: 백업 트리거 연결 로직 제거 (여기서는 백업 로직 불필요)
  - `v3/main/models/data_manager.py`: `save_record`에서 `_export_report` 호출 제거 (DB 저장 전용)
  - `v3/main/main.py`: **단일 인스턴스 실행 로직 추가 (Windows Mutex 활용)**
- 추가
  - `v3/main/config/google_sheets_config.py`(이관·보강) (완료)
  - `v3/main/models/backup/google_sheets_backup.py`(신규) (완료)
  - `v3/main/ui/dialogs/google_sheets_settings_dialog.py`(선택) (완료)
  - `v3/main/tools/migrate_from_venv.py`(마이그레이션 스크립트)
- 제거/정리
  - `.venv` 내 앱 자산(`config/`, `utils/`, `data/`, `output/` 등) → 프로젝트 트리로 이관 후 `.venv` 정리

---

## 11) 일정(예시)

- D0–D1: 자산 이관/리팩터(구성/백업 모듈)
- D2: 통합 지점 연결 및 로컬 검증
- D3: 패키징/배포 검증, 문서화 완료

---

## 12) 부록: 차이점 요약

- 동일: `mixing_records.db`(해시 동일), 로거 구조
- 메인 전용: `scan_effects`/`signature` 옵션, 경로 폴백, 빌드/배포 스크립트, PDF 품질 도구
- .venv 전용: Google Sheets 구성/설정 파일, 산출물 폴더

