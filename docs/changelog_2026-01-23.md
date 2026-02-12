# 작업 일지 - 2026-01-23

## 1. AI 모델 업그레이드

**변경 파일**: `api/chat.py:181`

| 항목 | Before | After |
|------|--------|-------|
| Gemini 모델 | gemini-2.0-flash | gemini-2.5-flash |

---

## 2. SQL 버그 수정

**증상**: "로트가 2로 시작하는 생산량" 질문 시 오류
```
sqlite3.OperationalError: aggregate functions are not allowed in the GROUP BY clause
```

**원인**: `get_production_summary`에서 GROUP BY에 집계 함수 포함

**수정 파일**:
- `api/tools.py:165` - `outer_group_by=""` 로 변경
- `shared/database.py:340-356` - GROUP BY 절 조건부 생성

---

## 3. Text-to-SQL 도구 추가

**새 도구**: `execute_custom_query`

**파일**: `api/tools.py`

**기능**:
- AI가 직접 SQL 작성하여 복잡한 조건 처리
- 로트 번호 패턴, 다중 필터 등 기존 도구로 불가능한 질문 대응

**안전장치**:
- SELECT만 허용
- LIMIT 1000 자동 적용
- 3초 타임아웃
- DB 자체가 read-only 모드

---

## 4. 시스템 아키텍처 문서 작성

**파일**: `docs/specs/system_architecture.md`

**포함 내용**:
- 서버 구성 (Dashboard :8501, API :8000)
- 분리 운영 설계 원칙 (장애 격리, 독립 배포)
- API 서버 보안 설계 (읽기 전용 아키텍처)
- AI 도구 확장 프로세스 (로그 기반 의사결정)
- 토큰 효율성 고려사항
- 데이터 조회량 제한 정책 (API vs AI 채팅)
- 효율적인 데이터 조회 패턴 (집계 + 상세 조합)

---

## 5. 실행 파일 추가

| 파일 | 용도 |
|------|------|
| `start_services_hidden.vbs` | 터미널 숨김 실행 |
| `설치방법.txt` | 새 PC 설치 가이드 |

---

## 6. v7 성능 개선 현황 확인

모든 주요 항목 적용 완료:
- GZip 압축
- ORJSONResponse
- Cursor 기반 Pagination
- 복합 인덱스 (idx_item_date)
- TTLCache + mtime 무효화
- 연결 캐싱 + mtime 재연결
- Dashboard TTL 차등화

---

## 다음 단계

- [ ] 다른 PC에서 서버 실행 테스트
- [ ] 기존 프로젝트 API 연동 테스트
