import streamlit as st
import pandas as pd
import altair as alt
from scanner import scan_universe

# ────────────────────────────
# Custom Altair Theme (Deep Cyan)
# ────────────────────────────
alt.themes.register('eh_dark', lambda: {
    "config": {
        "background": "hsl(199, 35%, 9%)",
        "view": {"stroke": "transparent"},
        "axis": {
            "domainColor": "#bfcad1",
            "gridColor": "hsl(199, 25%, 20%)",
            "labelColor": "#dfe5e8",
            "titleColor": "#dfe5e8",
        },
        "legend": {"labelColor": "#dfe5e8", "titleColor": "#dfe5e8"},
        "title": {"color": "#ffffff"},
    }
})
alt.themes.enable('eh_dark')

# ────────────────────────────
# Global Styling & Font
# ────────────────────────────
custom_css = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {
    --accent-color: hsl(172, 59%, 57%);
    --accent-hover: hsl(172, 59%, 65%);
    --bg-primary: hsl(199, 35%, 9%);
    --bg-secondary: hsl(199, 35%, 12%);
    --bg-tertiary: hsl(199, 35%, 16%);
    --text-color: hsl(199, 21%, 90%);
    --text-muted: hsl(199, 21%, 70%);
    --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Ubuntu, 'Helvetica Neue', sans-serif;
    
}

/* Target Base Web's active tab indicator */
.Tab[aria-selected="true"]::after,
.Tabs .Tab[aria-selected="true"]::after,
[data-baseweb="tab"] [aria-selected="true"]::after {
  background-color: hsl(172, 59%, 57%) !important;
  height: 0.125rem !important;
  border-radius: 1px !important;
}

/* Also override any inline styles */
* {
  --colors-negative: hsl(172, 59%, 57%) !important;
  --colors-negative50: hsl(172, 59%, 57%) !important;
  /* ... repeat or use a loop in SCSS */
}

/* Global App Background */
html, body, [class*="stApp"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-color) !important;
    font-family: var(--font-primary) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: hsl(201, 21%, 13%);;
    color: var(--text-color) !important;
}

/* Headings */
h1, h2, h3, h4, h5 {
    color: var(--text-color) !important;
}

/* Buttons */
.stButton button {
    background-color: var(--accent-color) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: var(--font-primary) !important;
    font-weight: 500 !important;
}
.stButton button:hover {
    background-color: var(--accent-hover) !important;
}

/* Tabs */
[data-testid="stTabs"] {
    background-color: transparent;
    border-bottom: 1px solid var(--bg-tertiary);
}
[data-testid="stTab"] > div > p {
    color: var(--text-color) !important;
    font-family: var(--font-primary);
    font-weight: 500;
    letter-spacing: -0.01em;
}
[data-testid="stTab"]:has(div[aria-selected="true"]) > div > p {
    color: var(--accent-color) !important;
}
[data-testid="stTab"]:has(div[aria-selected="true"]) {
    border-bottom: 2px solid var(--accent-color) !important;
}
[data-testid="stTab"]:hover > div > p {
    color: var(--accent-hover) !important;
}

/* ─────────── clean cyan slider ─────────── */
[data-baseweb="slider"] {
    color: #ffffff !important;
}

/* filled part of the slider track */
[data-baseweb="slider"] > div > div:nth-child(2) {
    background-color: hsl(172, 59%, 57%) !important;
}

/* unfilled part */
[data-baseweb="slider"] > div > div:nth-child(1) {
    background-color: hsl(199, 25%, 25%) !important;
}

/* slider knob */
[data-baseweb="slider"] [role="slider"] {
    background-color: hsl(172, 59%, 57%) !important;
    box-shadow: 0 0 0 2px hsl(172, 59%, 57%) !important;
}

/* hover state */
[data-baseweb="slider"] [role="slider"]:hover {
    background-color: hsl(172, 59%, 65%) !important;
    box-shadow: 0 0 0 3px hsl(172, 59%, 65%) !important;
}

/* all numbers and labels */
.stSlider label,
.stSlider span,
[data-testid="stSliderValue"],
[data-testid="stSliderThumbValue"],
[data-testid="stTickBarMin"],
[data-testid="stTickBarMax"] {
    color: #ffffff !important;
    font-weight: 500 !important;
}

/* ticks and track cleanup */
[data-testid="stSliderTickBar"] {
    background-color: transparent !important;
}

[data-baseweb="tab-highlight"] {
    background-color: hsl(172, 59%, 57%) !important;
}

[data-baseweb="slider"] [role="slider"] {
    background-color: hsl(172, 59%, 57%) !important;
}

[data-testid="stButton"] button[kind="secondary"] {
        color: var(--bg-primary) !important;          /* your text color */
        background-color: var(--accent-color) !important;  /* button bg if you want */
        font-weight: 600 !important;
    }

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)





# ────────────────────────────
# App Setup
# ────────────────────────────
st.set_page_config(page_title="EventHorizon", layout="wide")
st.title("Event Horizon v1.0")
st.caption("Binance USDT Spot · 4h Candles · Composite + Volatility + RS Metrics")

refresh = st.button("Refresh data")

if refresh or "data" not in st.session_state:
    with st.spinner("Scanning market..."):
        df = scan_universe()
        st.session_state["data"] = df

df = st.session_state.get("data")

if df is None or df.empty:
    st.error("No data. Try refresh again.")
    st.stop()

# ────────────────────────────
# Column Renaming (for clarity)
# ────────────────────────────
df_display = df.rename(columns={
    "symbol": "Symbol",
    "last_price": "Last Price",
    "pct_change_%": "Change (%)",
    "breakout_%": "Breakout (%)",
    "vol_z": "Volatility Z-Score",
    "vol_breakout": "Volatility Breakout",
    "relative_strength": "Relative Strength",
    "score": "Composite Score",
})

# ────────────────────────────
# Sidebar Filters
# ────────────────────────────
st.sidebar.header("Filters")
min_score = st.sidebar.slider("Min composite score", -20.0, 40.0, 5.0, 0.5)
min_breakout = st.sidebar.slider("Min breakout %", -10.0, 30.0, 0.0, 0.5)
top_n = st.sidebar.slider("Show top N", 10, 150, 60, 5)

filtered = df_display[
    (df_display["Composite Score"] >= min_score)
    & (df_display["Breakout (%)"] >= min_breakout)
].head(top_n)

# ────────────────────────────
# Tooltip Info (ℹ️ icons)
# ────────────────────────────
tooltips = {
    "Last Price": "Most recent candle close price.",
    "Change (%)": "Percent change over the 24h lookback window.",
    "Breakout (%)": "Distance from the most recent 24h high — momentum signal.",
    "Volatility Z-Score": "How unusual current volatility is compared to average.",
    "Volatility Breakout": "Change in volatility trend relative to average.",
    "Relative Strength": "Price deviation vs its 24h mean.",
    "Composite Score": "Weighted score combining breakout, change, and volatility.",
}

# ────────────────────────────
# Tab Layout
# ────────────────────────────
tab1, tab2, tab3 = st.tabs(["Overview", "Scatterplots", "Sectors"])

# ────────────────────────
# TAB 1 – RANKED TABLE + CHARTS (WITH REAL TOOLTIP ICONS)
# ────────────────────────
with tab1:
    st.subheader("Ranked Table")

    st.dataframe(
        filtered,
        use_container_width=True,
        column_config={
            "Symbol": st.column_config.TextColumn(
                "Symbol", help="Trading pair on Binance (e.g. BTC/USDT)"
            ),
            "Last Price": st.column_config.NumberColumn(
                "Last Price", help="Latest closing price"
            ),
            "Change (%)": st.column_config.NumberColumn(
                "Change (%)", help="Percent change over last N candles"
            ),
            "Breakout (%)": st.column_config.NumberColumn(
                "Breakout (%)", help="Percent above recent local high"
            ),
            "Volatility Z-Score": st.column_config.NumberColumn(
                "Volatility Z-Score", help="Z-score of short-term volatility"
            ),
            "Volatility Breakout": st.column_config.NumberColumn(
                "Volatility Breakout", help="Z-score of volatility expansion"
            ),
            "Relative Strength": st.column_config.NumberColumn(
                "Relative Strength", help="Relative strength vs rolling mean"
            ),
            "Composite Score": st.column_config.NumberColumn(
                "Composite Score",
                help="Weighted composite of breakout, momentum, volatility, and RS",
            ),
        },
    )

    # ───────────────────────────────
    # Charts Section
    # ───────────────────────────────
    st.subheader("Breakout Rankings")

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        "Composite Score",
        "Volatility Breakout",
        "Relative Strength",
        "Volatility Z-Score",
    ]
    for col, metric in zip([col1, col2, col3, col4], metrics):
        top = df_display.sort_values(metric, ascending=False).head(20)
        chart = (
            alt.Chart(top)
            .mark_bar(color="hsl(172, 59%, 57%)")

            .encode(
                x=alt.X(metric, title=metric),
                y=alt.Y("Symbol", sort="-x"),
                tooltip=["Symbol", alt.Tooltip(metric, format=".2f")],
            )
            .properties(height=400)
        )
        col.altair_chart(chart, use_container_width=True)







with tab2:
    st.subheader("Scatterplots")

    scatter_pairs = [
        ("Change (%)", "Breakout (%)"),
        ("Volatility Z-Score", "Breakout (%)"),
        ("Volatility Breakout", "Relative Strength"),
        ("Relative Strength", "Composite Score"),
    ]

    for x, y in scatter_pairs:
        c = (
            alt.Chart(df_display)
            .mark_circle(size=60)
            .encode(
                x=x,
                y=y,
                color=alt.Color(
                    "Composite Score",
                    scale=alt.Scale(
                        domainMid=0,
                        range=[
                            "hsl(199, 60%, 10%)",   # deep navy base
                            "hsl(172, 85%, 55%)",   # electric cyan mid
                            "hsl(172, 100%, 72%)",  # glowing mint highlight
                        ],
                    ),
                    legend=alt.Legend(title="Composite Score"),
                ),
                tooltip=["Symbol", x, y],
            )
            .properties(
                title=f"{x} vs {y}",
                height=300,
                background="hsl(199, 35%, 9%)",
            )
        )
        st.altair_chart(c, use_container_width=True)


with tab3:
    st.subheader("Sector Analysis")

    try:
        sectors = pd.read_csv("sectors.csv")
        if "symbol" in sectors.columns:
            sectors.rename(columns={"symbol": "Symbol"}, inplace=True)

        merged = df_display.merge(sectors, on="Symbol", how="left")
        merged = merged.dropna(subset=["sector"])

        if merged.empty:
            st.warning("No symbols matched the sectors file.")
            st.stop()

        sector_scores = (
            merged.groupby("sector")["Composite Score"]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )

        if sector_scores.empty:
            st.warning("No sector scores to plot.")
            st.stop()

        # dynamic height
        rows = len(sector_scores)
        chart_height = rows * 35

        # define sort order explicitly
        sector_order = sector_scores["sector"].tolist()

        # split positives and negatives
        positive = sector_scores[sector_scores["Composite Score"] >= 0]
        negative = sector_scores[sector_scores["Composite Score"] < 0]

        base_y = alt.Y(
            "sector:N",
            sort=sector_order,  # explicit order
            title=None,
            axis=alt.Axis(
                labelLimit=500,
                labelFontSize=12,
                labelPadding=8,
                ticks=False,
                domain=False,
            ),
        )

        bars_pos = alt.Chart(positive).mark_bar(
            color="hsl(172, 59%, 57%)",
            cornerRadiusTopRight=4,
            cornerRadiusBottomRight=4,
        ).encode(
            x=alt.X("Composite Score:Q", title="Avg Composite Score"),
            y=base_y,
            tooltip=["sector", alt.Tooltip("Composite Score", format=".2f")],
        )

        bars_neg = alt.Chart(negative).mark_bar(
            color="hsl(172, 59%, 57%)",
            cornerRadiusTopLeft=4,
            cornerRadiusBottomLeft=4,
        ).encode(
            x=alt.X("Composite Score:Q", title="Avg Composite Score"),
            y=base_y,
            tooltip=["sector", alt.Tooltip("Composite Score", format=".2f")],
        )

        c = (bars_pos + bars_neg).properties(
            height=chart_height,
            background="hsl(199, 35%, 9%)",
            title=alt.TitleParams(
                text="Average Composite Score by Sector",
                anchor="start",
                fontSize=16,
                color="#e6e9eb",
            ),
        ).configure_axis(grid=False, labelColor="#e6e9eb", titleColor="#e6e9eb") \
         .configure_view(strokeWidth=0)

        st.altair_chart(c, use_container_width=True)
        st.caption(f"Showing **{rows}** sector{'' if rows == 1 else 's'}")

    except FileNotFoundError:
        st.error("`sectors.csv` not found in the app folder.")
        st.info(
            "Create a CSV with **Symbol** and **sector** columns, e.g.:\n"
            "```\n"
            "Symbol,sector\n"
            "BTCUSDT,Bluechip\n"
            "ETHUSDT,Bluechip\n"
            "SOLUSDT,Layer1\n"
            "```"
        )
    except Exception as e:
        st.exception(e)

