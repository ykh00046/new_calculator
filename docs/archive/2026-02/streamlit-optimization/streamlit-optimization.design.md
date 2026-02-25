# Design: Streamlit Dashboard Optimization

## Design Overview

Plan 문서를 기반으로 Dashboard UI/UX 최적화 구현 설계

## Architecture

### Before (Current)

```
dashboard/
├── app.py                    # CSS 주입 호출
└── components/
    ├── kpi_cards.py          # st.columns(4) 사용
    └── theme.py              # Python으로 CSS 주입
```

### After (Optimized)

```
dashboard/
├── app.py                    # theme.py 단순화
└── components/
    ├── kpi_cards.py          # st.container(horizontal=True) + 스파크라인
    └── theme.py              # config.toml 테마 감지 + 최소 CSS

.streamlit/
└── config.toml               # 테마 설정 (NEW)
```

## Component Design

### 1. KPI Cards with Sparklines

**File:** `dashboard/components/kpi_cards.py`

**Changes:**

```python
# BEFORE
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Production", value=f"{total:,} ea")

# AFTER
with st.container(horizontal=True):
    st.metric(
        label="Total Production",
        value=f"{total:,} ea",
        border=True,
        chart_data=last_7_days_trend,  # 스파크라인
        chart_type="line"
    )
```

**New Function Required:**

```python
def get_sparkline_data(df: pd.DataFrame, days: int = 7) -> list[int]:
    """Get daily production trend for last N days."""
    # Implementation
```

### 2. Theme Configuration

**File:** `.streamlit/config.toml` (NEW)

```toml
[theme.light]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#1F1F1F"
borderColor = "#E0E0E0"

[theme.dark]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
borderColor = "#333333"

[theme.light.sidebar]
backgroundColor = "#F0F2F6"

[theme.dark.sidebar]
backgroundColor = "#262730"
```

### 3. Simplified Theme Manager

**File:** `dashboard/components/theme.py`

**Changes:**

```python
# BEFORE: CSS 주입
def apply_custom_css():
    st.markdown(f"<style>...", unsafe_allow_html=True)

# AFTER: config.toml 테마 감지만 수행
def get_theme() -> str:
    """Detect current theme from Streamlit context."""
    try:
        return st.context.theme.base  # "light" or "dark"
    except:
        return "light"

def get_colors() -> dict:
    """Return color palette based on detected theme."""
    # CSS 주입 없이 색상만 반환
```

## Implementation Details

### D1: KPI Sparklines

| Step | Description | File |
|------|-------------|------|
| D1.1 | Add `get_sparkline_data()` function | kpi_cards.py |
| D1.2 | Update `render_kpi_cards()` to use sparklines | kpi_cards.py |
| D1.3 | Replace `st.columns(4)` with `st.container(horizontal=True)` | kpi_cards.py |
| D1.4 | Add `border=True` to each metric | kpi_cards.py |

### D2: Theme Config

| Step | Description | File |
|------|-------------|------|
| D2.1 | Create `.streamlit/` directory | - |
| D2.2 | Create `config.toml` with theme settings | .streamlit/config.toml |
| D2.3 | Update `get_theme()` to use `st.context.theme.base` | theme.py |
| D2.4 | Remove CSS injection from `apply_custom_css()` | theme.py |
| D2.5 | Keep minimal CSS only for unsupported styles | theme.py |

### D3: Integration

| Step | Description | File |
|------|-------------|------|
| D3.1 | Pass sparkline data to `render_kpi_cards()` | app.py |
| D3.2 | Test dark/light mode toggle | - |

## API Changes

None - 내부 UI 변경만 수행

## Data Flow

```
app.py
  │
  ├── load_daily_summary() ──→ get_sparkline_data()
  │                                    │
  └── render_kpi_cards(sparkline_data) │
                                       ↓
                              st.metric(chart_data=[...])
```

## Testing Strategy

### Manual Testing

| Test Case | Expected Result |
|-----------|-----------------|
| Dashboard 로드 | KPI 카드에 스파크라인 표시 |
| 다크 모드 토글 | 테마 즉시 변경 |
| 창 크기 축소 | KPI 행 자동 줄바꿈 |
| 시스템 테마 변경 | Streamlit 테마 연동 |

### Verification

```bash
# Dashboard 실행
python -m streamlit run dashboard/app.py

# 확인 항목
# 1. KPI 스파크라인 표시
# 2. 다크/라이트 모드 전환
# 3. 반응형 레이아웃
```

## Files to Modify

| File | Action | Lines Changed |
|------|--------|---------------|
| `dashboard/components/kpi_cards.py` | Modify | ~50 |
| `dashboard/components/theme.py` | Simplify | ~100 |
| `.streamlit/config.toml` | Create | ~30 |
| `dashboard/app.py` | Minor update | ~5 |

## Rollback Plan

문제 발생 시 Git revert로 이전 버전 복구

## References

- [st.metric sparklines](https://docs.streamlit.io/develop/api-reference/data/st.metric)
- [st.container horizontal](https://docs.streamlit.io/develop/api-reference/layout/st.container)
- [Theming](https://docs.streamlit.io/develop/concepts/configuration/theming)
- [st.context.theme](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.context)
