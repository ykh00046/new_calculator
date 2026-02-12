import io
import os
import re
import sqlite3
import sys
import requests
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add parent directory for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import (
    DB_FILE,
    ARCHIVE_DB_FILE,
    ARCHIVE_CUTOFF_DATE,
    ARCHIVE_CUTOFF_YEAR,
    DBRouter,
)

st.set_page_config(page_title="Production Data Hub", layout="wide", page_icon="🏭")


# ==========================================================
# Helpers
# ==========================================================
def get_db_mtime():
    """Get DB modification time for cache invalidation."""
    try:
        mtime = os.path.getmtime(DB_FILE)
        if ARCHIVE_DB_FILE.exists():
            archive_mtime = os.path.getmtime(ARCHIVE_DB_FILE)
            mtime = max(mtime, archive_mtime)
        return mtime
    except Exception:
        return 0


def run_self_check():
    if not DB_FILE.exists():
        return False, f"DB 파일을 찾을 수 없습니다: {DB_FILE}"
    try:
        with DBRouter.get_connection(use_archive=False) as conn:
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='production_records'", conn)
            if tables.empty:
                return False, "production_records 테이블이 존재하지 않습니다."
            columns = pd.read_sql("PRAGMA table_info(production_records)", conn)["name"].tolist()
            required = ["production_date", "item_code", "item_name", "good_quantity", "lot_number"]
            if not all(c in columns for c in required):
                return False, "필수 컬럼이 누락되었습니다."
        if not ARCHIVE_DB_FILE.exists():
            return True, "⚠️ Archive DB(2025)를 찾을 수 없습니다."
    except Exception as e:
        return False, f"DB 연결 확인 오류: {e}"
    return True, ""


@st.cache_data(ttl=300)  # 5분 - 제품 목록 변경 드묾
def load_item_list(db_ver):
    with DBRouter.get_connection(use_archive=False) as conn:
        df = pd.read_sql("""
            SELECT item_code, MAX(item_name) AS item_name
            FROM production_records
            GROUP BY item_code
            ORDER BY item_code
        """, conn)
    df["label"] = df["item_code"] + " | " + df["item_name"].fillna("")
    return df


def _parse_production_dt(series: pd.Series) -> pd.Series:
    """
    Parse Korean datetime format to pandas datetime.

    Handles formats like:
    - "2026-01-20 오전 10:30:00" -> 2026-01-20 10:30:00
    - "2026-01-20 오후 02:15:00" -> 2026-01-20 14:15:00
    - "2026-01-20 오전 12:30:00" -> 2026-01-20 00:30:00 (midnight)
    - "2026-01-20 오후 12:30:00" -> 2026-01-20 12:30:00 (noon)
    - "2026-01-20 14:30:00" -> 2026-01-20 14:30:00 (24h format passthrough)
    """
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(오전|오후)\s+(\d{1,2}):(\d{2}):(\d{2})")

    def convert_korean_time(val) -> str:
        """Convert Korean AM/PM format to 24-hour format."""
        if pd.isna(val):
            return val
        val_str = str(val)
        match = pattern.match(val_str)
        if not match:
            return val_str  # Return as-is for other formats (e.g., 24h format)

        date_part, ampm, hour_str, minute, second = match.groups()
        hour = int(hour_str)

        if ampm == "오전":
            # 오전 12시 = 00시 (자정), 오전 1-11시 = 1-11시
            if hour == 12:
                hour = 0
        else:  # 오후
            # 오후 12시 = 12시 (정오), 오후 1-11시 = 13-23시
            if hour != 12:
                hour += 12

        return f"{date_part} {hour:02d}:{minute}:{second}"

    s = series.apply(convert_korean_time)
    dt = pd.to_datetime(s, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    dt2 = pd.to_datetime(series, errors="coerce", format="mixed")
    return dt.fillna(dt2)


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


@st.cache_data(ttl=60)  # 1분 - 실시간성 필요
def load_records(item_codes, keyword, date_from, date_to, limit, db_ver):
    where = []
    params = []

    # v7: SELECT 컬럼 최적화 (SELECT * 제거)
    # Include id for stable sorting (matches api/main.py sort order)
    columns = "id, production_date, item_code, item_name, good_quantity, lot_number"

    if item_codes:
        where.append(f"item_code IN ({','.join(['?']*len(item_codes))})")
        params.extend(item_codes)
    if keyword:
        like = f"%{keyword}%"
        where.append("(item_code LIKE ? OR item_name LIKE ? OR lot_number LIKE ?)")
        params.extend([like, like, like])
    if date_from:
        where.append("production_date >= ?")
        params.append(_iso(date_from))
    if date_to:
        next_day = date_to + timedelta(days=1)
        where.append("production_date < ?")
        params.append(_iso(next_day))

    # Use DBRouter.pick_targets for consistent archive/live routing
    date_from_str = _iso(date_from) if date_from else None
    date_to_str = _iso(date_to + timedelta(days=1)) if date_to else None  # exclusive
    targets = DBRouter.pick_targets(date_from_str, date_to_str)

    where_clause = " AND ".join(where) if where else "1=1"

    # Build SQL with parameterized cutoff date (avoid f-string injection)
    # Include 'source' column for stable sorting (matches api/main.py: production_date DESC, source DESC, id DESC)
    if targets.use_archive and targets.use_live and ARCHIVE_DB_FILE.exists():
        # UNION: archive + live (with source column for sorting)
        archive_sql = f"SELECT 'archive' AS source, {columns} FROM archive.production_records WHERE {where_clause} AND production_date < ?"
        live_sql = f"SELECT 'live' AS source, {columns} FROM production_records WHERE {where_clause} AND production_date >= ?"
        final_sql = f"{archive_sql} UNION ALL {live_sql}"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE] + list(params) + [ARCHIVE_CUTOFF_DATE]
        sort_order = "ORDER BY production_date DESC, source DESC, id DESC"
    elif targets.use_archive and ARCHIVE_DB_FILE.exists():
        # Archive only
        final_sql = f"SELECT 'archive' AS source, {columns} FROM archive.production_records WHERE {where_clause} AND production_date < ?"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE]
        sort_order = "ORDER BY production_date DESC, id DESC"
    else:
        # Live only (default)
        final_sql = f"SELECT 'live' AS source, {columns} FROM production_records WHERE {where_clause} AND production_date >= ?"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE]
        sort_order = "ORDER BY production_date DESC, id DESC"

    final_sql += f" {sort_order} LIMIT ?"
    query_params.append(int(limit))

    with DBRouter.get_connection(use_archive=targets.use_archive) as conn:
        df = pd.read_sql(final_sql, conn, params=query_params)

    df["good_quantity"] = pd.to_numeric(df["good_quantity"], errors="coerce")
    df["production_dt"] = _parse_production_dt(df["production_date"])
    df["production_day"] = df["production_dt"].dt.date
    df["year_month"] = df["production_dt"].dt.to_period("M").astype(str)
    bad = int(df["production_dt"].isna().sum())
    return df, bad


@st.cache_data(ttl=180)  # 3분 - 집계 데이터
def load_monthly_summary(date_from, date_to, db_ver):
    where, params = [], []
    if date_from:
        where.append("production_date >= ?")
        params.append(_iso(date_from))
    if date_to:
        next_day = date_to + timedelta(days=1)
        where.append("production_date < ?")
        params.append(_iso(next_day))

    # Use DBRouter.pick_targets for consistent archive/live routing
    date_from_str = _iso(date_from) if date_from else None
    date_to_str = _iso(date_to + timedelta(days=1)) if date_to else None  # exclusive
    targets = DBRouter.pick_targets(date_from_str, date_to_str)

    where_clause = " AND ".join(where) if where else "1=1"
    select_cols = "substr(production_date, 1, 7) AS year_month, good_quantity"

    # Build SQL with parameterized cutoff date (avoid f-string injection)
    if targets.use_archive and targets.use_live and ARCHIVE_DB_FILE.exists():
        # UNION: archive + live
        archive_sql = f"SELECT {select_cols} FROM archive.production_records WHERE {where_clause} AND production_date < ?"
        live_sql = f"SELECT {select_cols} FROM production_records WHERE {where_clause} AND production_date >= ?"
        final_sql = f"{archive_sql} UNION ALL {live_sql}"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE] + list(params) + [ARCHIVE_CUTOFF_DATE]
    elif targets.use_archive and ARCHIVE_DB_FILE.exists():
        # Archive only
        final_sql = f"SELECT {select_cols} FROM archive.production_records WHERE {where_clause} AND production_date < ?"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE]
    else:
        # Live only (default)
        final_sql = f"SELECT {select_cols} FROM production_records WHERE {where_clause} AND production_date >= ?"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE]

    wrapper_sql = f"""
    SELECT year_month, SUM(good_quantity) AS total_production, COUNT(*) AS batch_count, AVG(good_quantity) AS avg_batch_size
    FROM ({final_sql})
    GROUP BY year_month ORDER BY year_month
    """

    with DBRouter.get_connection(use_archive=targets.use_archive) as conn:
        df = pd.read_sql(wrapper_sql, conn, params=query_params)
    return df


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


# ==========================================================
# UI Main
# ==========================================================
st.title("🏭 Production Data Hub")

check_ok, check_msg = run_self_check()
if not check_ok:
    st.error(f"🚨 시스템 초기화 실패: {check_msg}"); st.stop()
elif check_msg: st.warning(check_msg)

current_db_ver = get_db_mtime()

st.sidebar.header("🔍 검색 조건")
limit = st.sidebar.slider("표시 최대 건수", 500, 50000, 5000, 500)
keyword = st.sidebar.text_input("키워드(제품코드/제품명/LOT)", value="").strip() or None

today = date.today()
date_range = st.sidebar.date_input("기간(생산일)", value=(today - timedelta(days=90), today))
date_from, date_to = None, None
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    date_from, date_to = date_range[0], date_range[1]

items_df = load_item_list(db_ver=current_db_ver)
labels = items_df["label"].tolist()
label_to_code = dict(zip(labels, items_df["item_code"].tolist()))
selected_labels = st.sidebar.multiselect("제품 선택(복수 가능)", options=labels, default=[])
item_codes = [label_to_code[x] for x in selected_labels] if selected_labels else None

if st.sidebar.button("🔄 새로고침"):
    st.cache_data.clear()
    st.rerun()

tab1, tab2, tab3 = st.tabs(["📋 상세 이력", "📈 실적 추이", "🤖 AI 분석"])

with tab1:
    df, bad_dt = load_records(item_codes, keyword, date_from, date_to, limit, db_ver=current_db_ver)
    if bad_dt > 0: st.warning(f"⚠️ 날짜 파싱 실패 {bad_dt:,}건이 있습니다.")
    
    st.subheader(f"총 {len(df):,} 건")
    st.dataframe(df[["production_date", "item_code", "item_name", "good_quantity", "lot_number"]], width="stretch", hide_index=True)
    st.download_button("📥 엑셀 다운로드", to_excel_bytes(df), "production_records.xlsx")

with tab2:
    summary_df = load_monthly_summary(date_from, date_to, db_ver=current_db_ver)
    st.subheader("월별 생산량 및 가동 건수")
    
    if len(summary_df) == 0:
        st.info("데이터가 없습니다.")
    else:
        # Plotly Mixed Chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=summary_df['year_month'], y=summary_df['total_production'], name="총 생산량", marker_color='#1f77b4'), secondary_y=False)
        fig.add_trace(go.Scatter(x=summary_df['year_month'], y=summary_df['batch_count'], name="생산 건수", mode='lines+markers', line=dict(color='#ff7f0e', width=3)), secondary_y=True)
        
        fig.update_layout(title_text="월별 실적 추이", hovermode="x unified", template="plotly_white")
        fig.update_yaxes(title_text="생산량 (ea)", secondary_y=False)
        fig.update_yaxes(title_text="건수 (count)", secondary_y=True)
        
        st.plotly_chart(fig, width="stretch")
        st.dataframe(summary_df, width="stretch", hide_index=True)

with tab3:
    st.subheader("🤖 AI 생산 데이터 분석가")
    
    # Help Chips (FAQ)
    st.write("💡 **빠른 질문 추천:**")
    cols = st.columns(3)
    faq_queries = ["작년 생산량 1위 제품은?", "오늘 총 생산 실적 알려줘", "BW0021 제품의 평균 생산량은?"]
    
    selected_faq = None
    for i, q in enumerate(faq_queries):
        if cols[i%3].button(q, width="stretch"):
            selected_faq = q

    # Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_container = st.container(height=450) # Scrollable area
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input Logic
    prompt = st.chat_input("무엇이든 물어보세요...")
    if selected_faq: # Chip clicked
        prompt = selected_faq

    if prompt:
        with chat_container:
            st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            with st.spinner("분석 중..."):
                resp = requests.post("http://localhost:8000/chat/", json={"query": prompt}, timeout=60)
            if resp.status_code == 200:
                answer = resp.json()["answer"]
                with chat_container:
                    st.chat_message("assistant").markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else: st.error(f"API 오류: {resp.status_code}")
        except Exception as e: st.error(f"연결 오류: {e}")

    if st.button("🗑️ 대화 기록 지우기"):
        st.session_state.messages = []; st.rerun()