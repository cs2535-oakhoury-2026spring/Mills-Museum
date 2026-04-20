"""
Data Story Exhibit — Gradio Web App
====================================

Live interactive dashboard served via Gradio. This is the version that
runs inside the website (launched through the main Gradio app).

Note: This is independent of ``src/analysis/09_dashboard.py``, which
produces a standalone HTML file (``figures/dashboard.html``) meant to be
opened directly in a browser. Both visualize the same AAT dataset but
do not share code or output.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


DATA_PATH = Path("src/analysis/data_cache/aat_museum_subset.parquet")
FIGURES_DIR = Path("src/analysis/figures")
HERO_IMAGE = Path(__file__).resolve().parent.parent / "design" / "mills.jpg"
CENTURY_PATTERN = re.compile(r"(\d+)(?:st|nd|rd|th)\s+centur", re.IGNORECASE)
STOPWORDS = {"and", "of", "the", "for", "in", "with", "a", "an", "to", "or", "by", "on", "at", "as", "is"}
FONT_STACK = "'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

# Muted, harmonious palette — greens and warm tans, no jarring jumps
PALETTE = ["#f0c040", "#e8b616", "#d4a017", "#5b749a", "#6c85a8",
           "#8a9bb8", "#c4960e", "#4a6385", "#f5d060", "#b08c12", "#3b5170", "#ffd866"]

GH_REPO = "https://github.com/cs2535-oakhoury-2026spring/Mills-Museum"

CHART_LAYOUT = dict(
    margin=dict(l=24, r=24, t=40, b=24),
    paper_bgcolor="#0f1e36",
    plot_bgcolor="#0f1e36",
    font=dict(family=FONT_STACK, color="#f0e6d0", size=12),
)


def load_dataset() -> pd.DataFrame:
    """Load the parquet snapshot and add helper columns used by multiple charts."""
    dataframe = pd.read_parquet(DATA_PATH).copy()
    dataframe["variant_count"] = dataframe["variant_terms"].apply(len)
    dataframe["scope_len"] = dataframe["scope_note"].fillna("").str.len()
    return dataframe


def compute_tree_depths(dataframe: pd.DataFrame) -> pd.Series:
    """Measure how many parent links each term sits below its facet root."""
    parent_map = dict(zip(dataframe["subject_id"], dataframe["parent_id"]))
    memo: dict[int, int] = {}

    def get_depth(subject_id: int) -> int:
        # Cache previously solved nodes so repeated parent chains are cheap.
        if subject_id in memo:
            return memo[subject_id]
        parent_id = parent_map.get(subject_id)
        if parent_id is None or parent_id == subject_id or parent_id not in parent_map:
            memo[subject_id] = 0
            return 0
        depth = get_depth(parent_id) + 1
        memo[subject_id] = depth
        return depth

    return dataframe["subject_id"].apply(get_depth)


# ──────────────────────────────────────────────
# CHART BUILDERS
# ──────────────────────────────────────────────

def build_facet_river(df: pd.DataFrame) -> go.Figure:
    """Show how many terms belong to each top-level AAT hierarchy."""
    counts = df["hierarchy"].value_counts().reset_index()
    counts.columns = ["Facet", "Terms"]
    counts["Share"] = counts["Terms"] / counts["Terms"].sum()
    fig = px.bar(counts, x="Terms", y="Facet", orientation="h",
                 color="Share", color_continuous_scale=["#1a2d4a", "#d4a017", "#f0c040"])
    fig.update_layout(**CHART_LAYOUT, showlegend=False, coloraxis_showscale=False, height=380,
                      xaxis_title="", yaxis_title="",
                      title=dict(text="Term count by facet", font=dict(size=13)))
    fig.update_traces(texttemplate="%{x:,}", textposition="outside",
                      hovertemplate="<b>%{y}</b><br>%{x:,} terms<extra></extra>",
                      marker_line_width=0)
    return fig


def build_sunburst(df: pd.DataFrame) -> go.Figure:
    """Show the largest parent-term groupings inside each hierarchy."""
    top_parents = (df.groupby(["hierarchy", "parent_term"]).size().reset_index(name="count")
                   .sort_values("count", ascending=False).groupby("hierarchy").head(5))
    fig = px.sunburst(top_parents, path=["hierarchy", "parent_term"], values="count",
                      color="count", color_continuous_scale=["#1a2d4a", "#5b749a", "#d4a017", "#f0c040"])
    fig.update_layout(**CHART_LAYOUT, height=440, coloraxis_showscale=False,
                      title=dict(text="Taxonomy clusters — click to explore", font=dict(size=13)))
    fig.update_traces(textfont=dict(color="#f0e6d0"))
    return fig


def build_century_heatmap(df: pd.DataFrame) -> go.Figure:
    """Extract century references from scope notes and count them by hierarchy."""
    scope = df[df["scope_note"].notna()]
    facet_century: dict = defaultdict(lambda: Counter())
    for _, row in scope.iterrows():
        for m in CENTURY_PATTERN.finditer(row["scope_note"]):
            c = int(m.group(1))
            if 3 <= c <= 20:
                facet_century[row["hierarchy"]][c] += 1
    facet_order = df["hierarchy"].value_counts().index.tolist()
    centuries = list(range(3, 21))
    z = [[facet_century[f].get(c, 0) for c in centuries] for f in facet_order]
    fig = go.Figure(go.Heatmap(
        z=z, x=[f"{c}th" for c in centuries], y=facet_order,
        colorscale=[[0, "#0a1628"], [0.15, "#1a2d4a"], [0.4, "#5b749a"], [0.7, "#d4a017"], [1, "#f0c040"]],
        hovertemplate="%{y}<br>%{x} century: <b>%{z}</b><extra></extra>"))
    fig.update_layout(**CHART_LAYOUT, height=400, yaxis=dict(autorange="reversed"), xaxis=dict(side="top"),
                      title=dict(text="Century references across facets", font=dict(size=13)))
    return fig


def build_kw_century(df: pd.DataFrame) -> go.Figure:
    """Track common preferred-term words across the centuries named in scope notes."""
    scope = df[df["scope_note"].notna()]
    top_words = Counter()
    for t in df["preferred_term"].str.lower():
        top_words.update(w for w in t.split() if w not in STOPWORDS and len(w) > 2)
    centuries = list(range(3, 21))
    kw_century: dict = defaultdict(lambda: Counter())
    top_kws = [w for w, _ in top_words.most_common(40)]
    for _, row in scope.iterrows():
        cfound = [int(m.group(1)) for m in CENTURY_PATTERN.finditer(row["scope_note"]) if 3 <= int(m.group(1)) <= 20]
        if not cfound:
            continue
        tw = set(row["preferred_term"].lower().split())
        for kw in top_kws:
            if kw in tw:
                for c in cfound:
                    kw_century[kw][c] += 1
    ranked = [w for w in top_kws if sum(kw_century[w].values()) >= 5][:20]
    z = [[kw_century[w].get(c, 0) for c in centuries] for w in ranked]
    fig = go.Figure(go.Heatmap(
        z=z, x=[f"{c}th" for c in centuries], y=ranked,
        colorscale=[[0, "#0a1628"], [0.2, "#1a2d4a"], [0.5, "#c4960e"], [0.8, "#e8b616"], [1, "#f0c040"]],
        hovertemplate="<b>%{y}</b> in the %{x} century: %{z}<extra></extra>"))
    fig.update_layout(**CHART_LAYOUT, height=440, yaxis=dict(autorange="reversed"), xaxis=dict(side="top"),
                      title=dict(text="Keyword trends across centuries", font=dict(size=13)))
    return fig


def build_depth_violin(df: pd.DataFrame) -> go.Figure:
    """Visualize how deep each hierarchy tends to be in the taxonomy tree."""
    ddf = df.copy()
    ddf["tree_depth"] = compute_tree_depths(ddf)
    fig = px.violin(ddf, x="hierarchy", y="tree_depth", color="hierarchy",
                    category_orders={"hierarchy": df["hierarchy"].value_counts().index.tolist()},
                    color_discrete_sequence=["#f0c040", "#e8b616", "#d4a017", "#5b749a", "#6c85a8",
                                             "#8a9bb8", "#c4960e", "#4a6385", "#f5d060", "#b08c12", "#3b5170", "#ffd866"],
                    box=True, points=False)
    fig.update_layout(**CHART_LAYOUT, showlegend=False, height=400, xaxis_title="", yaxis_title="Depth",
                      xaxis=dict(tickangle=30, tickfont=dict(size=9)),
                      title=dict(text="Hierarchy depth per facet", font=dict(size=13)))
    return fig


def build_geo_area(df: pd.DataFrame) -> go.Figure:
    """Approximate geographic emphasis by matching regional words in scope notes."""
    scope = df[df["scope_note"].notna()]
    geo_pats = {
        "European": re.compile(r"\b(europe|european|french|italian|english|german|spanish|dutch|greek|roman|british)\b", re.I),
        "Asian": re.compile(r"\b(asia|asian|chinese|japanese|indian|korean|persian|thai)\b", re.I),
        "African": re.compile(r"\b(africa|african|egyptian|saharan)\b", re.I),
        "Americas": re.compile(r"\b(america|american|native american|mesoamerican|pre-columbian)\b", re.I),
        "Middle Eastern": re.compile(r"\b(middle east|islamic|ottoman|arab|mesopotamian)\b", re.I),
    }
    centuries = list(range(3, 21))
    geo_c: dict = defaultdict(lambda: Counter())
    for _, row in scope.iterrows():
        cfound = [int(m.group(1)) for m in CENTURY_PATTERN.finditer(row["scope_note"]) if 3 <= int(m.group(1)) <= 20]
        if not cfound:
            continue
        for region, pat in geo_pats.items():
            if pat.search(row["scope_note"]):
                for c in cfound:
                    geo_c[region][c] += 1
    rows = [{"Region": r, "Century": f"{c}th", "Mentions": geo_c[r].get(c, 0)} for r in geo_pats for c in centuries]
    fig = px.area(pd.DataFrame(rows), x="Century", y="Mentions", color="Region",
                  color_discrete_sequence=["#f0c040", "#e8b616", "#d4a017", "#5b749a", "#8a9bb8"])
    fig.update_layout(**CHART_LAYOUT, height=380, hovermode="x unified",
                      title=dict(text="Regional emphasis shifting over centuries", font=dict(size=13)))
    return fig


def build_scatter(df: pd.DataFrame) -> go.Figure:
    """Compare translation breadth against scope-note length for individual terms."""
    sampled = df[df["scope_len"] > 0].copy()
    if len(sampled) > 3000:
        # Sampling keeps the chart responsive without changing the overall shape too much.
        sampled = sampled.sample(3000, random_state=42)
    fig = px.scatter(sampled, x="variant_count", y="scope_len", color="hierarchy",
                     hover_name="preferred_term", opacity=0.55, color_discrete_sequence=PALETTE)
    fig.update_layout(**CHART_LAYOUT, height=400, legend_title_text="",
                      xaxis_title="Variant count", yaxis_title="Scope note length (chars)",
                      title=dict(text="Description richness vs. translation breadth", font=dict(size=13)))
    return fig


# ──────────────────────────────────────────────
# HTML BUILDERS
# ──────────────────────────────────────────────

def build_hero_html() -> str:
    return """
    <div class="hero-panel" role="banner">
        <p class="hero-eyebrow">Mills College Art Museum</p>
        <h1>Data Exhibit</h1>
        <p class="hero-sub">Exploring the Art &amp; Architecture Thesaurus through
        44,225 terms, 334K multilingual variants, and 18 centuries of material culture.</p>
    </div>
    """


def build_stat_strip(df: pd.DataFrame) -> str:
    """Build the top-line statistic cards shown near the top of the exhibit."""
    scope_pct = df["scope_note"].notna().mean() * 100
    multi = (df["variant_count"] >= 5).sum()

    items = [
        ("44,225", "Total terms", "Museum-ready AAT subset"),
        ("12", "Facets", "Conceptual neighborhoods"),
        (f"{scope_pct:.0f}%", "Described", "Have scope notes"),
        (f"{multi:,}", "Multilingual", "Carry 5+ translations"),
        ("1,127", "Ambiguous", "Shared across facets"),
        ("36%", "Objects", "Furnishings &amp; Equipment"),
    ]
    cards = "".join(
        f"<div class='s-card' role='figure' aria-label='{lbl}: {val}'>"
        f"<div class='s-num'>{val}</div>"
        f"<div class='s-label'>{lbl}</div>"
        f"<div class='s-detail'>{det}</div></div>"
        for val, lbl, det in items
    )
    return f"<div class='stat-strip' role='region' aria-label='Key statistics'>{cards}</div>"


def _panel_header(pill: str, title: str, callouts: list[tuple[str, str]], warm: bool = False) -> str:
    pill_cls = "pill warm" if warm else "pill"
    co_num_cls = "warm" if warm else ""
    cards = "".join(
        f"<div class='co' role='note'><span class='co-num {co_num_cls}'>{num}</span> {txt}</div>"
        for num, txt in callouts
    )
    return (
        f"<div class='ph' role='region' aria-label='{title}'>"
        f"<div class='ph-left'><span class='{pill_cls}'>{pill}</span><h2>{title}</h2></div>"
        f"<div class='ph-right'>{cards}</div></div>"
    )


def build_keyword_wall(df: pd.DataFrame) -> str:
    """Build a text-heavy card wall that surfaces vocabulary per hierarchy."""
    top_facets = df["hierarchy"].value_counts().head(6).index.tolist()
    cards = []
    for facet in top_facets:
        facet_terms = df.loc[df["hierarchy"] == facet, "preferred_term"].str.lower()
        words = Counter()
        for term in facet_terms:
            words.update(w for w in term.split() if w not in STOPWORDS and len(w) > 2)
        top6 = words.most_common(6)
        mx = top6[0][1] if top6 else 1
        tags = "".join(
            f"<span class='kt' style='opacity:{0.45 + 0.55 * c / mx:.2f}'>{w}</span>"
            for w, c in top6
        )
        count = len(df[df["hierarchy"] == facet])
        cards.append(
            f"<div class='kc' role='listitem'>"
            f"<div class='kc-head'><span class='kc-name'>{facet}</span>"
            f"<span class='kc-count'>{count:,}</span></div>"
            f"<div class='kc-tags'>{tags}</div></div>"
        )
    return f"<div class='kw' role='list' aria-label='Top keywords per facet'>{''.join(cards)}</div>"


def build_footer() -> str:
    gh_icon = (
        '<svg width="20" height="20" viewBox="0 0 16 16" fill="#3a3530" aria-hidden="true">'
        '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 '
        '5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-'
        '2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 '
        '1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-'
        '3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 '
        '2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 '
        '2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 '
        '3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 '
        '.21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'
    )
    return f"""
    <footer class="ef" role="contentinfo">
        <div class="ef-team">
            <span class="ef-course">CS 2535</span>
            <span class="ef-sep">·</span> Prof. Oakhoury
            <span class="ef-sep">·</span> Spring 2026
        </div>
        <div class="ef-names">Alazar Manakelew · Keegan Carey · Alexander Nguyen · Robbie Neko</div>
        <div class="ef-org">Mills College Art Museum</div>
        <a href="{GH_REPO}" target="_blank" rel="noopener" class="ef-gh" aria-label="View source on GitHub">
            {gh_icon}
        </a>
    </footer>
    """


# ──────────────────────────────────────────────
# MODAL VIEWER JS (click chart → fullscreen overlay)
# ──────────────────────────────────────────────

MODAL_HTML = """
<div id="chart-modal" class="cm" role="dialog" aria-modal="true" aria-label="Expanded chart view" style="display:none">
    <button class="cm-close" aria-label="Close expanded view" onclick="document.getElementById('chart-modal').style.display='none'">&times;</button>
    <div class="cm-body" id="cm-body"></div>
</div>
"""

MODAL_JS = """
<script>
document.addEventListener('click', function(e) {
    var plot = e.target.closest('.js-plotly-plot');
    if (!plot) return;
    var modal = document.getElementById('chart-modal');
    var body = document.getElementById('cm-body');
    body.innerHTML = '';
    var clone = plot.cloneNode(true);
    clone.style.width = '100%';
    clone.style.height = '100%';
    body.appendChild(clone);
    modal.style.display = 'flex';
    if (window.Plotly) {
        var data = plot.data;
        var layout = JSON.parse(JSON.stringify(plot.layout));
        layout.width = undefined;
        layout.height = undefined;
        layout.autosize = true;
        Plotly.newPlot(clone, data, layout, {responsive: true, displayModeBar: true, scrollZoom: true});
    }
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') document.getElementById('chart-modal').style.display = 'none';
});
</script>
"""


# ──────────────────────────────────────────────
# MAIN APP
# ──────────────────────────────────────────────

def create_interface() -> tuple[gr.Blocks, str, gr.themes.Soft]:
    """Assemble the full Gradio exhibit and return it for launching elsewhere."""
    df = load_dataset()

    css = """
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg: #0a1628;
        --surface: #0f1e36;
        --surface-hover: #142744;
        --border: rgba(212,160,23,0.2);
        --ink: #f0e6d0;
        --muted: #8a9bb8;
        --accent: #f0c040;
        --accent-light: rgba(240,192,64,0.15);
        --warm: #f0c040;
        --warm-light: rgba(240,192,64,0.12);
        --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
        --shadow: 0 8px 32px rgba(0,0,0,0.4);
        --radius: 16px;
    }

    /* Force light mode + unified font everywhere */
    .gradio-container, .gradio-container .dark, body, html {
        background: var(--bg) !important;
        color: var(--ink) !important;
        color-scheme: light !important;
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    *, *::before, *::after {
        font-family: inherit;
    }
    .app { max-width: 1280px; margin: 0 auto; padding: 24px 20px 40px; }

    /* ── Hero ── */
    .hero-panel {
        padding: 44px 36px 36px;
        background: var(--surface);
        border-radius: var(--radius);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }
    .hero-eyebrow {
        font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.18em;
        color: var(--accent); font-weight: 600; margin: 0 0 8px;
    }
    .hero-panel h1 {
        font-size: 2.8rem; font-weight: 700; line-height: 1.05; margin: 0;
        color: var(--ink);
    }
    .hero-sub {
        color: var(--muted); font-size: 1rem; margin: 16px 0 0;
        max-width: 620px; line-height: 1.65;
    }

    /* ── Hero image ── */
    .hero-img img {
        width: 100%; max-height: 240px;
        object-fit: cover; border-radius: var(--radius);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }

    /* ── Stats ── */
    .stat-strip {
        display: grid; grid-template-columns: repeat(6, 1fr);
        gap: 10px; margin: 18px 0 8px;
    }
    .s-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 14px; padding: 16px 14px; text-align: center;
        box-shadow: var(--shadow-sm);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .s-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
    .s-num { font-size: 1.65rem; font-weight: 700; color: var(--accent); line-height: 1; }
    .s-label {
        font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em;
        color: var(--muted); margin-top: 5px; font-weight: 500;
    }
    .s-detail {
        font-size: 0.68rem; color: var(--muted); margin-top: 6px;
        line-height: 1.35; opacity: 0.65;
    }

    /* ── Panel headers ── */
    .ph {
        display: flex; gap: 20px; align-items: flex-start;
        padding: 28px 0 12px;
    }
    .ph-left { flex: 0 0 auto; min-width: 200px; }
    .ph-left h2 { font-size: 1.2rem; font-weight: 600; margin: 8px 0 0; color: var(--ink); }
    .pill {
        display: inline-block; font-size: 0.58rem; text-transform: uppercase;
        letter-spacing: 0.18em; padding: 4px 14px; border-radius: 99px; font-weight: 600;
        background: var(--accent-light); color: var(--accent);
    }
    .pill.warm { background: var(--warm-light); color: var(--warm); }
    .ph-right {
        display: flex; gap: 10px; flex-wrap: wrap; flex: 1;
        align-items: stretch; padding-top: 2px;
    }
    .co {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; padding: 10px 14px;
        font-size: 0.8rem; color: var(--muted); line-height: 1.45;
        flex: 1; min-width: 170px; box-shadow: var(--shadow-sm);
    }
    .co-num { font-weight: 700; color: var(--accent); display: block; font-size: 0.88rem; margin-bottom: 2px; }
    .co-num.warm { color: var(--warm); }

    /* ── Keyword wall ── */
    .kw { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 14px 0; }
    .kc {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 14px; padding: 16px; box-shadow: var(--shadow-sm);
        transition: transform 0.2s; cursor: default;
    }
    .kc:hover { transform: translateY(-2px); }
    .kc-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
    .kc-name { font-weight: 600; font-size: 0.85rem; color: var(--ink); }
    .kc-count { font-size: 0.68rem; color: var(--muted); font-weight: 500; }
    .kc-tags { display: flex; flex-wrap: wrap; gap: 5px; }
    .kt {
        display: inline-block; background: var(--accent-light); color: var(--accent);
        padding: 3px 10px; border-radius: 99px; font-size: 0.72rem; font-weight: 500;
    }

    /* ── Chart click hint ── */
    .gradio-plot { position: relative; cursor: pointer; }
    .gradio-plot::after {
        content: 'Click to expand';
        position: absolute; top: 10px; right: 14px;
        font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.1em;
        color: var(--muted); opacity: 0;
        background: var(--surface); padding: 3px 10px; border-radius: 8px;
        border: 1px solid var(--border);
        transition: opacity 0.3s;
        pointer-events: none;
    }
    .gradio-plot:hover::after { opacity: 1; }

    /* ── Modal ── */
    .cm {
        position: fixed; inset: 0; z-index: 10000;
        background: rgba(58,53,48,0.6); backdrop-filter: blur(8px);
        display: flex; align-items: center; justify-content: center;
        padding: 32px;
    }
    .cm-close {
        position: absolute; top: 18px; left: 22px;
        width: 36px; height: 36px; border-radius: 50%;
        background: var(--surface); border: 1px solid var(--border);
        font-size: 1.3rem; color: var(--ink); cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        box-shadow: var(--shadow); z-index: 10001;
        transition: transform 0.2s;
    }
    .cm-close:hover { transform: scale(1.1); }
    .cm-body {
        background: var(--surface); border-radius: 20px;
        border: 1px solid var(--border); box-shadow: 0 24px 80px rgba(0,0,0,0.15);
        width: 90vw; max-width: 1100px; height: 80vh;
        padding: 24px; overflow: hidden;
    }

    /* ── Footer ── */
    .ef {
        text-align: center; padding: 36px 0 12px;
        border-top: 1px solid var(--border); margin-top: 32px;
    }
    .ef-team { font-size: 0.82rem; color: var(--ink); }
    .ef-course { font-weight: 700; color: var(--accent); }
    .ef-sep { color: var(--muted); margin: 0 4px; }
    .ef-names { font-size: 0.78rem; color: var(--muted); margin: 6px 0; }
    .ef-org { font-size: 0.72rem; color: var(--muted); margin-bottom: 14px; }
    .ef-gh {
        display: inline-flex; align-items: center; justify-content: center;
        width: 36px; height: 36px; border-radius: 50%;
        background: var(--surface); border: 1px solid var(--border);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .ef-gh:hover { transform: translateY(-2px); box-shadow: var(--shadow); }

    /* ── Override gradio defaults ── */
    .gradio-plot {
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        background: var(--surface) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ── Skip link for accessibility ── */
    .skip-link {
        position: absolute; left: -9999px; top: auto;
        width: 1px; height: 1px; overflow: hidden;
        z-index: 99999;
    }
    .skip-link:focus {
        position: fixed; top: 10px; left: 10px;
        width: auto; height: auto; padding: 10px 18px;
        background: var(--accent); color: #fff; border-radius: 8px;
        font-size: 0.85rem; text-decoration: none;
    }

    @media (max-width: 900px) {
        .stat-strip { grid-template-columns: repeat(3, 1fr); }
        .kw { grid-template-columns: repeat(2, 1fr); }
        .ph { flex-direction: column; gap: 10px; }
    }
    @media (max-width: 600px) {
        .stat-strip { grid-template-columns: repeat(2, 1fr); }
        .kw { grid-template-columns: 1fr; }
    }

    @media (prefers-reduced-motion: reduce) {
        .s-card, .kc, .ef-gh, .cm-close { transition: none !important; }
        .s-card:hover, .kc:hover { transform: none; }
    }
    """

    theme = gr.themes.Soft(primary_hue="yellow", secondary_hue="slate", neutral_hue="slate").set(
        body_background_fill="#0a1628",
        block_background_fill="#0f1e36",
        block_border_width="1px",
        block_border_color="rgba(212,160,23,0.2)",
    )

    with gr.Blocks(css=css, theme=theme, title="Mills Museum Data Exhibit") as demo:

        # Skip link for keyboard navigation
        gr.HTML('<a href="#main-content" class="skip-link">Skip to main content</a>')
        gr.HTML(MODAL_HTML)

        with gr.Column(elem_classes=["app"]):
            gr.HTML('<div id="main-content"></div>')

            # ── HERO ──
            with gr.Row():
                with gr.Column(scale=3):
                    gr.HTML(build_hero_html())
                with gr.Column(scale=2, elem_classes=["hero-img"]):
                    if HERO_IMAGE.exists():
                        gr.Image(value=str(HERO_IMAGE), show_label=False, interactive=False, container=False)

            # ── STATS ──
            gr.HTML(build_stat_strip(df))

            # ── ATLAS ──
            gr.HTML(_panel_header("Atlas", "Where the collection's weight sits", [
                ("16,157", "furnishings terms — 36.5% of the entire dataset"),
                ("316 children", "under metalworking equipment, the largest parent node"),
                ("82.8% leaves", "most terms sit at the edges of the taxonomy"),
            ]))
            with gr.Row():
                gr.Plot(value=build_facet_river(df), container=True)
                gr.Plot(value=build_sunburst(df), container=True)

            # ── VOCABULARY ──
            gr.HTML(build_keyword_wall(df))

            # ── TIME ──
            gr.HTML(_panel_header("Time", "When each century left its mark", [
                ("562 mentions", "of the 19th century in scope notes — the Industrial Revolution's echo"),
                ("15th century", "paper enters the vocabulary as the printing press spreads"),
                ("Tang dynasty", "Asian references peak during the 8th-13th centuries"),
            ], warm=True))
            with gr.Row():
                gr.Plot(value=build_century_heatmap(df), container=True)
            with gr.Row():
                gr.Plot(value=build_kw_century(df), container=True)

            # ── STRUCTURE ──
            gr.HTML(_panel_header("Structure", "How deep does each facet go?", [
                ("11 levels deep", "Eukaryota to Morpho menelaus — a butterfly at the bottom"),
                ("32% undescribed", "Furnishings terms lack scope notes — the biggest gap"),
                ("Jaccard 0.11", "Components and Furnishings share the most vocabulary"),
            ]))
            with gr.Row():
                gr.Plot(value=build_depth_violin(df), container=True)
                gr.Plot(value=build_scatter(df), container=True)

            # ── WORLD ──
            gr.HTML(_panel_header("World", "Geography and language across time", [
                ("2,278 vs 2,264", "Asian references edge out European in a Getty thesaurus"),
                ("11.3% CJK", "of 334K variant terms are Chinese, Japanese, or Korean"),
                ("53 variants", "for scrolled pediments — the most translated single term"),
            ], warm=True))
            with gr.Row():
                gr.Plot(value=build_geo_area(df), container=True)

            # ── FOOTER ──
            gr.HTML(build_footer())

        # Inject the JavaScript that powers click-to-expand chart viewing.
        gr.HTML(MODAL_JS)

    return demo, css, theme


demo, _css, _theme = create_interface()


def main() -> None:
    """Launch the exhibit locally for browser viewing."""
    demo.launch(server_name="127.0.0.1", server_port=7860, css=_css, theme=_theme)


if __name__ == "__main__":
    main()
