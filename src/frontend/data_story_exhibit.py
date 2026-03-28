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
HERO_IMAGE = Path("src/frontend/mills.jpg")
CENTURY_PATTERN = re.compile(r"(\d+)(?:st|nd|rd|th)\s+centur", re.IGNORECASE)
STOPWORDS = {
    "and",
    "of",
    "the",
    "for",
    "in",
    "with",
    "a",
    "an",
    "to",
    "or",
    "by",
    "on",
    "at",
    "as",
    "is",
}
PALETTE = [
    "#355c4d",
    "#6b9e8a",
    "#9d6b2f",
    "#c4956a",
    "#7b8f6a",
    "#7c6245",
    "#597765",
    "#d4b089",
]


def load_dataset() -> pd.DataFrame:
    dataframe = pd.read_parquet(DATA_PATH).copy()
    dataframe["variant_count"] = dataframe["variant_terms"].apply(len)
    dataframe["scope_len"] = dataframe["scope_note"].fillna("").str.len()
    return dataframe


def compute_tree_depths(dataframe: pd.DataFrame) -> pd.Series:
    parent_map = dict(zip(dataframe["subject_id"], dataframe["parent_id"]))
    memo: dict[int, int] = {}

    def get_depth(subject_id: int) -> int:
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


def build_stat_cards(dataframe: pd.DataFrame) -> list[dict[str, str]]:
    scope_coverage = (dataframe["scope_note"].notna().mean()) * 100
    multilingual_terms = (dataframe["variant_count"] >= 5).sum()
    return [
        {"label": "Terms in play", "value": f"{len(dataframe):,}", "detail": "museum-ready AAT subset rows"},
        {
            "label": "Facets represented",
            "value": f"{dataframe['hierarchy'].nunique()}",
            "detail": "distinct conceptual neighborhoods",
        },
        {
            "label": "Scope note coverage",
            "value": f"{scope_coverage:.1f}%",
            "detail": "terms with curator-friendly descriptions",
        },
        {
            "label": "Multilingual richness",
            "value": f"{multilingual_terms:,}",
            "detail": "terms carrying 5+ variants or translations",
        },
    ]


def render_stat_cards(cards: list[dict[str, str]]) -> str:
    card_markup = "".join(
        (
            "<div class='stat-card'>"
            f"<div class='stat-label'>{card['label']}</div>"
            f"<div class='stat-value'>{card['value']}</div>"
            f"<div class='stat-detail'>{card['detail']}</div>"
            "</div>"
        )
        for card in cards
    )
    return f"<div class='stat-grid'>{card_markup}</div>"


def build_facet_river(dataframe: pd.DataFrame) -> go.Figure:
    counts = dataframe["hierarchy"].value_counts().reset_index()
    counts.columns = ["Facet", "Terms"]
    counts["Share"] = counts["Terms"] / counts["Terms"].sum()
    fig = px.bar(
        counts,
        x="Terms",
        y="Facet",
        orientation="h",
        color="Share",
        color_continuous_scale=["#f3efe7", "#9d6b2f", "#355c4d"],
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        coloraxis_showscale=False,
        title="Facet River — where the collection’s weight sits",
        xaxis_title="Term count",
        yaxis_title="",
        height=430,
    )
    fig.update_traces(
        texttemplate="%{x:,}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,} terms<extra></extra>",
    )
    return fig


def build_taxonomy_sunburst(dataframe: pd.DataFrame) -> go.Figure:
    top_parents = (
        dataframe.groupby(["hierarchy", "parent_term"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .groupby("hierarchy")
        .head(5)
    )
    fig = px.sunburst(
        top_parents,
        path=["hierarchy", "parent_term"],
        values="count",
        color="hierarchy",
        color_discrete_sequence=PALETTE,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        title="Taxonomy Constellation — the biggest parent clusters",
        height=430,
    )
    return fig


def build_century_heatmap(dataframe: pd.DataFrame) -> go.Figure:
    scope_notes = dataframe[dataframe["scope_note"].notna()]
    facet_century = defaultdict(lambda: Counter())
    for _, row in scope_notes.iterrows():
        for match in CENTURY_PATTERN.finditer(row["scope_note"]):
            century = int(match.group(1))
            if 3 <= century <= 20:
                facet_century[row["hierarchy"]][century] += 1

    facet_order = dataframe["hierarchy"].value_counts().index.tolist()
    centuries = list(range(3, 21))
    z_data = [[facet_century[facet].get(century, 0) for century in centuries] for facet in facet_order]

    fig = go.Figure(
        go.Heatmap(
            z=z_data,
            x=[f"{century}th" for century in centuries],
            y=facet_order,
            colorscale=[
                [0, "#f3efe7"],
                [0.2, "#dce9e2"],
                [0.5, "#6b9e8a"],
                [0.8, "#355c4d"],
                [1, "#1a3329"],
            ],
            hovertemplate="%{y}<br>%{x} century: <b>%{z}</b> mentions<extra></extra>",
        )
    )
    fig.update_layout(
        title="Time Machine — when each facet shows up in scope notes",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        height=430,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(side="top"),
    )
    return fig


def build_language_treemap(dataframe: pd.DataFrame) -> go.Figure:
    script_patterns = {
        "Latin alphabet": re.compile(r"[A-Za-z]"),
        "Chinese characters": re.compile(r"[\u4e00-\u9fff]"),
        "Arabic script": re.compile(r"[\u0600-\u06FF]"),
    }
    buckets = Counter()
    for variants in dataframe["variant_terms"]:
        joined = " ".join(variants)
        matched = False
        for label, pattern in script_patterns.items():
            if pattern.search(joined):
                buckets[label] += 1
                matched = True
        if not matched:
            buckets["Other / none detected"] += 1

    script_df = pd.DataFrame(
        [{"bucket": bucket, "count": count} for bucket, count in buckets.items()]
    ).sort_values("count", ascending=False)
    fig = px.treemap(
        script_df,
        path=["bucket"],
        values="count",
        color="count",
        color_continuous_scale=["#f5ead7", "#c4956a", "#355c4d"],
    )
    fig.update_layout(
        title="Language Garden — script coverage across variant terms",
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        height=430,
        coloraxis_showscale=False,
    )
    return fig


def build_complexity_scatter(dataframe: pd.DataFrame) -> go.Figure:
    sampled = dataframe[dataframe["scope_len"] > 0].copy()
    if len(sampled) > 4000:
        sampled = sampled.sample(4000, random_state=42)
    fig = px.scatter(
        sampled,
        x="variant_count",
        y="scope_len",
        color="hierarchy",
        hover_name="preferred_term",
        opacity=0.7,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        title="Complexity Field — do richer descriptions travel with more variants?",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        legend_title_text="Facet",
        height=460,
        xaxis_title="Variant term count",
        yaxis_title="Scope note length",
    )
    return fig


def build_depth_violin(dataframe: pd.DataFrame) -> go.Figure:
    depth_df = dataframe.copy()
    depth_df["tree_depth"] = compute_tree_depths(depth_df)
    facet_order = depth_df["hierarchy"].value_counts().index.tolist()
    fig = px.violin(
        depth_df,
        x="hierarchy",
        y="tree_depth",
        color="hierarchy",
        category_orders={"hierarchy": facet_order},
        color_discrete_sequence=PALETTE,
        box=True,
        points=False,
    )
    fig.update_layout(
        title="Depth Chorus — some facets nest deeper than others",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        showlegend=False,
        height=460,
        xaxis_title="",
        yaxis_title="Hierarchy depth",
    )
    return fig


def build_keyword_century_heatmap(dataframe: pd.DataFrame) -> go.Figure:
    scope_notes = dataframe[dataframe["scope_note"].notna()]
    top_words = Counter()
    for term in dataframe["preferred_term"].str.lower():
        top_words.update(word for word in term.split() if word not in STOPWORDS and len(word) > 2)

    centuries = list(range(3, 21))
    keyword_century = defaultdict(lambda: Counter())
    top_keywords = [word for word, _ in top_words.most_common(40)]
    for _, row in scope_notes.iterrows():
        found_centuries = [
            int(match.group(1))
            for match in CENTURY_PATTERN.finditer(row["scope_note"])
            if 3 <= int(match.group(1)) <= 20
        ]
        if not found_centuries:
            continue
        term_words = set(row["preferred_term"].lower().split())
        for keyword in top_keywords:
            if keyword in term_words:
                for century in found_centuries:
                    keyword_century[keyword][century] += 1

    ranked_keywords = [word for word in top_keywords if sum(keyword_century[word].values()) >= 5][:20]
    z_data = [[keyword_century[word].get(century, 0) for century in centuries] for word in ranked_keywords]
    fig = go.Figure(
        go.Heatmap(
            z=z_data,
            x=[f"{century}th" for century in centuries],
            y=ranked_keywords,
            colorscale=[[0, "#f3efe7"], [0.2, "#f7e8ce"], [0.5, "#c4956a"], [0.8, "#9d6b2f"], [1, "#5a3a12"]],
            hoverongaps=False,
            hovertemplate="<b>%{y}</b> in the %{x} century: %{z} mentions<extra></extra>",
        )
    )
    fig.update_layout(
        title="Keyword Time Weave — when words peak across centuries",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        height=460,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(side="top"),
    )
    return fig


def build_geography_area(dataframe: pd.DataFrame) -> go.Figure:
    scope_notes = dataframe[dataframe["scope_note"].notna()]
    geo_patterns = {
        "European": re.compile(r"\b(europe|european|french|italian|english|german|spanish|dutch|greek|roman|british)\b", re.I),
        "Asian": re.compile(r"\b(asia|asian|chinese|japanese|indian|korean|persian|thai)\b", re.I),
        "African": re.compile(r"\b(africa|african|egyptian|saharan)\b", re.I),
        "Americas": re.compile(r"\b(america|american|native american|mesoamerican|pre-columbian)\b", re.I),
        "Middle Eastern": re.compile(r"\b(middle east|islamic|ottoman|arab|mesopotamian)\b", re.I),
    }
    centuries = list(range(3, 21))
    geo_century = defaultdict(lambda: Counter())
    for _, row in scope_notes.iterrows():
        found_centuries = [
            int(match.group(1))
            for match in CENTURY_PATTERN.finditer(row["scope_note"])
            if 3 <= int(match.group(1)) <= 20
        ]
        if not found_centuries:
            continue
        for region, pattern in geo_patterns.items():
            if pattern.search(row["scope_note"]):
                for century in found_centuries:
                    geo_century[region][century] += 1

    geo_rows = [
        {"Region": region, "Century": f"{century}th", "Mentions": geo_century[region].get(century, 0)}
        for region in geo_patterns
        for century in centuries
    ]
    fig = px.area(
        pd.DataFrame(geo_rows),
        x="Century",
        y="Mentions",
        color="Region",
        color_discrete_sequence=["#355c4d", "#6b9e8a", "#9d6b2f", "#c4956a", "#8b7355"],
    )
    fig.update_layout(
        title="Geographic Drift — how regional emphasis shifts over time",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        height=430,
        hovermode="x unified",
    )
    return fig


def build_script_pie(dataframe: pd.DataFrame) -> go.Figure:
    cjk_pattern = re.compile(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]")
    arabic_pattern = re.compile(r"[\u0600-\u06ff]")
    cyrillic_pattern = re.compile(r"[\u0400-\u04ff]")
    counts = Counter()
    for variants in dataframe["variant_terms"]:
        for variant in variants:
            text = str(variant)
            if cjk_pattern.search(text):
                counts["CJK"] += 1
            elif arabic_pattern.search(text) or cyrillic_pattern.search(text):
                counts["Other"] += 1
            else:
                counts["Latin"] += 1

    fig = go.Figure(
        go.Pie(
            labels=list(counts.keys()),
            values=list(counts.values()),
            hole=0,
            textinfo="label+percent",
            marker=dict(colors=["#355c4d", "#9d6b2f", "#b8a898"], line=dict(color="#f3efe7", width=3)),
            hovertemplate="<b>%{label}</b><br>%{value:,} terms (%{percent})<extra></extra>",
            pull=[0, 0.05, 0.08],
        )
    )
    fig.update_layout(
        title="Language Coverage — scripts across 334K variants",
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        height=380,
        showlegend=False,
    )
    return fig


def build_keyword_wall(dataframe: pd.DataFrame) -> str:
    top_facets = dataframe["hierarchy"].value_counts().head(6).index.tolist()
    cards = []
    for facet in top_facets:
        facet_terms = dataframe.loc[dataframe["hierarchy"] == facet, "preferred_term"].str.lower()
        words = Counter()
        for term in facet_terms:
            words.update(word for word in term.split() if word not in STOPWORDS and len(word) > 2)
        top_words = ", ".join(word for word, _ in words.most_common(6))
        cards.append(
            "<div class='keyword-card'>"
            f"<div class='keyword-facet'>{facet}</div>"
            f"<div class='keyword-words'>{top_words}</div>"
            "</div>"
        )
    return "<div class='keyword-wall'>" + "".join(cards) + "</div>"


def build_curator_notes() -> str:
    notes = [
        ("Atlas view", "Use structural plots to show the taxonomy as a map instead of a slideshow."),
        ("Time lens", "Let visitors see when centuries cluster, revealing historical bias in the corpus."),
        ("Language garden", "Make multilingual variants feel alive rather than buried in CSV-style metadata."),
        ("Complexity field", "Show how descriptive richness and synonym breadth move together or diverge."),
    ]
    return "<div class='note-grid'>" + "".join(
        (
            "<div class='note-card'>"
            f"<h3>{title}</h3>"
            f"<p>{description}</p>"
            "</div>"
        )
        for title, description in notes
    ) + "</div>"


def build_story_notes() -> str:
    sections = [
        ("The collection", "Furnishings & Equipment accounts for 36.5% of the subset, so object culture dominates the corpus."),
        ("Through time", "The 19th century spikes hardest, turning industrial-era vocabulary into the loudest historical layer."),
        ("Depth", "Hierarchy depth varies wildly — shallow furnishings versus biological chains that run 11 levels deep."),
        ("Languages", "The thesaurus is multilingual at scale: Latin scripts dominate, but CJK variants still make up a striking 11.3%."),
    ]
    return "<div class='story-grid'>" + "".join(
        (
            "<div class='story-card'>"
            f"<h3>{title}</h3>"
            f"<p>{description}</p>"
            "</div>"
        )
        for title, description in sections
    ) + "</div>"


def build_figure_gallery() -> list[tuple[str, str]]:
    featured = [
        ("Facet Donut", FIGURES_DIR / "01_facet_donut.png"),
        ("Century Heatmap", FIGURES_DIR / "03_century_heatmap.png"),
        ("Hierarchy Depth", FIGURES_DIR / "05_depth_violin.png"),
        ("Language Scripts", FIGURES_DIR / "07_language_scripts.png"),
        ("Facet Similarity", FIGURES_DIR / "19_facet_similarity.png"),
        ("Taxonomy Network", FIGURES_DIR / "20_taxonomy_network.png"),
    ]
    return [(str(path), title) for title, path in featured if path.exists()]


def create_interface() -> gr.Blocks:
    dataframe = load_dataset()
    stats_html = render_stat_cards(build_stat_cards(dataframe))
    keyword_wall = build_keyword_wall(dataframe)
    curator_notes = build_curator_notes()
    story_notes = build_story_notes()
    gallery_images = build_figure_gallery()

    css = """
    :root {
        --bg: linear-gradient(180deg, #f3efe7 0%, #ebe3d3 52%, #f7f2ea 100%);
        --surface: rgba(255, 251, 246, 0.88);
        --surface-strong: rgba(255, 251, 246, 0.96);
        --border: rgba(53, 92, 77, 0.18);
        --ink: #2b241f;
        --muted: #6c6155;
        --accent: #355c4d;
        --warm: #9d6b2f;
        --shadow: 0 20px 40px rgba(43, 36, 31, 0.08);
    }
    .gradio-container { background: var(--bg) !important; color: var(--ink); }
    .app-shell { max-width: 1380px; margin: 0 auto; padding: 28px 18px 48px; }
    .hero-card, .section-card, .gradio-plot, .gradio-gallery {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 24px;
        box-shadow: var(--shadow);
    }
    .hero-card { padding: 28px; margin-bottom: 18px; }
    .hero-card h1 { margin: 0 0 10px; font-size: 2.7rem; line-height: 1.05; }
    .hero-card p { margin: 0; max-width: 900px; color: var(--muted); font-size: 1.05rem; }
    .section-head { margin: 12px 4px 10px; }
    .section-head h2 { margin: 0 0 4px; font-size: 1.55rem; }
    .section-head p { margin: 0; color: var(--muted); }
    .stat-grid, .note-grid, .keyword-wall {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
    }
    .story-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
    }
    .stat-card, .note-card, .keyword-card {
        background: var(--surface-strong);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 18px;
    }
    .story-card {
        background: linear-gradient(180deg, rgba(255,251,246,0.98), rgba(244,236,223,0.95));
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 20px;
        box-shadow: var(--shadow);
    }
    .stat-label, .keyword-facet { color: var(--muted); font-size: 0.92rem; }
    .stat-value { font-size: 2rem; font-weight: 700; color: var(--accent); margin-top: 6px; }
    .stat-detail, .keyword-words, .note-card p { color: var(--muted); margin-top: 8px; line-height: 1.45; }
    .note-card h3 { margin: 0; font-size: 1.02rem; }
    .story-card h3 { margin: 0; font-size: 1.08rem; color: var(--accent); }
    .story-card p { margin: 10px 0 0; color: var(--muted); line-height: 1.55; }
    .keyword-words { color: var(--ink); font-weight: 600; }
    .hero-media img {
        width: 100%;
        max-height: 320px;
        object-fit: cover;
        border-radius: 22px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }
    """

    theme = gr.themes.Soft(primary_hue="emerald", secondary_hue="amber", neutral_hue="stone").set(
        body_background_fill="transparent",
        block_background_fill="rgba(255,255,255,0)",
        block_border_width="0px",
    )

    with gr.Blocks(css=css, theme=theme, title="Mills Museum Data Exhibit") as demo:
        with gr.Column(elem_classes=["app-shell"]):
            with gr.Row():
                with gr.Column(scale=3):
                    gr.HTML(
                        """
                        <section class="hero-card">
                          <h1>Mills Museum Data Exhibit</h1>
                          <p>
                            This merged interface combines the new exhibit-style frontend with the deeper report logic:
                            the collection is explored as a spatial, temporal, and multilingual system rather than a list of screenshots.
                          </p>
                        </section>
                        """
                    )
                with gr.Column(scale=2, elem_classes=["hero-media"]):
                    if HERO_IMAGE.exists():
                        gr.Image(value=str(HERO_IMAGE), show_label=False, interactive=False, container=False)

            with gr.Tabs():
                with gr.Tab("Exhibit"):
                    gr.HTML(stats_html)
                    gr.HTML(
                        """
                        <div class="section-head">
                          <h2>Curatorial Framing</h2>
                          <p>The website should feel like it is in dialogue with the dataset, not just hanging screenshots on a wall.</p>
                        </div>
                        """
                    )
                    gr.HTML(curator_notes)
                    gr.HTML(
                        """
                        <div class="section-head">
                          <h2>Atlas Room</h2>
                          <p>Start with structure: where the collection’s conceptual mass lives, and which parent clusters dominate.</p>
                        </div>
                        """
                    )
                    with gr.Row():
                        gr.Plot(value=build_facet_river(dataframe), container=True)
                        gr.Plot(value=build_taxonomy_sunburst(dataframe), container=True)

                    gr.HTML(
                        """
                        <div class="section-head">
                          <h2>Time + Language Rooms</h2>
                          <p>Let viewers move between historical emphasis and multilingual breadth rather than scrolling through isolated cards.</p>
                        </div>
                        """
                    )
                    with gr.Row():
                        gr.Plot(value=build_century_heatmap(dataframe), container=True)
                        gr.Plot(value=build_language_treemap(dataframe), container=True)

                    gr.HTML(
                        """
                        <div class="section-head">
                          <h2>Complexity Room</h2>
                          <p>These views show how deeply terms nest and whether dense descriptions correlate with broader lexical coverage.</p>
                        </div>
                        """
                    )
                    with gr.Row():
                        gr.Plot(value=build_complexity_scatter(dataframe), container=True)
                        gr.Plot(value=build_depth_violin(dataframe), container=True)

                    gr.HTML(
                        """
                        <div class="section-head">
                          <h2>Facet Vocabulary Wall</h2>
                          <p>Instead of generic descriptions, surface the language each facet actually uses most.</p>
                        </div>
                        """
                    )
                    gr.HTML(keyword_wall)

                with gr.Tab("Story Report"):
                    gr.HTML(
                        """
                        <div class="section-head">
                          <h2>Seven dense findings, one launch path</h2>
                          <p>This tab pulls the strongest report-style findings into the same interface so you do not have to switch between apps.</p>
                        </div>
                        """
                    )
                    gr.HTML(story_notes)
                    with gr.Row():
                        gr.Plot(value=build_century_heatmap(dataframe), container=True)
                        gr.Plot(value=build_keyword_century_heatmap(dataframe), container=True)
                    with gr.Row():
                        gr.Plot(value=build_depth_violin(dataframe), container=True)
                        gr.Plot(value=build_geography_area(dataframe), container=True)
                    with gr.Row():
                        gr.Plot(value=build_script_pie(dataframe), container=True)
                        gr.Plot(value=build_taxonomy_sunburst(dataframe), container=True)

                    if gallery_images:
                        gr.HTML(
                            """
                            <div class="section-head">
                              <h2>Rendered Reference Figures</h2>
                              <p>The static outputs remain here as supporting evidence, but the live report above is the main merged experience.</p>
                            </div>
                            """
                        )
                        gr.Gallery(value=gallery_images, columns=3, rows=2, object_fit="contain", height="auto")

    return demo


demo = create_interface()


def main() -> None:
    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
