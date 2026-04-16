"""
Analysis on Art & Architecture Thesaurus (Getty Research Institute)
====================================================================

This script builds an interactive HTML dashboard that visualizes
44,225 terms from the Getty AAT (Art & Architecture Thesaurus).

The dashboard is a single-page scrolling story with 7 interactive
Plotly charts covering:

    1. Facet distribution   — donut chart of the 12 AAT facets
    2. Century heatmap      — when each facet's terms were most active
    3. Hierarchy sunburst   — drill into parent/child term structure
    4. Keyword trends       — top words plotted across centuries
    5. Tree depth           — how deep each facet's taxonomy goes
    6. Geographic coverage  — which world regions appear over time
    7. Language scripts     — Latin vs CJK vs other writing systems

How to run
----------
    python src/analysis/09_dashboard.py

Override the input data or output location with environment variables:

    AAT_ANALYSIS_DATA_PATH=path/to/data.parquet \\
    AAT_ANALYSIS_OUTPUT_PATH=path/to/output.html \\
        python src/analysis/09_dashboard.py

Dependencies: pandas, plotly, pyarrow

Note
----
This script is independent of the Gradio web app in
``src/frontend/data_viz/data_story_exhibit.py``. That app builds its own live
charts for the interactive website. This script produces a standalone
HTML file you open directly in a browser — no server required.
"""

import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# These paths can be overridden via environment variables so the same script
# works on any dataset snapshot or output location.

ANALYSIS_DIR = Path(__file__).resolve().parent
FIGDIR = ANALYSIS_DIR / "figures"

DATA_PATH = (
    Path(os.environ["AAT_ANALYSIS_DATA_PATH"]).expanduser()
    if "AAT_ANALYSIS_DATA_PATH" in os.environ
    else ANALYSIS_DIR / "data_cache" / "aat_museum_subset.parquet"
)

OUTPUT_PATH = (
    Path(os.environ["AAT_ANALYSIS_OUTPUT_PATH"]).expanduser()
    if "AAT_ANALYSIS_OUTPUT_PATH" in os.environ
    else FIGDIR / "dashboard.html"
)

# ---------------------------------------------------------------------------
# Load the dataset
# ---------------------------------------------------------------------------
# The parquet file is a cached snapshot of the HuggingFace dataset
# "KeeganC/aat-museum-subset". Each row represents one AAT term with
# columns like preferred_term, hierarchy, scope_note, parent_term, etc.

df = pd.read_parquet(DATA_PATH)

# Filter to rows that have a scope note (free-text description). Many
# visualizations mine these descriptions for century references and
# geographic keywords.
scope_notes = df[df["scope_note"].notna()]

# Common English stopwords removed when counting keywords in term names.
stopwords = {
    "and", "of", "the", "for", "in", "with", "a", "an",
    "to", "or", "by", "on", "at", "as", "is",
}

# Regex that finds century references like "19th century" in scope notes.
century_pattern = re.compile(r'(\d+)(?:st|nd|rd|th)\s+centur', re.IGNORECASE)

# ---------------------------------------------------------------------------
# Visual theme
# ---------------------------------------------------------------------------
# All charts share this dark-background layout so they blend into the
# dashboard's navy/gold color scheme. Changing these values will update
# every chart at once.

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,30,54,0.4)",
    font=dict(
        family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        color="#f0e6d0",
        size=12,
    ),
    margin=dict(l=50, r=30, t=40, b=40),
)

GOLD = "#f0c040"
WARM = "#e8b616"
PALETTE = [
    "#f0c040", "#e8b616", "#d4a017", "#5b749a", "#6c85a8",
    "#8a9bb8", "#c4960e", "#4a6385", "#f5d060", "#b08c12",
    "#3b5170", "#ffd866",
]

# Dictionary that collects every Plotly figure by name. At the end of the
# script, each figure is serialized to JSON and embedded into the HTML.
figs = {}

# ---------------------------------------------------------------------------
# Chart 1: Facet Donut
# ---------------------------------------------------------------------------
# The AAT organizes every term into one of 12 "facets" (broad categories
# like Furnishings & Equipment, Styles & Periods, Materials, etc.).
# This donut chart shows what percentage of the 44K terms falls into each.
# Furnishings & Equipment dominates at ~36%.
counts = df["hierarchy"].value_counts()
figs["facet_donut"] = go.Figure(go.Pie(
    labels=counts.index.tolist(), values=counts.values.tolist(),
    hole=0.48, textinfo="percent", textposition="inside",
    textfont=dict(size=10, color="#0a1628"),
    marker=dict(colors=PALETTE, line=dict(color="#0a1628", width=2)),
    hovertemplate="<b>%{label}</b><br>%{value:,} terms (%{percent})<extra></extra>",
    sort=False
))
figs["facet_donut"].update_layout(**CHART_LAYOUT, height=480, showlegend=True,
    legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)", x=1.02, y=0.5))

# ---------------------------------------------------------------------------
# Chart 2: Century Heatmap
# ---------------------------------------------------------------------------
# For every term that has a scope note, we search the text for phrases like
# "19th century" or "3rd century". We then count how often each century is
# mentioned within each facet. The result is a heatmap where bright cells
# mean a facet has many terms associated with that time period.
facet_century = defaultdict(lambda: Counter())
for _, row in scope_notes.iterrows():
    for match in century_pattern.finditer(row["scope_note"]):
        c = int(match.group(1))
        if 3 <= c <= 20:
            facet_century[row["hierarchy"]][c] += 1

facet_order = df["hierarchy"].value_counts().index.tolist()
centuries = list(range(3, 21))
z_data = [[facet_century[f].get(c, 0) for c in centuries] for f in facet_order]

figs["century_heatmap"] = go.Figure(go.Heatmap(
    z=z_data, x=[f"{c}th" for c in centuries], y=facet_order,
    colorscale=[[0, "#0a1628"], [0.15, "#1a2d4a"], [0.4, "#5b749a"], [0.7, "#d4a017"], [1, "#f0c040"]],
    hoverongaps=False,
    hovertemplate="%{y}<br>%{x} century: <b>%{z}</b> mentions<extra></extra>"
))
figs["century_heatmap"].update_layout(**CHART_LAYOUT, height=460,
    yaxis=dict(autorange="reversed"), xaxis=dict(side="top"))

# ---------------------------------------------------------------------------
# Chart 3: Hierarchy Sunburst
# ---------------------------------------------------------------------------
# A sunburst (nested ring chart) showing the top 5 parent terms within each
# facet. Clicking a ring drills into that branch. This reveals how terms
# cluster — e.g., "metalworking equipment" holds 316 children.
top_parents = df.groupby(["hierarchy", "parent_term"]).size().reset_index(name="count")
top_parents = top_parents.sort_values("count", ascending=False).groupby("hierarchy").head(5)
figs["sunburst"] = px.sunburst(
    top_parents, path=["hierarchy", "parent_term"], values="count",
    color="hierarchy", color_discrete_sequence=PALETTE
)
figs["sunburst"].update_layout(**CHART_LAYOUT, height=580)
figs["sunburst"].update_traces(
    textfont=dict(color="#f0e6d0", size=11),
    insidetextorientation="radial",
    marker=dict(line=dict(color="#0a1628", width=1.5))
)

# ---------------------------------------------------------------------------
# Chart 4: Keyword Trends Over Centuries
# ---------------------------------------------------------------------------
# The 40 most common words in term names are cross-referenced with century
# mentions in scope notes. The resulting heatmap shows when each keyword
# peaked — for example, "styles" surges in the 19th century during the
# Revival movements, while "paper" appears from the 15th century onward.
top_words = Counter()
for term in df["preferred_term"].str.lower():
    top_words.update(w for w in term.split() if w not in stopwords and len(w) > 2)

top_kws = [w for w, _ in top_words.most_common(40)]
kw_century = defaultdict(lambda: Counter())
for _, row in scope_notes.iterrows():
    cfound = [int(m.group(1)) for m in century_pattern.finditer(row["scope_note"]) if 3 <= int(m.group(1)) <= 20]
    if not cfound:
        continue
    tw = set(row["preferred_term"].lower().split())
    for kw in top_kws:
        if kw in tw:
            for c in cfound:
                kw_century[kw][c] += 1

kws_with_data = [kw for kw in top_kws if sum(kw_century[kw].values()) >= 5][:20]
z_kw = [[kw_century[kw].get(c, 0) for c in centuries] for kw in kws_with_data]

figs["kw_trend"] = go.Figure(go.Heatmap(
    z=z_kw, x=[f"{c}th" for c in centuries], y=kws_with_data,
    colorscale=[[0, "#0a1628"], [0.2, "#1a2d4a"], [0.5, "#c4960e"], [0.8, "#e8b616"], [1, "#f0c040"]],
    hoverongaps=False,
    hovertemplate="<b>%{y}</b> in the %{x} century: %{z} mentions<extra></extra>"
))
figs["kw_trend"].update_layout(**CHART_LAYOUT, height=540,
    yaxis=dict(autorange="reversed"), xaxis=dict(side="top"))

# ---------------------------------------------------------------------------
# Chart 5: Tree Depth Violin Plot
# ---------------------------------------------------------------------------
# Each AAT term sits at some depth in a parent-child tree. We walk up the
# parent_id chain for every term to compute its depth, then show the
# distribution per facet as a violin plot. Styles & Periods tends to have
# the widest spread; the deepest single path is 11 levels (a butterfly
# species under biological taxonomy).
parent_map = dict(zip(df["subject_id"], df["parent_id"]))
def get_depth(sid, memo={}):
    if sid in memo:
        return memo[sid]
    pid = parent_map.get(sid)
    if pid is None or pid not in parent_map or pid == sid:
        memo[sid] = 0
        return 0
    d = get_depth(pid, memo) + 1
    memo[sid] = d
    return d

df["tree_depth"] = df["subject_id"].apply(get_depth)
depth_df = df[["hierarchy", "tree_depth"]].copy()

figs["depth_violin"] = px.violin(
    depth_df, x="hierarchy", y="tree_depth", color="hierarchy",
    color_discrete_sequence=PALETTE, box=True, points=False,
    category_orders={"hierarchy": facet_order}
)
figs["depth_violin"].update_layout(**CHART_LAYOUT,
    xaxis_title="", yaxis_title="Tree Depth", showlegend=False, height=460,
    xaxis=dict(tickangle=35, tickfont=dict(size=9)))

# ---------------------------------------------------------------------------
# Chart 6: Geographic Coverage Over Time
# ---------------------------------------------------------------------------
# We scan scope notes for region-related keywords (e.g., "European",
# "Chinese", "Islamic") and count how often each region appears per century.
# The stacked area chart reveals that Asian and European references are
# nearly tied overall, with distinct peaks in different eras.
geo_patterns = {
    "European": re.compile(r'\b(europe|european|french|italian|english|german|spanish|dutch|greek|roman|british)\b', re.I),
    "Asian": re.compile(r'\b(asia|asian|chinese|japanese|indian|korean|persian|thai)\b', re.I),
    "African": re.compile(r'\b(africa|african|egyptian|saharan)\b', re.I),
    "Americas": re.compile(r'\b(america|american|native american|mesoamerican|pre-columbian)\b', re.I),
    "Middle Eastern": re.compile(r'\b(middle east|islamic|ottoman|arab|mesopotamian)\b', re.I),
}

geo_century = defaultdict(lambda: Counter())
for _, row in scope_notes.iterrows():
    cfound = [int(m.group(1)) for m in century_pattern.finditer(row["scope_note"]) if 3 <= int(m.group(1)) <= 20]
    if not cfound:
        continue
    for region, pat in geo_patterns.items():
        if pat.search(row["scope_note"]):
            for c in cfound:
                geo_century[region][c] += 1

geo_rows = []
for region in geo_patterns:
    for c in centuries:
        geo_rows.append({"Region": region, "Century": f"{c}th", "Mentions": geo_century[region].get(c, 0)})

figs["geo_time"] = px.area(
    pd.DataFrame(geo_rows), x="Century", y="Mentions", color="Region",
    color_discrete_sequence=["#f0c040", "#e8b616", "#d4a017", "#5b749a", "#8a9bb8"]
)
figs["geo_time"].update_layout(**CHART_LAYOUT, height=420, hovermode="x unified")

# ---------------------------------------------------------------------------
# Chart 7: Writing Scripts (Latin / CJK / Other)
# ---------------------------------------------------------------------------
# Every AAT term has multilingual "variant_terms" (translations). We check
# each variant's Unicode range to classify it as Latin, CJK (Chinese,
# Japanese, Korean), or Other (Arabic, Cyrillic, etc.). Latin dominates
# at ~88%, but CJK makes up a surprising ~11% of all variants.
cjk_re = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]')
arabic_re = re.compile(r'[\u0600-\u06ff]')
cyrillic_re = re.compile(r'[\u0400-\u04ff]')

lang_counts = Counter()
for variants in df["variant_terms"]:
    for v in variants:
        v_str = str(v)
        if cjk_re.search(v_str):
            lang_counts["CJK"] += 1
        elif arabic_re.search(v_str) or cyrillic_re.search(v_str):
            lang_counts["Other"] += 1
        else:
            lang_counts["Latin"] += 1

figs["scripts"] = go.Figure(go.Pie(
    labels=list(lang_counts.keys()), values=list(lang_counts.values()),
    hole=0, textinfo="label+percent", textfont=dict(size=14, color="#fff"),
    marker=dict(colors=[GOLD, "#5b749a", "#8a9bb8"], line=dict(color="#0a1628", width=3)),
    hovertemplate="<b>%{label}</b><br>%{value:,} terms (%{percent})<extra></extra>",
    pull=[0, 0.06, 0.1]
))
figs["scripts"].update_layout(**CHART_LAYOUT, height=400, showlegend=False)


# ---------------------------------------------------------------------------
# Serialize all charts to JavaScript
# ---------------------------------------------------------------------------
# Each Plotly figure is converted to JSON and wrapped in an immediately-
# invoked function expression (IIFE). The browser executes these on page
# load to render every chart into its <div> container.

fig_init_js = ""
for key, fig in figs.items():
    fig_init_js += f"""
    (function() {{
        var data = {fig.to_json()};
        Plotly.newPlot('chart-{key}', data.data, data.layout, {{
            responsive: true, displayModeBar: false, scrollZoom: false
        }});
    }})();
    """

# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------
# The entire dashboard is a single self-contained HTML file. Plotly.js is
# loaded from a CDN; all chart data is inlined as JSON. The page uses a
# dark navy/gold theme with scroll-triggered animations.

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analysis on Art &amp; Architecture Thesaurus (Getty Research Institute)</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root {{
    --bg: #0a1628;
    --bg2: #0f1e36;
    --surface: rgba(15,30,54,0.94);
    --ink: #f0e6d0;
    --muted: #8a9bb8;
    --accent: #f0c040;
    --accent-soft: rgba(240,192,64,0.15);
    --warm: #e8b616;
    --warm-soft: rgba(232,182,22,0.12);
    --border: rgba(212,160,23,0.2);
    --shadow: 0 18px 60px rgba(0,0,0,0.4);
    --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
    background: var(--bg);
    color: var(--ink);
    font-family: var(--font);
    line-height: 1.7;
    overflow-x: hidden;
}}

/* ══ HERO ══ */
.hero {{
    position: relative;
    height: 75vh;
    min-height: 480px;
    max-height: 680px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    overflow: hidden;
}}
.hero-bg {{
    position: absolute; inset: 0;
    background: linear-gradient(
        135deg,
        #0a1628 0%,
        #0f1e36 30%,
        #1a2d4a 60%,
        #0f1e36 80%,
        #0a1628 100%
    );
}}
.hero-bg::after {{
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(
        ellipse at 50% 40%,
        rgba(240,192,64,0.08) 0%,
        transparent 70%
    );
}}
.hero-content {{
    position: relative; z-index: 2;
    text-align: center;
    padding: 0 24px 70px;
    max-width: 720px;
}}
.hero-content h1 {{
    font-size: clamp(2rem, 4.5vw, 3.2rem);
    font-weight: 300;
    color: var(--ink);
    line-height: 1.2;
    margin-bottom: 14px;
}}
.hero-content h1 strong {{ font-weight: 700; color: var(--accent); }}
.hero-content .tagline {{
    font-size: 1.05rem;
    color: var(--muted);
    font-style: italic;
    margin-bottom: 32px;
}}
.hero-stats {{
    display: flex;
    justify-content: center;
    gap: 28px;
    flex-wrap: wrap;
}}
.hero-stat {{
    text-align: center;
    opacity: 0;
    transform: translateY(20px);
    animation: fadeUp 0.7s ease forwards;
}}
.hero-stat:nth-child(1){{ animation-delay:.3s }}
.hero-stat:nth-child(2){{ animation-delay:.42s }}
.hero-stat:nth-child(3){{ animation-delay:.54s }}
.hero-stat:nth-child(4){{ animation-delay:.66s }}
.hero-stat:nth-child(5){{ animation-delay:.78s }}
.hero-stat .num {{
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
    line-height: 1.1;
}}
.hero-stat .lbl {{
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
}}
.scroll-cue {{
    position: absolute;
    bottom: 20px; left: 50%;
    transform: translateX(-50%);
    z-index: 2;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    animation: gentle-bounce 2.5s ease-in-out infinite;
}}
.scroll-cue::after {{
    content: '';
    display: block;
    width: 1px; height: 28px;
    background: var(--accent);
    margin: 6px auto 0;
    opacity: 0.4;
}}
@keyframes fadeUp {{ to {{ opacity:1; transform:translateY(0) }} }}
@keyframes gentle-bounce {{
    0%,100% {{ transform: translateX(-50%) translateY(0) }}
    50% {{ transform: translateX(-50%) translateY(6px) }}
}}

/* ══ BIRDS ══ */
nav {{ position: sticky; top:0; z-index:1000; }}
.nav-bar {{
    position: relative;
    background: rgba(10,22,40,0.88);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: center;
    gap: 0;
    padding: 0 20px;
}}
.bird {{
    position: absolute;
    bottom: calc(100% - 2px);
    width: 26px; height: 18px;
    opacity: 0.45;
}}
.bird svg {{ width:100%; height:100%; }}
.bird:nth-child(1) {{ left: 14%; transform: scaleX(-1); }}
.bird:nth-child(2) {{ left: 40%; }}
.bird:nth-child(3) {{ right: 24%; transform: scaleX(-1); }}
.bird:nth-child(4) {{ right: 10%; }}
.bird-idle {{ animation: bird-bob 3s ease-in-out infinite; }}
.bird:nth-child(2) .bird-idle {{ animation-delay: 0.8s; }}
.bird:nth-child(3) .bird-idle {{ animation-delay: 1.6s; }}
.bird:nth-child(4) .bird-idle {{ animation-delay: 0.4s; }}
@keyframes bird-bob {{
    0%,100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-3px); }}
}}

.nav-link {{
    color: var(--muted);
    text-decoration: none;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 14px 18px;
    position: relative;
    transition: color 0.3s;
}}
.nav-link:hover {{ color: var(--accent); }}
.nav-link.active {{ color: var(--accent); font-weight: 600; }}
.nav-link.active::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 18px; right: 18px;
    height: 2px;
    background: var(--accent);
    border-radius: 2px;
}}

/* ══ LEAVES ══ */
.leaves-container {{
    position: fixed; top:0; left:0;
    width: 100vw; height: 100vh;
    pointer-events: none;
    z-index: 9999;
    overflow: hidden;
}}
.leaf {{
    position: absolute;
    top: -40px;
    opacity: 0;
    animation: leafFall linear forwards;
}}
@keyframes leafFall {{
    0% {{ opacity:0; transform: translateX(0) rotate(0deg); }}
    5% {{ opacity:0.7; }}
    100% {{ opacity:0; transform: translateX(var(--drift)) rotate(var(--spin)); top: 110vh; }}
}}

/* ══ STORY ══ */
.story {{
    max-width: 1060px;
    margin: 0 auto;
    padding: 0 24px;
}}

.chapter {{
    padding: 80px 0 60px;
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.8s ease, transform 0.8s ease;
}}
.chapter.visible {{ opacity:1; transform:translateY(0); }}

.chapter-label {{
    display: inline-block;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--accent);
    font-weight: 600;
    background: var(--accent-soft);
    padding: 3px 12px;
    border-radius: 99px;
    margin-bottom: 14px;
}}
.chapter h2 {{
    font-size: clamp(1.4rem, 3vw, 2rem);
    font-weight: 600;
    line-height: 1.3;
    color: var(--ink);
    margin-bottom: 14px;
}}
.chapter p {{
    font-size: 0.95rem;
    color: var(--muted);
    line-height: 1.8;
    margin-bottom: 24px;
}}
.hl {{ color: var(--accent); font-weight: 600; }}
.hl2 {{ color: var(--warm); font-style: italic; }}

.chart-wrap {{
    width: 100%;
    min-height: 420px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px;
    box-shadow: var(--shadow);
    margin-top: 8px;
    overflow: visible;
}}
.chart-wrap .js-plotly-plot,
.chart-wrap .plotly,
.chart-wrap .plot-container {{
    width: 100% !important;
}}

/* Two-column: text beside chart, no overlap */
.two-col {{
    display: flex;
    gap: 40px;
    align-items: flex-start;
}}
.two-col > .col-text {{
    flex: 0 0 340px;
    min-width: 0;
}}
.two-col > .col-chart {{
    flex: 1 1 0%;
    min-width: 0;
}}
.two-col-reverse {{
    display: flex;
    gap: 40px;
    align-items: flex-start;
    flex-direction: row-reverse;
}}
.two-col-reverse > .col-text {{
    flex: 0 0 340px;
    min-width: 0;
}}
.two-col-reverse > .col-chart {{
    flex: 1 1 0%;
    min-width: 0;
}}

.callout {{
    display: inline-flex;
    align-items: baseline;
    gap: 8px;
    background: var(--warm-soft);
    border-radius: 10px;
    padding: 8px 16px;
    margin: 12px 0 0;
}}
.callout .big {{
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--warm);
}}
.callout .context {{
    font-size: 0.82rem;
    color: var(--muted);
}}

.sep {{
    width: 36px; height: 2px;
    background: var(--accent);
    opacity: 0.25;
    margin: 0 auto;
}}

.depth-path {{
    font-style: italic;
    color: var(--warm);
    font-size: 0.88rem;
    line-height: 1.5;
    margin-top: 6px;
}}

footer {{
    text-align: center;
    padding: 50px 24px;
    border-top: 1px solid var(--border);
    font-size: 0.78rem;
    color: var(--muted);
}}
footer a {{ color: var(--accent); text-decoration: none; }}

/* ══ SKIP LINK ══ */
.skip-link {{
    position: absolute; left: -9999px; top: auto;
    width: 1px; height: 1px; overflow: hidden; z-index: 99999;
}}
.skip-link:focus {{
    position: fixed; top: 10px; left: 10px;
    width: auto; height: auto; padding: 10px 18px;
    background: var(--accent); color: var(--bg); border-radius: 8px;
    font-size: 0.85rem; font-weight: 600; text-decoration: none;
    box-shadow: var(--shadow);
}}

/* ══ FOCUS STYLES ══ */
.nav-link:focus-visible {{
    outline: 2px solid var(--accent);
    outline-offset: 2px;
    border-radius: 4px;
}}
a:focus-visible, button:focus-visible {{
    outline: 2px solid var(--accent);
    outline-offset: 2px;
}}

/* ══ REDUCED MOTION ══ */
@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }}
    .chapter {{ opacity: 1; transform: none; }}
    .hero-stat {{ opacity: 1; transform: none; }}
    html {{ scroll-behavior: auto; }}
}}

@media (max-width: 800px) {{
    .two-col, .two-col-reverse {{
        flex-direction: column;
    }}
    .two-col > .col-text,
    .two-col-reverse > .col-text {{
        flex: none;
        width: 100%;
    }}
    .hero-stats {{ gap: 16px; }}
}}
</style>
</head>
<body>

<!-- Skip link for keyboard / screen-reader users -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- FALLING LEAVES (decorative, hidden from assistive tech) -->
<div class="leaves-container" id="leaves" aria-hidden="true"></div>

<!-- HERO -->
<header class="hero" role="banner">
    <div class="hero-bg" aria-hidden="true"></div>
    <div class="hero-content">
        <h1>Analysis on the<br><strong>Art &amp; Architecture Thesaurus</strong></h1>
        <p class="tagline">Getty Research Institute &mdash; 44,225 terms. 12 facets. Centuries of material culture.</p>
        <div class="hero-stats" role="list" aria-label="Key dataset statistics">
            <div class="hero-stat" role="listitem" aria-label="44,225 Terms"><div class="num">44,225</div><div class="lbl">Terms</div></div>
            <div class="hero-stat" role="listitem" aria-label="12 Facets"><div class="num">12</div><div class="lbl">Facets</div></div>
            <div class="hero-stat" role="listitem" aria-label="334K Translations"><div class="num">334K</div><div class="lbl">Translations</div></div>
            <div class="hero-stat" role="listitem" aria-label="37K Descriptions"><div class="num">37K</div><div class="lbl">Descriptions</div></div>
            <div class="hero-stat" role="listitem" aria-label="Max depth 11"><div class="num">11</div><div class="lbl">Max Depth</div></div>
        </div>
    </div>
    <div class="scroll-cue" aria-hidden="true">Scroll</div>
</header>

<!-- NAV WITH BIRDS -->
<nav aria-label="Dashboard sections">
    <div class="nav-bar" role="menubar">
        <div class="bird" aria-hidden="true"><svg class="bird-idle" viewBox="0 0 40 24" fill="none"><path d="M20 12c-4-6-12-8-18-6 4 1 8 4 10 8M20 12c4-6 12-8 18-6-4 1-8 4-10 8" stroke="#0f1a2e" stroke-width="1.5" stroke-linecap="round"/><circle cx="20" cy="13" r="2" fill="#0f1a2e" opacity="0.6"/></svg></div>
        <div class="bird" aria-hidden="true"><svg class="bird-idle" viewBox="0 0 40 24" fill="none"><path d="M20 12c-4-6-12-8-18-6 4 1 8 4 10 8M20 12c4-6 12-8 18-6-4 1-8 4-10 8" stroke="#0f1a2e" stroke-width="1.5" stroke-linecap="round"/><circle cx="20" cy="13" r="2" fill="#0f1a2e" opacity="0.6"/></svg></div>
        <div class="bird" aria-hidden="true"><svg class="bird-idle" viewBox="0 0 40 24" fill="none"><path d="M20 12c-4-6-12-8-18-6 4 1 8 4 10 8M20 12c4-6 12-8 18-6-4 1-8 4-10 8" stroke="#0f1a2e" stroke-width="1.5" stroke-linecap="round"/><circle cx="20" cy="13" r="2" fill="#0f1a2e" opacity="0.6"/></svg></div>
        <div class="bird" aria-hidden="true"><svg class="bird-idle" viewBox="0 0 40 24" fill="none"><path d="M20 12c-4-6-12-8-18-6 4 1 8 4 10 8M20 12c4-6 12-8 18-6-4 1-8 4-10 8" stroke="#0f1a2e" stroke-width="1.5" stroke-linecap="round"/><circle cx="20" cy="13" r="2" fill="#0f1a2e" opacity="0.6"/></svg></div>
        <a href="#overview" class="nav-link" role="menuitem">The Collection</a>
        <a href="#centuries" class="nav-link" role="menuitem">Through Time</a>
        <a href="#sunburst" class="nav-link" role="menuitem">Hierarchy</a>
        <a href="#trends" class="nav-link" role="menuitem">Trending</a>
        <a href="#depth" class="nav-link" role="menuitem">Depth</a>
        <a href="#geography" class="nav-link" role="menuitem">Geography</a>
        <a href="#scripts" class="nav-link" role="menuitem">Languages</a>
    </div>
</nav>

<main id="main-content" class="story">

    <!-- 1 — OVERVIEW -->
    <section class="chapter" id="overview" aria-labelledby="overview-heading">
        <div class="two-col">
            <div class="col-text">
                <span class="chapter-label">The Collection</span>
                <h2 id="overview-heading">One third of every term describes a physical object.</h2>
                <p>The AAT organizes human material culture into 12 facets. But they're far from equal —
                <span class="hl">Furnishings &amp; Equipment alone holds 36.5%</span> of all terms.
                From dental instruments to dough troughs, the thesaurus maps the objects
                civilizations have built, worn, and wielded.</p>
                <div class="callout" role="note" aria-label="16,157 terms for furnishings, tools, and equipment">
                    <span class="big">16,157</span>
                    <span class="context">terms for furnishings, tools, and equipment</span>
                </div>
            </div>
            <div class="col-chart">
                <div class="chart-wrap" id="chart-facet_donut" role="img" aria-label="Donut chart showing term distribution across the 12 AAT facets"></div>
            </div>
        </div>
    </section>

    <div class="sep" role="separator" aria-hidden="true"></div>

    <!-- 2 — CENTURIES -->
    <section class="chapter" id="centuries" aria-labelledby="centuries-heading">
        <span class="chapter-label">Through Time</span>
        <h2 id="centuries-heading">The 19th century casts the longest shadow.</h2>
        <p>Every scope note was mined for century references. The Industrial Revolution didn't just
        transform society — it generated an avalanche of vocabulary.
        <span class="hl">562 mentions of the 19th century</span>, more than double any other.
        Styles &amp; Periods is the most time-anchored facet. Color is timeless.</p>
        <div class="chart-wrap" id="chart-century_heatmap" role="img" aria-label="Heatmap of century references across facets, showing 19th century dominance"></div>
    </section>

    <div class="sep" role="separator" aria-hidden="true"></div>

    <!-- 3 — SUNBURST -->
    <section class="chapter" id="sunburst" aria-labelledby="sunburst-heading">
        <span class="chapter-label">The Hierarchy</span>
        <h2 id="sunburst-heading" style="max-width:600px;">Click inward. This is how knowledge is organized.</h2>
        <p style="max-width:600px;">Each ring peels back a layer of the taxonomy. Notice the
        <span class="hl">"temporary alphabetical list"</span> entries —
        terms awaiting classification in a living, curated system.
        The largest node is <span class="hl2">metalworking equipment</span> with 316 children.</p>
        <div class="chart-wrap" id="chart-sunburst" role="img" aria-label="Interactive sunburst chart of the AAT taxonomy hierarchy. Click rings to drill into branches."></div>
    </section>

    <div class="sep" role="separator" aria-hidden="true"></div>

    <!-- 4 — TRENDS -->
    <section class="chapter" id="trends" aria-labelledby="trends-heading">
        <span class="chapter-label">Trending Terms</span>
        <h2 id="trends-heading">When was each word at its peak?</h2>
        <p>Cross-referencing preferred terms with century mentions reveals temporal fingerprints.
        <span class="hl">"Styles" surges in the 19th century</span> as Revival movements exploded.
        "Paper" appears from the 15th century — the printing press rippling through vocabulary.
        Hover to trace each word's arc through time.</p>
        <div class="chart-wrap" id="chart-kw_trend" role="img" aria-label="Heatmap showing when top keywords peaked across centuries"></div>
    </section>

    <div class="sep" role="separator" aria-hidden="true"></div>

    <!-- 5 — DEPTH -->
    <section class="chapter" id="depth" aria-labelledby="depth-heading">
        <div class="two-col-reverse">
            <div class="col-text">
                <span class="chapter-label">Depth</span>
                <h2 id="depth-heading">Some branches run eleven levels deep.</h2>
                <p><span class="hl">Styles &amp; Periods spreads widest</span> — from "Renaissance"
                near the root to nested pottery sub-styles. The deepest path?</p>
                <p class="depth-path" aria-label="Deepest taxonomy path: Eukaryota to Morpho menelaus, 11 levels">
                    Eukaryota &rarr; Animalia &rarr; Arthropoda &rarr; Hexapoda &rarr;
                    Insecta &rarr; Lepidoptera &rarr; Papilionoidea &rarr; Nymphalidae &rarr;
                    Morphinae &rarr; Morphini &rarr; Morpho &rarr; <strong>Morpho menelaus</strong>
                </p>
                <p>A blue butterfly, eleven levels from the root.</p>
            </div>
            <div class="col-chart">
                <div class="chart-wrap" id="chart-depth_violin" role="img" aria-label="Violin plot showing taxonomy tree depth distribution per facet"></div>
            </div>
        </div>
    </section>

    <div class="sep" role="separator" aria-hidden="true"></div>

    <!-- 6 — GEOGRAPHY -->
    <section class="chapter" id="geography" aria-labelledby="geo-heading">
        <span class="chapter-label">Geography</span>
        <h2 id="geo-heading">Asia and Europe, neck and neck.</h2>
        <p><span class="hl">Asian references slightly edge out European</span> (2,278 vs 2,264)
        in a Getty-originated thesaurus. European mentions peak during the colonial era.
        Asian references are strongest during the Tang and Song dynasties, then again
        in the 17th–19th centuries. Watch the regions shift as you scan across time.</p>
        <div class="chart-wrap" id="chart-geo_time" role="img" aria-label="Stacked area chart of geographic region mentions across centuries"></div>
    </section>

    <div class="sep" role="separator" aria-hidden="true"></div>

    <!-- 7 — SCRIPTS -->
    <section class="chapter" id="scripts" aria-labelledby="scripts-heading">
        <div class="two-col">
            <div class="col-text">
                <span class="chapter-label">Languages</span>
                <h2 id="scripts-heading">334,694 names in scripts spanning the globe.</h2>
                <p>Every term averages <span class="hl">7.6 multilingual variants</span>.
                Latin script dominates at 88.5%, but the CJK presence is striking —
                <span class="hl">11.3% of all variants are Chinese, Japanese, or Korean</span>.
                Chinese architectural terms receive the richest scope notes in the entire dataset.</p>
                <div class="callout" role="note" aria-label="53 variants for scrolled pediments, the most translated term">
                    <span class="big">53</span>
                    <span class="context">variants for "scrolled pediments" — the most translated term</span>
                </div>
            </div>
            <div class="col-chart">
                <div class="chart-wrap" id="chart-scripts" role="img" aria-label="Pie chart showing Latin at 88.5%, CJK at 11.3%, and other scripts"></div>
            </div>
        </div>
    </section>

</main>

<footer role="contentinfo">
    <div style="margin-bottom:12px;">
        <strong style="color:var(--accent);">CS 2535</strong> &nbsp;&middot;&nbsp;
        Prof. Oakhoury &nbsp;&middot;&nbsp; Spring 2026
    </div>
    <div style="margin-bottom:8px;">
        Alazar Manakelew &nbsp;&middot;&nbsp; Keegan Carey &nbsp;&middot;&nbsp;
        Alexander Nguyen &nbsp;&middot;&nbsp; Robbie Neko
    </div>
    <div>Mills College Art Museum Project</div>
</footer>

<script>
// ── Init Charts (deferred to ensure containers have dimensions) ──
window.addEventListener('load', function() {{
    requestAnimationFrame(function() {{
        {fig_init_js}

        // Force resize all charts after a beat
        setTimeout(function() {{
            document.querySelectorAll('[id^="chart-"]').forEach(function(el) {{
                if (el._fullLayout) Plotly.Plots.resize(el);
            }});
        }}, 200);
    }});
}});

// ── Scroll Reveal ──
const chapters = document.querySelectorAll('.chapter');
const observer = new IntersectionObserver((entries) => {{
    entries.forEach(e => {{
        if (e.isIntersecting) {{
            e.target.classList.add('visible');
            // resize plotly charts when they become visible
            const charts = e.target.querySelectorAll('[id^="chart-"]');
            charts.forEach(c => Plotly.Plots.resize(c));
        }}
    }});
}}, {{ threshold: 0.1, rootMargin: '0px 0px -40px 0px' }});
chapters.forEach(c => observer.observe(c));

// ── Active Nav ──
const links = document.querySelectorAll('.nav-link');
const sects = document.querySelectorAll('.chapter[id]');
const navObs = new IntersectionObserver((entries) => {{
    entries.forEach(e => {{
        if (e.isIntersecting) {{
            links.forEach(l => l.classList.remove('active'));
            const a = document.querySelector('.nav-link[href="#' + e.target.id + '"]');
            if (a) a.classList.add('active');
        }}
    }});
}}, {{ threshold: 0.35 }});
sects.forEach(s => navObs.observe(s));

// ── Falling Leaves (one-time on load) ──
(function() {{
    const container = document.getElementById('leaves');
    const leafSVGs = [
        `<svg width="20" height="22" viewBox="0 0 20 22" fill="none"><path d="M10 0C10 0 2 8 2 14c0 4 3.5 7 8 7s8-3 8-7C18 8 10 0 10 0z" fill="#2a3f5c" opacity="0.55"/></svg>`,
        `<svg width="18" height="20" viewBox="0 0 18 20" fill="none"><ellipse cx="9" cy="10" rx="7" ry="10" fill="#d4a017" opacity="0.45" transform="rotate(15 9 10)"/></svg>`,
        `<svg width="16" height="18" viewBox="0 0 16 18" fill="none"><path d="M8 0C5 4 0 8 0 12c0 3 3 6 8 6s8-3 8-6C16 8 11 4 8 0z" fill="#e8b616" opacity="0.5"/></svg>`,
        `<svg width="14" height="16" viewBox="0 0 14 16" fill="none"><path d="M7 0C4 3 0 6 0 10c0 3 3 6 7 6s7-3 7-6C14 6 10 3 7 0z" fill="#0f1a2e" opacity="0.35"/></svg>`,
    ];

    for (let i = 0; i < 18; i++) {{
        const leaf = document.createElement('div');
        leaf.className = 'leaf';
        leaf.innerHTML = leafSVGs[i % leafSVGs.length];
        leaf.style.left = (Math.random() * 100) + 'vw';
        leaf.style.setProperty('--drift', (Math.random() * 200 - 100) + 'px');
        leaf.style.setProperty('--spin', (Math.random() * 720 - 360) + 'deg');
        leaf.style.animationDuration = (4 + Math.random() * 5) + 's';
        leaf.style.animationDelay = (Math.random() * 4) + 's';
        container.appendChild(leaf);
    }}

    // remove after animation
    setTimeout(() => container.remove(), 12000);
}})();
</script>
</body>
</html>"""

output_path = OUTPUT_PATH
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as f:
    f.write(html)

print(f"Dashboard saved to {output_path}")
print(f"File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
