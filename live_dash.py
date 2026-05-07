import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
from datetime import datetime, timedelta


st.set_page_config(
    page_title="Stackly Website Gap Analysis Dashboard",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Syne', sans-serif;
    }

    .main { background-color: #0d0f1a; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1a1d2e 0%, #22263a 100%);
        border: 1px solid #2e3350;
        border-radius: 16px;
        padding: 22px 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }
    .kpi-card.red::before   { background: linear-gradient(90deg, #ff4d6d, #c9184a); }
    .kpi-card.green::before { background: linear-gradient(90deg, #06d6a0, #0cb87b); }
    .kpi-card.blue::before  { background: linear-gradient(90deg, #4895ef, #4cc9f0); }
    .kpi-card.amber::before { background: linear-gradient(90deg, #f9c74f, #f3722c); }
    .kpi-card.purple::before{ background: linear-gradient(90deg, #7b2d8b, #c77dff); }

    .kpi-number {
        font-family: 'Syne', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        color: #e8eaf6;
        line-height: 1;
        margin-bottom: 4px;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: #8b92b5;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 500;
    }
    .kpi-delta {
        font-size: 0.75rem;
        margin-top: 8px;
        padding: 2px 10px;
        border-radius: 20px;
        display: inline-block;
    }
    .kpi-delta.bad  { background: rgba(255,77,109,0.15); color: #ff4d6d; }
    .kpi-delta.good { background: rgba(6,214,160,0.15);  color: #06d6a0; }
    .kpi-delta.warn { background: rgba(249,199,79,0.15); color: #f9c74f; }

    /* Section headers */
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #c5cae9;
        margin-bottom: 4px;
        letter-spacing: 0.3px;
    }
    .section-sub {
        font-size: 0.78rem;
        color: #5c6080;
        margin-bottom: 16px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #10121f;
        border-right: 1px solid #1e2133;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label { color: #8b92b5 !important; }

    /* Divider */
    hr { border-color: #1e2133; }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-critical { background: rgba(255,77,109,0.18); color: #ff4d6d; }
    .badge-high     { background: rgba(249,199,79,0.18); color: #f9c74f; }
    .badge-medium   { background: rgba(72,149,239,0.18); color: #4895ef; }
    .badge-low      { background: rgba(6,214,160,0.18);  color: #06d6a0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────
COLORS = {
    "tech":      "#4895ef",
    "affiliate": "#c77dff",
    "arch":      "#06d6a0",
    "critical":  "#ff4d6d",
    "high":      "#f9c74f",
    "medium":    "#4895ef",
    "low":       "#06d6a0",
    "bg":        "#0d0f1a",
    "card":      "#1a1d2e",
    "border":    "#2e3350",
    "text":      "#c5cae9",
    "muted":     "#5c6080",
}

def hex_to_rgba(hex_color, alpha=0.15):
    """Convert #rrggbb to rgba(r,g,b,alpha)"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

PLOTLY_THEME = dict(
    plot_bgcolor="#0d0f1a",
    paper_bgcolor="#0d0f1a",
    font_color="#c5cae9",
    font_family="DM Sans",
    title_font_family="Syne",
    colorway=[COLORS["tech"], COLORS["affiliate"], COLORS["arch"],
              COLORS["critical"], COLORS["high"], "#f77f00"],
)

SITES = ["Tech (Tecko)", "Affiliate (STACKLY)", "Architecture"]
SITE_SHORT = ["Tech", "Affiliate", "Arch"]

# ─────────────────────────────────────────────
# SAMPLE DATA
# ─────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

# --- Scorecard per site per dimension (0-100) ---
score_data = pd.DataFrame({
    "Site":      SITES * 5,
    "Dimension": (["Product Quality"] * 3 + ["Functionality & UX"] * 3 +
                  ["Support & Updates"] * 3 + ["Marketplace Experience"] * 3 +
                  ["Technical Performance"] * 3),
    "Score": [55, 70, 72,   # Product Quality
              52, 55, 75,   # Functionality & UX
              25, 22, 30,   # Support & Updates
              58, 60, 78,   # Marketplace Experience
              42, 60, 58],  # Technical Performance
    "Max": [100]*15,
})
score_data["Gap"] = score_data["Max"] - score_data["Score"]

# --- Issues count per site ---
issues_data = pd.DataFrame({
    "Site": SITES,
    "Dead Links":         [12, 9, 6],
    "Broken Forms":       [3, 0, 2],
    "Missing Pages":      [5, 4, 2],
    "SEO Gaps":           [7, 5, 4],
    "JS Errors":          [1, 0, 2],
    "Accessibility Gaps": [6, 4, 3],
})

# --- Weekly fix progress (12 weeks) ---
weeks = [f"W{i}" for i in range(1, 13)]
progress_data = pd.DataFrame({
    "Week": weeks,
    "Tech Issues Fixed":       [2, 4, 6, 8, 11, 14, 17, 20, 23, 26, 28, 30],
    "Affiliate Issues Fixed":  [1, 3, 5, 7, 9,  12, 14, 16, 18, 20, 21, 22],
    "Arch Issues Fixed":       [1, 2, 4, 6, 8,  10, 12, 13, 14, 15, 16, 17],
    "Tech Remaining":          [32, 30, 28, 26, 23, 20, 17, 14, 11,  8,  6,  4],
    "Affiliate Remaining":     [24, 23, 21, 19, 17, 14, 12, 10,  8,  6,  5,  4],
    "Arch Remaining":          [18, 17, 15, 13, 11,  9,  7,  6,  5,  4,  3,  2],
})

# --- PageSpeed monthly trend ---
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
pagespeed_data = pd.DataFrame({
    "Month": months,
    "Tech Desktop":       [48, 52, 54, 57, 60, 64, 68, 72, 76, 80, 85, 88],
    "Tech Mobile":        [38, 42, 44, 47, 50, 54, 58, 62, 66, 70, 75, 80],
    "Affiliate Desktop":  [60, 62, 64, 66, 68, 70, 72, 74, 76, 80, 84, 87],
    "Affiliate Mobile":   [52, 54, 56, 58, 60, 63, 66, 70, 73, 77, 81, 85],
    "Arch Desktop":       [55, 57, 59, 62, 65, 68, 71, 74, 78, 82, 86, 89],
    "Arch Mobile":        [44, 47, 50, 53, 56, 60, 63, 67, 71, 75, 79, 83],
    "Target":             [85]*12,
})

# --- Heatmap: issue severity per site per category ---
categories = ["404 Links", "Forms", "SEO", "A11y", "Perf.", "Docs", "JS", "Content"]
heatmap_values = np.array([
    [9, 8, 7, 6, 8, 9, 4, 6],   # Tech
    [7, 2, 5, 4, 6, 9, 2, 7],   # Affiliate
    [5, 6, 4, 3, 5, 9, 7, 4],   # Architecture
])

# --- Competitor comparison ---
comp_data = pd.DataFrame({
    "Competitor":  ["ThemeX Agency", "Linekon", "Mitech", "Arki", "Archeco", "Affiliaxe", "FinancePro", "Stackly Tech", "Stackly Affiliate", "Stackly Arch"],
    "Sales":       [8000, 4500, 12000, 3200, 2800, 1100, 900, 0, 0, 0],
    "Category":    ["Tech","Tech","Tech","Arch","Arch","Affiliate","Affiliate","Tech","Affiliate","Arch"],
    "Type":        ["Competitor"]*7 + ["Our Products"]*3,
    "Doc Score":   [85, 80, 90, 78, 75, 70, 65, 20, 15, 25],
    "Design Score":[80, 85, 75, 82, 70, 68, 60, 65, 70, 78],
})

# --- Revenue projections ---
rev_data = pd.DataFrame({
    "Scenario":     ["Conservative", "Moderate", "Optimistic"],
    "Min Revenue":  [5000, 15000, 50000],
    "Max Revenue":  [10000, 30000, 80000],
    "Sales Min":    [300, 900, 2400],
    "Sales Max":    [600, 1500, 4000],
})

# --- Priority action plan ---
action_data = pd.DataFrame({
    "Action":    ["Fix /404 links", "Repair counter JS", "Wire-up forms",
                  "Add documentation", "Connect social links", "Fix logo mismatch",
                  "PageSpeed audit", "ThemeForest descriptions", "Video demos", "Seed reviews"],
    "Priority":  ["P0","P0","P0","P1","P1","P1","P2","P2","P2","P3"],
    "Site":      ["All","Architecture","Tech, Arch","All","All","Tech","All","All","All","All"],
    "Week":      [1, 1, 1, 2, 1, 1, 2, 3, 3, 4],
    "Status":    ["Pending","Pending","Pending","Not Started","Pending","Pending","Not Started","Not Started","Not Started","Not Started"],
    "Impact":    [10, 8, 9, 7, 6, 5, 8, 7, 8, 6],
})

# --- Monthly visitor + conversion funnel (sample) ---
funnel_data = pd.DataFrame({
    "Stage":      ["Site Visitors", "Preview Clicked", "Demo Explored", "Purchase Page", "Completed Sale"],
    "Tech":       [10000, 4200, 1800, 650, 180],
    "Affiliate":  [8000,  3600, 1600, 600, 170],
    "Arch":       [6000,  2800, 1400, 500, 150],
})

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧩 Gap Analysis")
    st.markdown("<div style='color:#5c6080;font-size:0.78rem;margin-bottom:20px;'>Stackly Websites — ThemeForest Readiness</div>", unsafe_allow_html=True)

    view = st.radio("📌 Dashboard View", [
        "🏠 Executive Overview",
        "🔍 Site Deep Dive",
        "📈 Performance Trends",
        "🏆 Competitor Analysis",
        "💰 Revenue Projections",
        "📋 Action Plan",
    ])

    st.markdown("---")
    site_filter = st.multiselect("Filter by Site", SITES, default=SITES)
    st.markdown("---")
    st.markdown("<div style='color:#5c6080;font-size:0.72rem;'>Report Date: May 2026</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#5c6080;font-size:0.72rem;'>Prepared for: Stackly Team</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:8px;">
  <span style="font-family:'Syne',sans-serif;font-size:1.9rem;font-weight:800;color:#e8eaf6;">
    Stackly Website Gap Analysis
  </span>
  <span style="background:rgba(255,77,109,0.18);color:#ff4d6d;font-size:0.72rem;font-weight:700;
        padding:3px 10px;border-radius:20px;margin-left:12px;vertical-align:middle;
        letter-spacing:1px;">LIVE DASHBOARD</span>
</div>
<div style="color:#5c6080;font-size:0.85rem;margin-bottom:28px;">
  ThemeForest marketplace readiness tracker across 3 Stackly-branded websites
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
# VIEW: EXECUTIVE OVERVIEW
# ═══════════════════════════════════════════
if view == "🏠 Executive Overview":

    # ── KPI Row ──────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown("""
        <div class="kpi-card red">
            <div class="kpi-number">47</div>
            <div class="kpi-label">Total Critical Issues</div>
            <div class="kpi-delta bad">🔴 Across 3 sites</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="kpi-card amber">
            <div class="kpi-number">54%</div>
            <div class="kpi-label">Avg Readiness Score</div>
            <div class="kpi-delta warn">⚠️ Target: 85%+</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="kpi-card blue">
            <div class="kpi-number">3</div>
            <div class="kpi-label">Sites Under Review</div>
            <div class="kpi-delta warn">📋 Pre-submission</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="kpi-card purple">
            <div class="kpi-number">$30K</div>
            <div class="kpi-label">Moderate Rev. Target</div>
            <div class="kpi-delta good">📈 6-Month Projection</div>
        </div>""", unsafe_allow_html=True)

    with c5:
        st.markdown("""
        <div class="kpi-card green">
            <div class="kpi-number">0</div>
            <div class="kpi-label">ThemeForest-Ready</div>
            <div class="kpi-delta bad">❌ None approved yet</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Radar + Stacked Bar ───────────
    col_left, col_right = st.columns([1.1, 1])

    with col_left:
        st.markdown('<div class="section-title">Readiness Radar — All Dimensions</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Each spoke = a ThemeForest quality dimension (score out of 100)</div>', unsafe_allow_html=True)

        dims = score_data["Dimension"].unique().tolist()
        fig_radar = go.Figure()

        site_colors = [COLORS["tech"], COLORS["affiliate"], COLORS["arch"]]
        for i, site in enumerate(SITES):
            vals = score_data[score_data["Site"] == site]["Score"].tolist()
            vals += [vals[0]]
            dims_loop = dims + [dims[0]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=dims_loop, fill='toself',
                name=SITE_SHORT[i],
                line=dict(color=site_colors[i], width=2),
                fillcolor=hex_to_rgba(site_colors[i], 0.15),
                opacity=0.9,
            ))

        fig_radar.update_layout(
            **PLOTLY_THEME,
            polar=dict(
                radialaxis=dict(range=[0, 100], tickfont=dict(size=9, color="#5c6080"),
                                gridcolor="#1e2133", linecolor="#2e3350"),
                angularaxis=dict(tickfont=dict(size=10), linecolor="#2e3350", gridcolor="#1e2133"),
                bgcolor="#0d0f1a",
            ),
            legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center",
                        font=dict(color="#8b92b5")),
            height=380, margin=dict(t=20, b=40, l=40, r=40),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-title">Issues Breakdown by Type</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Stacked count of identified gaps per category</div>', unsafe_allow_html=True)

        issue_cols = ["Dead Links","Broken Forms","Missing Pages","SEO Gaps","JS Errors","Accessibility Gaps"]
        fig_stack = go.Figure()
        iss_colors = ["#ff4d6d","#f9c74f","#f77f00","#4895ef","#c77dff","#06d6a0"]

        for j, col in enumerate(issue_cols):
            fig_stack.add_trace(go.Bar(
                name=col,
                x=SITE_SHORT,
                y=issues_data[col],
                marker_color=iss_colors[j],
                marker_line_width=0,
            ))

        fig_stack.update_layout(
            **PLOTLY_THEME,
            barmode="stack",
            xaxis=dict(showgrid=False, linecolor="#2e3350"),
            yaxis=dict(gridcolor="#1e2133", linecolor="#2e3350"),
            legend=dict(orientation="v", x=1.01, y=0.5, font=dict(color="#8b92b5", size=10)),
            height=380, margin=dict(t=20, b=30, l=40, r=140),
        )
        st.plotly_chart(fig_stack, use_container_width=True)

    # ── Row 3: Heatmap + Pie ─────────────────
    col_h, col_p = st.columns([1.4, 1])

    with col_h:
        st.markdown('<div class="section-title">Issue Severity Heatmap</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Severity score (1-10) per site × issue category</div>', unsafe_allow_html=True)

        fig_heat = go.Figure(go.Heatmap(
            z=heatmap_values,
            x=categories,
            y=SITE_SHORT,
            colorscale=[
                [0.0, "#0d3b66"], [0.3, "#1a5276"], [0.5, "#f9c74f"],
                [0.75, "#f77f00"], [1.0, "#ff4d6d"]
            ],
            showscale=True,
            colorbar=dict(
                title=dict(text="Severity", font=dict(color="#8b92b5")),
                tickfont=dict(color="#8b92b5"), thickness=10,
            ),
            text=heatmap_values,
            texttemplate="%{text}",
            textfont=dict(size=13, color="white"),
        ))
        fig_heat.update_layout(
            **PLOTLY_THEME,
            height=260,
            margin=dict(t=10, b=30, l=60, r=60),
            xaxis=dict(tickfont=dict(size=10)),
            yaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_p:
        st.markdown('<div class="section-title">Issues by Priority</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Distribution across P0 → P3 tiers</div>', unsafe_allow_html=True)

        fig_pie = go.Figure(go.Pie(
            labels=["P0 – Critical", "P1 – High", "P2 – Medium", "P3 – Low"],
            values=[3, 3, 3, 2],
            hole=0.55,
            marker=dict(colors=[COLORS["critical"], COLORS["high"], COLORS["medium"], COLORS["low"]],
                        line=dict(color="#0d0f1a", width=2)),
            textfont=dict(size=11, color="white"),
            hovertemplate="%{label}: %{value} actions<extra></extra>",
        ))
        fig_pie.add_annotation(text="11<br><span style='font-size:10px'>Actions</span>",
                               x=0.5, y=0.5, showarrow=False,
                               font=dict(size=20, color="#e8eaf6", family="Syne"))
        fig_pie.update_layout(
            **PLOTLY_THEME,
            showlegend=True,
            legend=dict(orientation="v", font=dict(color="#8b92b5", size=10), x=1.0, y=0.5),
            height=260, margin=dict(t=10, b=10, l=10, r=100),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Row 4: Funnel ────────────────────────
    st.markdown('<div class="section-title">Conversion Funnel — Projected Monthly Traffic</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Estimated visitor → purchase journey per site after launch</div>', unsafe_allow_html=True)

    fig_funnel = go.Figure()
    funnel_colors = [COLORS["tech"], COLORS["affiliate"], COLORS["arch"]]
    for i, site in enumerate(["Tech", "Affiliate", "Arch"]):
        col_key = ["Tech","Affiliate","Arch"][i]
        fig_funnel.add_trace(go.Funnel(
            name=site,
            y=funnel_data["Stage"],
            x=funnel_data[col_key],
            marker=dict(color=funnel_colors[i]),
            textinfo="value+percent initial",
            textfont=dict(color="white", size=11),
        ))

    fig_funnel.update_layout(
        **PLOTLY_THEME,
        height=320, margin=dict(t=10, b=20, l=20, r=20),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center",
                    font=dict(color="#8b92b5")),
        funnelmode="overlay",
    )
    st.plotly_chart(fig_funnel, use_container_width=True)


# ═══════════════════════════════════════════
# VIEW: SITE DEEP DIVE
# ═══════════════════════════════════════════
elif view == "🔍 Site Deep Dive":
    site_sel = st.selectbox("Select Site", SITES)
    idx = SITES.index(site_sel)
    color = [COLORS["tech"], COLORS["affiliate"], COLORS["arch"]][idx]

    # KPIs for the selected site
    site_scores = score_data[score_data["Site"] == site_sel]
    avg_score = int(site_scores["Score"].mean())
    total_issues = int(issues_data[issues_data["Site"] == site_sel][
        ["Dead Links","Broken Forms","Missing Pages","SEO Gaps","JS Errors","Accessibility Gaps"]
    ].sum(axis=1) .values[0])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Avg Readiness", f"{avg_score}%", delta=f"{avg_score - 85}% vs target")
    k2.metric("Total Issues Found", total_issues)
    k3.metric("Weakest Dimension", site_scores.loc[site_scores["Score"].idxmin(), "Dimension"],
              delta=f"{site_scores['Score'].min()} / 100")
    k4.metric("Strongest Dimension", site_scores.loc[site_scores["Score"].idxmax(), "Dimension"],
              delta=f"{site_scores['Score'].max()} / 100")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Dimension Scores</div>', unsafe_allow_html=True)
        fig_bar = go.Figure(go.Bar(
            x=site_scores["Score"],
            y=site_scores["Dimension"],
            orientation='h',
            marker=dict(
                color=site_scores["Score"],
                colorscale=[[0, "#ff4d6d"],[0.5, "#f9c74f"],[1, "#06d6a0"]],
                showscale=False,
            ),
            text=[f"{s}/100" for s in site_scores["Score"]],
            textposition="outside",
            textfont=dict(color="#c5cae9", size=11),
        ))
        fig_bar.add_vline(x=85, line_dash="dot", line_color="#5c6080",
                          annotation_text="Target (85)", annotation_font_color="#5c6080")
        fig_bar.update_layout(
            **PLOTLY_THEME,
            xaxis=dict(range=[0, 110], showgrid=True, gridcolor="#1e2133"),
            yaxis=dict(showgrid=False),
            height=320, margin=dict(t=10, b=20, l=10, r=60),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Issue Breakdown</div>', unsafe_allow_html=True)
        iss_row = issues_data[issues_data["Site"] == site_sel].iloc[0]
        iss_labels = ["Dead Links","Broken Forms","Missing Pages","SEO Gaps","JS Errors","Accessibility Gaps"]
        iss_vals = [iss_row[c] for c in iss_labels]

        fig_iss = go.Figure(go.Pie(
            labels=iss_labels, values=iss_vals, hole=0.5,
            marker=dict(colors=["#ff4d6d","#f9c74f","#f77f00","#4895ef","#c77dff","#06d6a0"],
                        line=dict(color="#0d0f1a", width=2)),
            textfont=dict(size=10, color="white"),
        ))
        fig_iss.add_annotation(text=f"{sum(iss_vals)}<br>Issues", x=0.5, y=0.5,
                               showarrow=False, font=dict(size=18, color="#e8eaf6", family="Syne"))
        fig_iss.update_layout(
            **PLOTLY_THEME,
            showlegend=True,
            legend=dict(font=dict(color="#8b92b5", size=9), x=1.0, y=0.5),
            height=320, margin=dict(t=10, b=10, l=10, r=100),
        )
        st.plotly_chart(fig_iss, use_container_width=True)

    # Gauge for overall readiness
    st.markdown('<div class="section-title">ThemeForest Readiness Gauge</div>', unsafe_allow_html=True)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_score,
        delta={"reference": 85, "suffix": "%"},
        number={"suffix": "%", "font": {"size": 40, "color": "#e8eaf6", "family": "Syne"}},
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(color="#5c6080")),
            bar=dict(color=color),
            bgcolor="#1a1d2e",
            bordercolor="#2e3350",
            steps=[
                dict(range=[0, 50], color="#ff4d6d22"),
                dict(range=[50, 75], color="#f9c74f22"),
                dict(range=[75, 100], color="#06d6a022"),
            ],
            threshold=dict(line=dict(color="#06d6a0", width=3), thickness=0.8, value=85),
        ),
    ))
    fig_gauge.update_layout(
        **PLOTLY_THEME, height=280, margin=dict(t=20, b=20, l=40, r=40),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)


# ═══════════════════════════════════════════
# VIEW: PERFORMANCE TRENDS
# ═══════════════════════════════════════════
elif view == "📈 Performance Trends":

    st.markdown('<div class="section-title">PageSpeed Score Trend (Monthly)</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Simulated improvement trajectory — target 85+ mobile score</div>', unsafe_allow_html=True)

    device = st.radio("Device", ["Desktop", "Mobile"], horizontal=True)

    fig_speed = go.Figure()
    for site, col_suffix, color in [("Tech", "Tech", COLORS["tech"]),
                                     ("Affiliate", "Affiliate", COLORS["affiliate"]),
                                     ("Arch", "Arch", COLORS["arch"])]:
        fig_speed.add_trace(go.Scatter(
            x=pagespeed_data["Month"], y=pagespeed_data[f"{col_suffix} {device}"],
            name=site, line=dict(color=color, width=2.5),
            mode="lines+markers", marker=dict(size=6),
        ))

    fig_speed.add_trace(go.Scatter(
        x=pagespeed_data["Month"], y=pagespeed_data["Target"],
        name="Target (85)", line=dict(color="#5c6080", dash="dot", width=1.5),
        mode="lines",
    ))
    fig_speed.update_layout(
        **PLOTLY_THEME,
        xaxis=dict(showgrid=False, linecolor="#2e3350"),
        yaxis=dict(range=[30, 105], gridcolor="#1e2133", linecolor="#2e3350"),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center",
                    font=dict(color="#8b92b5")),
        height=360, margin=dict(t=10, b=40, l=40, r=20),
    )
    st.plotly_chart(fig_speed, use_container_width=True)

    # Issue fix progress line
    st.markdown('<div class="section-title">Issues Fixed — Weekly Progress</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cumulative count of resolved issues per site over 12 weeks</div>', unsafe_allow_html=True)

    fig_prog = make_subplots(rows=1, cols=2, subplot_titles=("Issues Fixed (Cumulative)", "Issues Remaining"))

    for site, col, color in [("Tech", "Tech Issues Fixed", COLORS["tech"]),
                               ("Affiliate", "Affiliate Issues Fixed", COLORS["affiliate"]),
                               ("Arch", "Arch Issues Fixed", COLORS["arch"])]:
        fig_prog.add_trace(go.Scatter(
            x=progress_data["Week"], y=progress_data[col],
            name=site, line=dict(color=color, width=2),
            fill='tozeroy', fillcolor=hex_to_rgba(color, 0.08),
        ), row=1, col=1)

    for site, col, color in [("Tech", "Tech Remaining", COLORS["tech"]),
                               ("Affiliate", "Affiliate Remaining", COLORS["affiliate"]),
                               ("Arch", "Arch Remaining", COLORS["arch"])]:
        fig_prog.add_trace(go.Scatter(
            x=progress_data["Week"], y=progress_data[col],
            name=site, line=dict(color=color, width=2, dash="dot"),
            showlegend=False,
        ), row=1, col=2)

    fig_prog.update_layout(
        **PLOTLY_THEME,
        height=340, margin=dict(t=40, b=30, l=40, r=40),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(color="#8b92b5")),
    )
    fig_prog.update_xaxes(showgrid=False, linecolor="#2e3350")
    fig_prog.update_yaxes(gridcolor="#1e2133", linecolor="#2e3350")
    st.plotly_chart(fig_prog, use_container_width=True)

    # Core Web Vitals table
    st.markdown('<div class="section-title">Core Web Vitals Snapshot</div>', unsafe_allow_html=True)
    cwv = pd.DataFrame({
        "Site":       SITES,
        "LCP (s)":    [3.8, 3.1, 3.4],
        "FID (ms)":   [145, 110, 130],
        "CLS":        [0.18, 0.14, 0.16],
        "LCP Status": ["❌ Fail", "❌ Fail", "❌ Fail"],
        "FID Status": ["❌ Fail", "⚠️ Warn", "❌ Fail"],
        "CLS Status": ["❌ Fail", "❌ Fail", "❌ Fail"],
    })
    st.dataframe(cwv, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════
# VIEW: COMPETITOR ANALYSIS
# ═══════════════════════════════════════════
elif view == "🏆 Competitor Analysis":

    st.markdown('<div class="section-title">Sales — Competitors vs Stackly Products</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">ThemeForest lifetime estimated sales (Stackly = 0 pre-launch)</div>', unsafe_allow_html=True)

    fig_comp = px.bar(
        comp_data.sort_values("Sales", ascending=True),
        x="Sales", y="Competitor", orientation='h',
        color="Type",
        color_discrete_map={"Competitor": COLORS["muted"], "Our Products": COLORS["arch"]},
        text="Sales",
    )
    fig_comp.update_traces(textposition="outside", textfont=dict(color="#c5cae9"))
    fig_comp.update_layout(
        **PLOTLY_THEME,
        xaxis=dict(showgrid=True, gridcolor="#1e2133"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(color="#8b92b5")),
        height=420, margin=dict(t=10, b=40, l=10, r=60),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Scatter: Design vs Doc score
    st.markdown('<div class="section-title">Design Quality vs Documentation Score</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Bubble size = sales volume. Stackly products highlighted in green.</div>', unsafe_allow_html=True)

    fig_scat = px.scatter(
        comp_data, x="Design Score", y="Doc Score",
        color="Type", size=[max(s, 300) for s in comp_data["Sales"]],
        text="Competitor",
        color_discrete_map={"Competitor": COLORS["tech"], "Our Products": COLORS["arch"]},
        hover_data={"Sales": True},
    )
    fig_scat.update_traces(textposition="top center", textfont=dict(size=9, color="#c5cae9"))
    fig_scat.update_layout(
        **PLOTLY_THEME,
        xaxis=dict(gridcolor="#1e2133", range=[55, 100]),
        yaxis=dict(gridcolor="#1e2133", range=[10, 100]),
        legend=dict(font=dict(color="#8b92b5"), x=0, y=1),
        height=400, margin=dict(t=10, b=40, l=40, r=20),
    )
    st.plotly_chart(fig_scat, use_container_width=True)

    # Threat level pie
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">Competitor Threat Distribution</div>', unsafe_allow_html=True)
        fig_threat = go.Figure(go.Pie(
            labels=["High Threat", "Medium Threat"],
            values=[3, 4], hole=0.5,
            marker=dict(colors=[COLORS["critical"], COLORS["high"]],
                        line=dict(color="#0d0f1a", width=2)),
        ))
        fig_threat.update_layout(**PLOTLY_THEME, height=260, margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig_threat, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Sales by Category</div>', unsafe_allow_html=True)
        cat_sales = comp_data.groupby("Category")["Sales"].sum().reset_index()
        fig_cat = go.Figure(go.Bar(
            x=cat_sales["Category"], y=cat_sales["Sales"],
            marker_color=[COLORS["tech"], COLORS["affiliate"], COLORS["arch"]],
            text=cat_sales["Sales"], textposition="outside",
            textfont=dict(color="#c5cae9"),
        ))
        fig_cat.update_layout(
            **PLOTLY_THEME,
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1e2133"),
            height=260, margin=dict(t=10, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_cat, use_container_width=True)


# ═══════════════════════════════════════════
# VIEW: REVENUE PROJECTIONS
# ═══════════════════════════════════════════
elif view == "💰 Revenue Projections":

    st.markdown('<div class="section-title">Revenue Scenarios — First 6 Months Post-Launch</div>', unsafe_allow_html=True)

    # Range bar chart
    fig_rev = go.Figure()
    colors_rev = [COLORS["medium"], COLORS["high"], COLORS["arch"]]
    for i, row in rev_data.iterrows():
        fig_rev.add_trace(go.Bar(
            name=row["Scenario"],
            x=[row["Scenario"]],
            y=[row["Max Revenue"]],
            base=[row["Min Revenue"]],
            marker=dict(color=colors_rev[i], opacity=0.85),
            text=f'${row["Min Revenue"]:,} – ${row["Max Revenue"]:,}',
            textposition='outside',
            textfont=dict(color="#c5cae9"),
        ))

    fig_rev.update_layout(
        **PLOTLY_THEME,
        yaxis=dict(tickprefix="$", gridcolor="#1e2133"),
        xaxis=dict(showgrid=False),
        showlegend=False,
        height=360, margin=dict(t=40, b=20, l=60, r=40),
        title=dict(text="Revenue Range per Scenario (USD)", font=dict(size=13, color="#8b92b5")),
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    # Per-template pricing waterfall
    st.markdown('<div class="section-title">Pricing Strategy & Projected Sales Volume</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        price_data = pd.DataFrame({
            "Tier":  ["Single Template", "Bundle (3 Templates)"],
            "Price": [24, 54],
            "Color": [COLORS["tech"], COLORS["arch"]],
        })
        fig_price = go.Figure(go.Bar(
            x=price_data["Tier"], y=price_data["Price"],
            marker_color=price_data["Color"],
            text=[f"${p}" for p in price_data["Price"]],
            textposition="outside", textfont=dict(color="#c5cae9", size=13),
        ))
        fig_price.update_layout(
            **PLOTLY_THEME, height=280,
            yaxis=dict(tickprefix="$", gridcolor="#1e2133"),
            xaxis=dict(showgrid=False),
            margin=dict(t=20, b=20, l=40, r=20),
        )
        st.plotly_chart(fig_price, use_container_width=True)

    with col2:
        sales_df = pd.DataFrame({
            "Scenario":   ["Conservative", "Moderate", "Optimistic"],
            "Sales (Min)": rev_data["Sales Min"],
            "Sales (Max)": rev_data["Sales Max"],
        })
        fig_sales = go.Figure()
        fig_sales.add_trace(go.Bar(name="Min Sales", x=sales_df["Scenario"],
                                    y=sales_df["Sales (Min)"], marker_color=COLORS["muted"]))
        fig_sales.add_trace(go.Bar(name="Max Sales", x=sales_df["Scenario"],
                                    y=sales_df["Sales (Max)"], marker_color=COLORS["arch"]))
        fig_sales.update_layout(
            **PLOTLY_THEME, barmode="group", height=280,
            yaxis=dict(gridcolor="#1e2133"),
            xaxis=dict(showgrid=False),
            legend=dict(font=dict(color="#8b92b5"), orientation="h", y=-0.2),
            margin=dict(t=20, b=40, l=40, r=20),
        )
        st.plotly_chart(fig_sales, use_container_width=True)

    # Break-even timeline
    st.markdown('<div class="section-title">Break-Even Timeline Projection</div>', unsafe_allow_html=True)
    months_6 = ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"]
    cum_rev_mod = [3000, 8000, 14000, 19000, 25000, 30000]
    dev_cost    = [8000, 8000, 8000, 8000, 8000, 8000]

    fig_be = go.Figure()
    fig_be.add_trace(go.Scatter(x=months_6, y=cum_rev_mod, name="Cumulative Revenue (Moderate)",
                                 line=dict(color=COLORS["arch"], width=2.5), fill='tozeroy',
                                 fillcolor="rgba(6,214,160,0.08)"))
    fig_be.add_trace(go.Scatter(x=months_6, y=dev_cost, name="Dev Cost Baseline",
                                 line=dict(color=COLORS["critical"], dash="dot", width=2)))
    fig_be.update_layout(
        **PLOTLY_THEME, height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(tickprefix="$", gridcolor="#1e2133"),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center", font=dict(color="#8b92b5")),
        margin=dict(t=10, b=40, l=60, r=20),
    )
    st.plotly_chart(fig_be, use_container_width=True)


# ═══════════════════════════════════════════
# VIEW: ACTION PLAN
# ═══════════════════════════════════════════
elif view == "📋 Action Plan":

    st.markdown('<div class="section-title">Priority Action Timeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Gantt-style view of all remediation tasks</div>', unsafe_allow_html=True)

    # Gantt
    gantt_data = []
    week_start = datetime(2026, 5, 6)
    week_colors = {"P0": COLORS["critical"], "P1": COLORS["high"],
                   "P2": COLORS["medium"], "P3": COLORS["low"]}

    for _, row in action_data.iterrows():
        start = week_start + timedelta(weeks=row["Week"] - 1)
        end = start + timedelta(days=5)
        gantt_data.append(dict(
            Task=row["Action"], Start=start, Finish=end,
            Priority=row["Priority"], Color=week_colors[row["Priority"]],
        ))

    fig_gantt = go.Figure()
    for item in gantt_data:
        fig_gantt.add_trace(go.Bar(
            x=[(item["Finish"] - item["Start"]).days],
            y=[item["Task"]],
            base=[(item["Start"] - week_start).days],
            orientation='h',
            marker_color=item["Color"],
            name=item["Priority"],
            showlegend=False,
            text=item["Priority"],
            textposition="inside",
            textfont=dict(color="white", size=10),
        ))

    for p, c in week_colors.items():
        fig_gantt.add_trace(go.Bar(x=[0], y=[""], base=[0], orientation='h',
                                    marker_color=c, name=p, showlegend=True))

    fig_gantt.update_layout(
        **PLOTLY_THEME,
        barmode='overlay',
        xaxis=dict(title="Days from Start", showgrid=True, gridcolor="#1e2133"),
        yaxis=dict(showgrid=False, autorange="reversed"),
        legend=dict(title="Priority", orientation="h", y=-0.12, x=0.5, xanchor="center",
                    font=dict(color="#8b92b5")),
        height=420, margin=dict(t=10, b=50, l=20, r=20),
    )
    st.plotly_chart(fig_gantt, use_container_width=True)

    # Impact vs effort scatter
    st.markdown('<div class="section-title">Impact vs Priority Weight</div>', unsafe_allow_html=True)

    fig_imp = px.scatter(
        action_data, x="Week", y="Impact",
        color="Priority", text="Action", size=[10]*len(action_data),
        color_discrete_map={"P0": COLORS["critical"], "P1": COLORS["high"],
                             "P2": COLORS["medium"], "P3": COLORS["low"]},
    )
    fig_imp.update_traces(textposition="top center", textfont=dict(size=9, color="#c5cae9"))
    fig_imp.update_layout(
        **PLOTLY_THEME,
        xaxis=dict(title="Delivery Week", showgrid=False, dtick=1),
        yaxis=dict(title="Impact Score (1-10)", gridcolor="#1e2133"),
        legend=dict(font=dict(color="#8b92b5")),
        height=380, margin=dict(t=10, b=40, l=40, r=20),
    )
    st.plotly_chart(fig_imp, use_container_width=True)

    # Table summary
    st.markdown('<div class="section-title">Full Action Register</div>', unsafe_allow_html=True)
    styled_df = action_data.copy()
    st.dataframe(styled_df, use_container_width=True, hide_index=True)



st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#2e3350;font-size:0.75rem;padding:8px 0;'>"
    "Stackly Gap Analysis Dashboard • Built with Streamlit & Plotly • May 2026"
    "</div>",
    unsafe_allow_html=True,
)