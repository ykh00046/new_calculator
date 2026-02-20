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

# Import UI enhancement components
from components import (
    # Theme
    init_theme,
    render_theme_toggle,
    apply_custom_css,
    get_colors,
    # Loading
    show_loading_status,
    render_last_update,
    # Responsive
    apply_responsive_css,
    # KPI
    calculate_kpis,
    render_kpi_cards,
    get_sparkline_data,
    get_sparkline_for_top_product,
    # Charts
    create_top10_bar_chart,
    create_distribution_pie,
    create_trend_lines,
    get_chart_config,
    # Presets
    init_presets,
    render_preset_manager,
)

st.set_page_config(page_title="Production Data Hub", layout="wide", page_icon=":factory:")

# ==========================================================
# Theme and UI Initialization
# ==========================================================
init_theme()
apply_responsive_css()
render_theme_toggle()
apply_custom_css()
init_presets()


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
        return False, f"Database file not found: {DB_FILE}"
    try:
        with DBRouter.get_connection(use_archive=False) as conn:
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='production_records'", conn)
            if tables.empty:
                return False, "production_records table does not exist."
            columns = pd.read_sql("PRAGMA table_info(production_records)", conn)["name"].tolist()
            required = ["production_date", "item_code", "item_name", "good_quantity", "lot_number"]
            if not all(c in columns for c in required):
                return False, "Required columns are missing."
        if not ARCHIVE_DB_FILE.exists():
            return True, "Warning: Archive DB (2025) not found."
    except Exception as e:
        return False, f"DB connection check error: {e}"
    return True, ""


@st.cache_data(ttl=300)  # 5 minutes - product list rarely changes
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
    - Also handles English "AM"/"PM" format
    """
    # Match both Korean (오전/오후) and English (AM/PM) formats
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(오전|오후|AM|PM)\s+(\d{1,2}):(\d{2}):(\d{2})")

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

        # Handle both Korean and English AM/PM
        is_am = ampm in ("오전", "AM")

        if is_am:
            # AM 12 = 00 (midnight), AM 1-11 = 1-11
            if hour == 12:
                hour = 0
        else:  # PM/오후
            # PM 12 = 12 (noon), PM 1-11 = 13-23
            if hour != 12:
                hour += 12

        return f"{date_part} {hour:02d}:{minute}:{second}"

    s = series.apply(convert_korean_time)
    dt = pd.to_datetime(s, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    dt2 = pd.to_datetime(series, errors="coerce", format="mixed")
    return dt.fillna(dt2)


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


@st.cache_data(ttl=60)  # 1 minute - real-time data needed
def load_records(item_codes, keyword, date_from, date_to, limit, db_ver):
    where = []
    params = []

    # v7: SELECT column optimization (remove SELECT *)
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


@st.cache_data(ttl=180)  # 3 minutes - aggregated data
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


@st.cache_data(ttl=180)  # 3 minutes - daily aggregated data
def load_daily_summary(date_from, date_to, db_ver):
    """Load daily aggregated production data."""
    where, params = [], []
    if date_from:
        where.append("production_date >= ?")
        params.append(_iso(date_from))
    if date_to:
        next_day = date_to + timedelta(days=1)
        where.append("production_date < ?")
        params.append(_iso(next_day))

    date_from_str = _iso(date_from) if date_from else None
    date_to_str = _iso(date_to + timedelta(days=1)) if date_to else None
    targets = DBRouter.pick_targets(date_from_str, date_to_str)

    where_clause = " AND ".join(where) if where else "1=1"
    select_cols = "substr(production_date, 1, 10) AS production_day, good_quantity"

    if targets.use_archive and targets.use_live and ARCHIVE_DB_FILE.exists():
        archive_sql = f"SELECT {select_cols} FROM archive.production_records WHERE {where_clause} AND production_date < ?"
        live_sql = f"SELECT {select_cols} FROM production_records WHERE {where_clause} AND production_date >= ?"
        final_sql = f"{archive_sql} UNION ALL {live_sql}"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE] + list(params) + [ARCHIVE_CUTOFF_DATE]
    elif targets.use_archive and ARCHIVE_DB_FILE.exists():
        final_sql = f"SELECT {select_cols} FROM archive.production_records WHERE {where_clause} AND production_date < ?"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE]
    else:
        final_sql = f"SELECT {select_cols} FROM production_records WHERE {where_clause} AND production_date >= ?"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE]

    wrapper_sql = f"""
    SELECT production_day, SUM(good_quantity) AS total_production, COUNT(*) AS batch_count
    FROM ({final_sql})
    GROUP BY production_day ORDER BY production_day
    """

    with DBRouter.get_connection(use_archive=targets.use_archive) as conn:
        df = pd.read_sql(wrapper_sql, conn, params=query_params)
    return df


@st.cache_data(ttl=180)  # 3 minutes - weekly aggregated data
def load_weekly_summary(date_from, date_to, db_ver):
    """Load weekly aggregated production data."""
    where, params = [], []
    if date_from:
        where.append("production_date >= ?")
        params.append(_iso(date_from))
    if date_to:
        next_day = date_to + timedelta(days=1)
        where.append("production_date < ?")
        params.append(_iso(next_day))

    date_from_str = _iso(date_from) if date_from else None
    date_to_str = _iso(date_to + timedelta(days=1)) if date_to else None
    targets = DBRouter.pick_targets(date_from_str, date_to_str)

    where_clause = " AND ".join(where) if where else "1=1"
    # Use strftime for week-based grouping
    select_cols = "substr(production_date, 1, 4) || '-W' || printf('%02d', (strftime('%j', production_date) - 1) / 7 + 1) AS year_week, good_quantity"

    if targets.use_archive and targets.use_live and ARCHIVE_DB_FILE.exists():
        archive_sql = f"SELECT {select_cols} FROM archive.production_records WHERE {where_clause} AND production_date < ?"
        live_sql = f"SELECT {select_cols} FROM production_records WHERE {where_clause} AND production_date >= ?"
        final_sql = f"{archive_sql} UNION ALL {live_sql}"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE] + list(params) + [ARCHIVE_CUTOFF_DATE]
    elif targets.use_archive and ARCHIVE_DB_FILE.exists():
        final_sql = f"SELECT {select_cols} FROM archive.production_records WHERE {where_clause} AND production_date < ?"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE]
    else:
        final_sql = f"SELECT {select_cols} FROM production_records WHERE {where_clause} AND production_date >= ?"
        query_params = list(params) + [ARCHIVE_CUTOFF_DATE]

    wrapper_sql = f"""
    SELECT year_week, SUM(good_quantity) AS total_production, COUNT(*) AS batch_count
    FROM ({final_sql})
    GROUP BY year_week ORDER BY year_week
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
st.title(":factory: Production Data Hub")

check_ok, check_msg = run_self_check()
if not check_ok:
    st.error(f":rotating_light: System initialization failed: {check_msg}")
    st.stop()
elif check_msg:
    st.warning(check_msg)

current_db_ver = get_db_mtime()

# Sidebar - Search Conditions
st.sidebar.header(":mag: Search Filters")
limit = st.sidebar.slider("Max Records", 500, 50000, 5000, 500)
keyword = st.sidebar.text_input("Keyword (Code/Name/LOT)", value="").strip() or None

today = date.today()
date_range = st.sidebar.date_input("Date Range (Production)", value=(today - timedelta(days=90), today))
date_from, date_to = None, None
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    date_from, date_to = date_range[0], date_range[1]

items_df = load_item_list(db_ver=current_db_ver)
labels = items_df["label"].tolist()
label_to_code = dict(zip(labels, items_df["item_code"].tolist()))
selected_labels = st.sidebar.multiselect("Select Products", options=labels, default=[])
item_codes = [label_to_code[x] for x in selected_labels] if selected_labels else None

# Filter Preset Manager - can return loaded preset values
loaded_preset = render_preset_manager(
    current_item_codes=item_codes,
    current_date_from=date_from,
    current_date_to=date_to,
    current_keyword=keyword,
    current_limit=limit
)

# Apply loaded preset values if user clicked Apply
if loaded_preset:
    # Note: In Streamlit, we can't directly set widget values.
    # The preset values are returned for informational purposes.
    # A more sophisticated implementation would use session_state
    # to control default values.
    st.sidebar.info(f"Loaded preset. Please adjust filters and refresh.")

if st.sidebar.button(":arrows_counterclockwise: Refresh"):
    st.cache_data.clear()
    st.rerun()

# Load data for KPIs and tabs
df, bad_dt = load_records(item_codes, keyword, date_from, date_to, limit, db_ver=current_db_ver)

# Render KPI Cards at top with sparklines
kpis = calculate_kpis(df, date_from, date_to)

# Calculate sparkline data (7-day trend)
production_sparkline = get_sparkline_data(df, days=7)
batch_sparkline = get_sparkline_data(df, days=7)  # Use same for batch count
top_product_sparkline = get_sparkline_for_top_product(df, kpis['top_item'], days=7)

render_kpi_cards(
    kpis,
    get_colors(),
    sparkline_data=production_sparkline,
    batch_sparkline=batch_sparkline,
    top_product_sparkline=top_product_sparkline
)

# Display last update time
render_last_update()

if bad_dt > 0:
    st.warning(f":warning: {bad_dt:,} records have date parsing issues.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([":memo: Details", ":chart_with_upwards_trend: Trends", ":robot: AI Analysis", ":bar_chart: Product Comparison"])

with tab1:
    st.subheader(f"Total {len(df):,} Records")
    st.dataframe(df[["production_date", "item_code", "item_name", "good_quantity", "lot_number"]], width="stretch", hide_index=True)
    st.download_button(":inbox_tray: Download Excel", to_excel_bytes(df), "production_records.xlsx")

with tab2:
    # Aggregation unit selector
    agg_unit = st.radio(
        "Aggregation Unit",
        options=["Daily", "Weekly", "Monthly"],
        index=2,  # Default: Monthly
        horizontal=True
    )

    # Load appropriate data based on aggregation unit
    if agg_unit == "Daily":
        summary_df = load_daily_summary(date_from, date_to, db_ver=current_db_ver)
        x_col = "production_day"
    elif agg_unit == "Weekly":
        summary_df = load_weekly_summary(date_from, date_to, db_ver=current_db_ver)
        x_col = "year_week"
    else:  # Monthly
        summary_df = load_monthly_summary(date_from, date_to, db_ver=current_db_ver)
        x_col = "year_month"

    st.subheader(f"{agg_unit} Production & Batch Count")

    if len(summary_df) == 0:
        st.info("No data available for the selected period.")
    else:
        # Get theme colors for chart template
        colors = get_colors()
        chart_template = colors.get("chart_template", "plotly_white")

        # Plotly Mixed Chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(
                x=summary_df[x_col],
                y=summary_df['total_production'],
                name="Total Production",
                marker_color='#1f77b4'
            ),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(
                x=summary_df[x_col],
                y=summary_df['batch_count'],
                name="Batch Count",
                mode='lines+markers',
                line=dict(color='#ff7f0e', width=3)
            ),
            secondary_y=True
        )

        fig.update_layout(
            title_text=f"{agg_unit} Performance Trends",
            hovermode="x unified",
            template=chart_template
        )
        fig.update_yaxes(title_text="Production (ea)", secondary_y=False)
        fig.update_yaxes(title_text="Batch Count", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True, config=get_chart_config(f"production_trends_{agg_unit.lower()}"))
        st.dataframe(summary_df, width="stretch", hide_index=True)

with tab3:
    st.subheader(":robot: AI Production Data Analyst")

    # Help Chips (FAQ)
    st.write(":bulb: **Quick Questions:**")
    cols = st.columns(3)
    faq_queries = ["Top product last year?", "Today's total production?", "Average production for BW0021?"]

    selected_faq = None
    for i, q in enumerate(faq_queries):
        if cols[i % 3].button(q, use_container_width=True):
            selected_faq = q

    # Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_container = st.container(height=450)  # Scrollable area
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input Logic
    prompt = st.chat_input("Ask anything...")
    if selected_faq:  # Chip clicked
        prompt = selected_faq

    if prompt:
        with chat_container:
            st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            with st.spinner("Analyzing..."):
                resp = requests.post("http://localhost:8000/chat/", json={"query": prompt}, timeout=60)
            if resp.status_code == 200:
                answer = resp.json()["answer"]
                with chat_container:
                    st.chat_message("assistant").markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"API Error: {resp.status_code}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

    if st.button(":wastebasket: Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

with tab4:
    st.subheader(":bar_chart: Product Comparison")

    # Get theme colors for chart template
    colors = get_colors()
    chart_template = colors.get("chart_template", "plotly_white")

    # Two columns for charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.write("**Top 10 Products**")
        fig_bar = create_top10_bar_chart(df, chart_template)
        st.plotly_chart(fig_bar, use_container_width=True, config=get_chart_config("top10_products"))

    with col_right:
        st.write("**Production Distribution**")
        fig_pie = create_distribution_pie(df, chart_template)
        st.plotly_chart(fig_pie, use_container_width=True, config=get_chart_config("product_distribution"))

    # Product trend comparison
    st.divider()
    st.write("**Product Trend Comparison**")

    # Multi-select for products to compare
    if not items_df.empty:
        compare_options = items_df["item_code"].tolist()
        selected_compare = st.multiselect(
            "Select products to compare (up to 5)",
            options=compare_options,
            max_selections=5,
            help="Select 2-5 products to compare their production trends"
        )

        if selected_compare:
            # Aggregation unit for trend comparison
            trend_agg = st.radio(
                "Trend Aggregation",
                options=["Daily", "Weekly", "Monthly"],
                index=2,
                horizontal=True,
                key="trend_agg_unit"
            )

            fig_trend = create_trend_lines(df, selected_compare, trend_agg, chart_template)
            st.plotly_chart(fig_trend, use_container_width=True, config=get_chart_config("product_trends"))
        else:
            st.info("Select products above to view trend comparison.")
    else:
        st.info("No products available for comparison.")
