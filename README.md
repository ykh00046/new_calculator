# Production Data Hub (Phase 1)

## Folder Structure
Place the following 4 files under `C:\X\Server_v1\`.

- `production_analysis.db`
- `app.py` (Streamlit Dashboard)
- `api.py` (FastAPI Data API)
- `manager.py` (Integrated Server Manager)

## Installation (Windows PowerShell)
```powershell
cd C:\X\Server_v1
python -m venv .venv
.\.venv\Scripts\activate

pip install -U pip
pip install streamlit fastapi uvicorn pandas openpyxl
```

## Execution
1) Double-click `manager.py`  
2) Left: **Start Web Server** → http://localhost:8501 (or http://[Local_IP]:8501)
3) Right: **Start API Server** → http://localhost:8000 (or http://[Local_IP]:8000)

## API 간단 예시
- 최신 1000건: `GET http://localhost:8000/records`
- 특정 품목: `GET http://localhost:8000/records/B0061`
- 기간 필터: `GET /records?date_from=2026-01-01&date_to=2026-01-19`
- 월별 총합: `GET /summary/monthly_total`
- 품목 목록: `GET /items?limit=200`
