"""Interactive Plotly visualizations — keyword trends, sunburst, network."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter, defaultdict
import re

FIGDIR = "src/analysis/figures"
df = pd.read_parquet("src/analysis/data_cache/aat_museum_subset.parquet")
scope_notes = df[df["scope_note"].notna()]

# ─── 1. Sunburst — Facet → Top Parent → Term count ───

top_parents = df.groupby(["hierarchy", "parent_term"]).size().reset_index(name="count")
top_parents = top_parents.sort_values("count", ascending=False).groupby("hierarchy").head(5)

fig = px.sunburst(
    top_parents, path=["hierarchy", "parent_term"], values="count",
    color="hierarchy", color_discrete_sequence=px.colors.qualitative.Set3,
    title="AAT Hierarchy — Facets and Top Parent Categories"
)
fig.update_layout(width=900, height=900)
fig.write_html(f"{FIGDIR}/11_sunburst.html")
print("✓ 11_sunburst.html")

# ─── 2. Keyword × Century Diagonal Heatmap ───

century_pattern = re.compile(r'(\d+)(?:st|nd|rd|th)\s+centur', re.IGNORECASE)

top_words_in_terms = Counter()
stopwords = {"and", "of", "the", "for", "in", "with", "a", "an", "to", "or", "by", "on", "at", "as", "is"}
for term in df["preferred_term"].str.lower():
    top_words_in_terms.update(w for w in term.split() if w not in stopwords and len(w) > 2)

top_30_keywords = [w for w, _ in top_words_in_terms.most_common(40)]

keyword_century = defaultdict(lambda: Counter())
for _, row in scope_notes.iterrows():
    centuries_found = [int(m.group(1)) for m in century_pattern.finditer(row["scope_note"]) if 1 <= int(m.group(1)) <= 21]
    if not centuries_found:
        continue
    term_words = set(row["preferred_term"].lower().split())
    for kw in top_30_keywords:
        if kw in term_words:
            for c in centuries_found:
                keyword_century[kw][c] += 1

keywords_with_data = [kw for kw in top_30_keywords if sum(keyword_century[kw].values()) >= 5][:30]
centuries = list(range(3, 21))

matrix = []
for kw in keywords_with_data:
    row = [keyword_century[kw].get(c, 0) for c in centuries]
    matrix.append(row)

heatmap_df = pd.DataFrame(matrix, index=keywords_with_data,
                          columns=[f"{c}th c." for c in centuries])

fig = go.Figure(data=go.Heatmap(
    z=heatmap_df.values,
    x=heatmap_df.columns.tolist(),
    y=heatmap_df.index.tolist(),
    colorscale="YlOrRd",
    hoverongaps=False,
    hovertemplate="Keyword: %{y}<br>Century: %{x}<br>Mentions: %{z}<extra></extra>"
))
fig.update_layout(
    title="Keyword Trends Across Centuries (from Scope Notes)",
    xaxis_title="Century", yaxis_title="Keyword",
    width=1200, height=800,
    yaxis=dict(autorange="reversed")
)
fig.write_html(f"{FIGDIR}/12_keyword_century_heatmap.html")
print("✓ 12_keyword_century_heatmap.html")

# ─── 3. Treemap — Full hierarchy drill-down ───

tree_data = df.groupby(["hierarchy", "parent_term"]).agg(
    count=("subject_id", "size"),
    avg_variants=("variant_terms", lambda x: x.apply(len).mean())
).reset_index()

fig = px.treemap(
    tree_data, path=["hierarchy", "parent_term"], values="count",
    color="avg_variants", color_continuous_scale="Viridis",
    title="AAT Taxonomy Treemap — Size = Terms, Color = Avg Variant Richness",
    hover_data={"avg_variants": ":.1f"}
)
fig.update_layout(width=1200, height=800)
fig.write_html(f"{FIGDIR}/13_treemap.html")
print("✓ 13_treemap.html")

# ─── 4. Geographic × Facet Stacked Area ───

geo_patterns = {
    "European": re.compile(r'\b(europe|european|french|italian|english|german|spanish|dutch|greek|roman|british)\b', re.I),
    "Asian": re.compile(r'\b(asia|asian|chinese|japanese|indian|korean|persian|thai)\b', re.I),
    "African": re.compile(r'\b(africa|african|egyptian|saharan)\b', re.I),
    "Americas": re.compile(r'\b(america|american|native american|mesoamerican|pre-columbian)\b', re.I),
    "Middle Eastern": re.compile(r'\b(middle east|islamic|ottoman|arab|mesopotamian)\b', re.I),
}

geo_century = defaultdict(lambda: Counter())
for _, row in scope_notes.iterrows():
    centuries_found = [int(m.group(1)) for m in century_pattern.finditer(row["scope_note"]) if 1 <= int(m.group(1)) <= 21]
    if not centuries_found:
        continue
    for region, pattern in geo_patterns.items():
        if pattern.search(row["scope_note"]):
            for c in centuries_found:
                geo_century[region][c] += 1

geo_time_data = []
for region in geo_patterns:
    for c in range(3, 21):
        geo_time_data.append({"Region": region, "Century": f"{c}th", "Mentions": geo_century[region].get(c, 0)})

geo_time_df = pd.DataFrame(geo_time_data)

fig = px.area(
    geo_time_df, x="Century", y="Mentions", color="Region",
    title="Geographic Focus Across Centuries — When Was Each Region Referenced?",
    color_discrete_sequence=px.colors.qualitative.Bold
)
fig.update_layout(width=1100, height=600, hovermode="x unified")
fig.write_html(f"{FIGDIR}/14_geo_centuries.html")
print("✓ 14_geo_centuries.html")

# ─── 5. Scope Note Length vs Variant Count Scatter ───

df_scatter = df.copy()
df_scatter["variant_count"] = df_scatter["variant_terms"].apply(len)
df_scatter["scope_len"] = df_scatter["scope_note"].str.len().fillna(0)
df_scatter = df_scatter[df_scatter["scope_len"] > 0].sample(5000, random_state=42)

fig = px.scatter(
    df_scatter, x="variant_count", y="scope_len", color="hierarchy",
    hover_name="preferred_term",
    title="Scope Note Length vs. Variant Count — Does Richer Description = More Translations?",
    labels={"variant_count": "Number of Variant Terms", "scope_len": "Scope Note Length (chars)"},
    opacity=0.6, color_discrete_sequence=px.colors.qualitative.Set3
)
fig.update_layout(width=1100, height=700)
fig.write_html(f"{FIGDIR}/15_scatter_scope_variants.html")
print("✓ 15_scatter_scope_variants.html")

# ─── 6. Top Keywords Bar Race (by facet) ───

facet_word_data = []
for facet in df["hierarchy"].value_counts().head(6).index:
    facet_terms = df[df["hierarchy"] == facet]["preferred_term"].str.lower()
    freq = Counter()
    for t in facet_terms:
        freq.update(w for w in t.split() if w not in stopwords and len(w) > 2)
    for word, count in freq.most_common(10):
        facet_word_data.append({"Facet": facet, "Word": word, "Count": count})

fwd = pd.DataFrame(facet_word_data)

fig = px.bar(
    fwd, x="Count", y="Word", color="Facet", orientation="h",
    facet_col="Facet", facet_col_wrap=3,
    title="Top 10 Keywords per Facet",
    color_discrete_sequence=px.colors.qualitative.Set3
)
fig.update_layout(width=1400, height=900, showlegend=False)
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1][:25]))
fig.write_html(f"{FIGDIR}/16_facet_keywords.html")
print("✓ 16_facet_keywords.html")

print("\n✅ All interactive visualizations saved to src/analysis/figures/")
