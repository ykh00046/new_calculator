# Production Analysis Dashboard

Streamlit 기반의 생산 데이터 분석/시각화 대시보드입니다.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

---

## 주요 기능
- 일간/주간/월간/커스텀 분석 (최근 N일 추세, 이동평균, 비교기간)
- 카테고리/제품 필터(Top5/Top10/커스텀), 단위 자동/수동 설정
- 시간대별/일별 차트, 상위 제품 카드, KPI 비교(전일/전기간)
- 캐싱 및 상위 N 제한으로 대용량 데이터에서도 원활한 뷰

---

## 빠른 시작

### 1) 사전 준비 - Python 3.10+ 권장
- SQLite 데이터베이스 파일 `production_analysis.db` 준비

### 2) 설치
```bash
cd C:\X\material_box\production_analysis_dashboard
pip install -r requirements.txt
```

### 3) 실행
`run_dashboard.bat` 하나로 실행합니다.
```bash
# 기본 실행 (포트 8504)
run_dashboard.bat

# 포트 지정
run_dashboard.bat 8501

# 헤드리스 실행
run_dashboard.bat 8504 headless

# 의존성 설치 후 실행
run_dashboard.bat 8504 headless install
```

### 4) 데이터베이스 설정
- 앱 초기화면에서 DB 파일 업로드 또는 파일 경로 입력
- 저장된 경로는 `config/db_path.conf`에 보관됩니다

---

## 프로젝트 구조(요약)
```
production_analysis_dashboard/
  app.py                      # 메인 앱
  requirements.txt            # 의존성
  config/
    settings.py               # 기본 DB 경로(프로젝트 루트)
    user_settings.py          # 사용자 DB 경로 save/load
  data_access/
    db_connector.py           # DB 조회/파싱/분류(캐시, 인코딩 보정)
  components/
    daily_tab.py              # 일간 모니터링 탭
    weekly_tab.py             # 주간 분석 탭
    monthly_tab.py            # 월간 분석 탭
    custom_tab.py             # 커스텀 기간 분석 탭
    charts.py                 # Altair 차트
    summary.py                # KPI 메트릭
    product_cards.py          # 제품 카드/비교/트렌드
  utils/
    date_utils.py, data_utils.py, helpers.py
```

---

## 설정/옵션
- 포트 변경: `--server.port 8080`
- 헤드리스 모드: `--server.headless true`
- 테마/보안: `.streamlit/config.toml` 참고

자세한 배포/보안 가이드는 `DEPLOYMENT.md`를 참고하세요.

---

## 데이터베이스 요약 스키마
`production_records` 테이블 예시:
- `id` INTEGER (PK)
- `production_date` DATE (`YYYY-MM-DD`)
- `lot_number` VARCHAR(50)
- `item_code` VARCHAR(50)
- `item_name` VARCHAR(200)
- `good_quantity` DECIMAL(10,2) (kg/L)

---

## FAQ
1) 글자 깨짐(제품명/LOT 등)
- DB에 CP949 텍스트가 섞여 있어, 커넥터에서 인코딩 보정을 합니다.
- 여전히 깨짐이 보이면 DB 텍스트 인코딩을 확인해주세요.

2) 날짜 파싱 경고
- "Dropped N rows with invalid production_date" 메시지는 날짜 형식이 `YYYY-MM-DD`가 아닌 경우 발생합니다.
- 원본 데이터의 날짜 형식을 확인해주세요.

3) 선택 구간에 데이터 없음
- 선택한 기간/카테고리에 데이터가 없으면 메시지가 표시됩니다. 필터를 조정해보세요.
