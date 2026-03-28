"""Static visualizations — matplotlib, seaborn, wordcloud."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter, defaultdict
import re
import textwrap

sns.set_theme(style="whitegrid", font_scale=1.1)
FIGDIR = "src/analysis/figures"

df = pd.read_parquet("src/analysis/data_cache/aat_museum_subset.parquet")

PALETTE = sns.color_palette("Set3", 12)
FACET_ORDER = df["hierarchy"].value_counts().index.tolist()
FACET_COLORS = {f: PALETTE[i] for i, f in enumerate(FACET_ORDER)}

# ─── 1. Facet Distribution Donut ───

fig, ax = plt.subplots(figsize=(10, 10))
counts = df["hierarchy"].value_counts()
wedges, texts, autotexts = ax.pie(
    counts.values, labels=None, autopct=lambda p: f"{p:.1f}%" if p > 2 else "",
    colors=[FACET_COLORS[f] for f in counts.index],
    startangle=90, pctdistance=0.82, wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2)
)
ax.legend(
    [textwrap.fill(f"{name} ({count:,})", 30) for name, count in zip(counts.index, counts.values)],
    loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9
)
ax.set_title("AAT Museum Subset — Facet Distribution", fontsize=16, fontweight="bold", pad=20)
for t in autotexts:
    t.set_fontsize(9)
    t.set_fontweight("bold")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/01_facet_donut.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 01_facet_donut.png")

# ─── 2. Word Cloud of Preferred Terms ───

term_freq = Counter()
stopwords = {"and", "of", "the", "for", "in", "with", "a", "an", "to", "or", "by", "on", "at"}
for term in df["preferred_term"].str.lower():
    words = [w for w in term.split() if w not in stopwords and len(w) > 2]
    term_freq.update(words)

wc = WordCloud(
    width=1600, height=800, background_color="white",
    colormap="viridis", max_words=200, min_font_size=8,
    prefer_horizontal=0.7, contour_width=2, contour_color="steelblue"
)
wc.generate_from_frequencies(term_freq)
fig, ax = plt.subplots(figsize=(16, 8))
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")
ax.set_title("Most Common Words in AAT Preferred Terms", fontsize=18, fontweight="bold", pad=15)
fig.savefig(f"{FIGDIR}/02_term_wordcloud.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 02_term_wordcloud.png")

# ─── 3. Century Heatmap from Scope Notes ───

scope_notes = df[["hierarchy", "scope_note"]].dropna(subset=["scope_note"])
century_pattern = re.compile(r'(\d+)(?:st|nd|rd|th)\s+centur', re.IGNORECASE)

facet_century = defaultdict(lambda: Counter())
for _, row in scope_notes.iterrows():
    for match in century_pattern.finditer(row["scope_note"]):
        c = int(match.group(1))
        if 1 <= c <= 21:
            facet_century[row["hierarchy"]][c] += 1

centuries = list(range(1, 22))
facets_with_data = [f for f in FACET_ORDER if sum(facet_century[f].values()) > 0]

matrix = []
for f in facets_with_data:
    row = [facet_century[f].get(c, 0) for c in centuries]
    matrix.append(row)

heatmap_df = pd.DataFrame(matrix, index=facets_with_data,
                          columns=[f"{c}th c." for c in centuries])

fig, ax = plt.subplots(figsize=(18, 8))
sns.heatmap(heatmap_df, cmap="YlOrRd", annot=True, fmt="d", linewidths=0.5,
            ax=ax, cbar_kws={"label": "Mentions"})
ax.set_title("Century References in Scope Notes by Facet", fontsize=16, fontweight="bold")
ax.set_xlabel("Century", fontsize=12)
ax.set_ylabel("")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/03_century_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 03_century_heatmap.png")

# ─── 4. Geographic Mentions Radar ───

geo_patterns = {
    "European": re.compile(r'\b(europe|european|french|italian|english|german|spanish|dutch|greek|roman|british|scandinavian)\b', re.I),
    "Asian": re.compile(r'\b(asia|asian|chinese|japanese|indian|korean|persian|thai|vietnamese|indonesian|tibetan)\b', re.I),
    "African": re.compile(r'\b(africa|african|egyptian|north africa|west africa|saharan)\b', re.I),
    "Americas": re.compile(r'\b(america|american|native american|mesoamerican|south american|pre-columbian)\b', re.I),
    "Middle Eastern": re.compile(r'\b(middle east|islamic|ottoman|arab|mesopotamian|babylonian|assyrian)\b', re.I),
    "Oceanian": re.compile(r'\b(pacific|polynesian|melanesian|oceanian|australian|aboriginal)\b', re.I),
}

facet_geo = defaultdict(lambda: Counter())
for _, row in scope_notes.iterrows():
    for region, pattern in geo_patterns.items():
        if pattern.search(row["scope_note"]):
            facet_geo[row["hierarchy"]][region] += 1

regions = list(geo_patterns.keys())
geo_matrix = []
for f in FACET_ORDER[:6]:
    geo_matrix.append([facet_geo[f].get(r, 0) for r in regions])

geo_df = pd.DataFrame(geo_matrix, index=FACET_ORDER[:6], columns=regions)

fig, ax = plt.subplots(figsize=(12, 7))
geo_df.plot(kind="barh", stacked=True, ax=ax, colormap="Set2", edgecolor="white", linewidth=0.5)
ax.set_title("Geographic References by Facet (from Scope Notes)", fontsize=14, fontweight="bold")
ax.set_xlabel("Number of Mentions")
ax.legend(title="Region", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/04_geo_by_facet.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 04_geo_by_facet.png")

# ─── 5. Tree Depth Distribution by Facet ───

parent_map = dict(zip(df["subject_id"], df["parent_id"]))
all_ids = set(df["subject_id"])

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

fig, ax = plt.subplots(figsize=(14, 7))
depth_data = []
for facet in FACET_ORDER[:6]:
    facet_depths = df[df["hierarchy"] == facet]["tree_depth"]
    depth_data.append(facet_depths)

parts = ax.violinplot(depth_data, positions=range(len(FACET_ORDER[:6])),
                      showmeans=True, showmedians=True)
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(FACET_COLORS[FACET_ORDER[i]])
    pc.set_alpha(0.7)

ax.set_xticks(range(len(FACET_ORDER[:6])))
ax.set_xticklabels([textwrap.fill(f, 15) for f in FACET_ORDER[:6]], fontsize=9)
ax.set_ylabel("Tree Depth")
ax.set_title("Tree Depth Distribution by Facet (Top 6)", fontsize=14, fontweight="bold")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/05_depth_violin.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 05_depth_violin.png")

# ─── 6. Variant Term Count Distribution ───

df["variant_count"] = df["variant_terms"].apply(len)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

axes[0].hist(df["variant_count"], bins=50, color="steelblue", edgecolor="white", alpha=0.8)
axes[0].set_xlabel("Number of Variant Terms")
axes[0].set_ylabel("Count")
axes[0].set_title("Distribution of Variant Term Count", fontweight="bold")
axes[0].axvline(df["variant_count"].median(), color="red", linestyle="--", label=f"Median: {df['variant_count'].median():.0f}")
axes[0].axvline(df["variant_count"].mean(), color="orange", linestyle="--", label=f"Mean: {df['variant_count'].mean():.1f}")
axes[0].legend()

facet_medians = df.groupby("hierarchy")["variant_count"].median().sort_values(ascending=True)
colors = [FACET_COLORS[f] for f in facet_medians.index]
axes[1].barh(range(len(facet_medians)), facet_medians.values, color=colors, edgecolor="white")
axes[1].set_yticks(range(len(facet_medians)))
axes[1].set_yticklabels([textwrap.fill(f, 25) for f in facet_medians.index], fontsize=8)
axes[1].set_xlabel("Median Variant Count")
axes[1].set_title("Median Variants by Facet", fontweight="bold")

plt.suptitle("Multilingual Richness of AAT Terms", fontsize=16, fontweight="bold", y=1.02)
plt.tight_layout()
fig.savefig(f"{FIGDIR}/06_variant_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 06_variant_distribution.png")

# ─── 7. Language Script Distribution Pie ───

cjk = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]')
arabic = re.compile(r'[\u0600-\u06ff]')
cyrillic = re.compile(r'[\u0400-\u04ff]')

lang_counts = Counter()
for variants in df["variant_terms"]:
    for v in variants:
        v_str = str(v)
        if cjk.search(v_str):
            lang_counts["CJK"] += 1
        elif arabic.search(v_str):
            lang_counts["Arabic"] += 1
        elif cyrillic.search(v_str):
            lang_counts["Cyrillic"] += 1
        else:
            lang_counts["Latin"] += 1

fig, ax = plt.subplots(figsize=(8, 8))
labels = list(lang_counts.keys())
sizes = list(lang_counts.values())
explode = [0.05] * len(labels)
colors_pie = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]
ax.pie(sizes, labels=labels, autopct="%1.1f%%", explode=explode, colors=colors_pie,
       startangle=140, textprops={"fontsize": 12})
ax.set_title("Script Distribution Across All 334K Variant Terms", fontsize=14, fontweight="bold")
fig.savefig(f"{FIGDIR}/07_language_scripts.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 07_language_scripts.png")

# ─── 8. Scope Note Length by Facet ───

df_with_scope = df[df["scope_note"].notna()].copy()
df_with_scope["scope_len"] = df_with_scope["scope_note"].str.len()

fig, ax = plt.subplots(figsize=(14, 7))
scope_data = []
labels = []
for facet in FACET_ORDER:
    data = df_with_scope[df_with_scope["hierarchy"] == facet]["scope_len"]
    if len(data) > 0:
        scope_data.append(data)
        labels.append(facet)

bp = ax.boxplot(scope_data, vert=False, patch_artist=True, widths=0.6)
for i, patch in enumerate(bp["boxes"]):
    patch.set_facecolor(FACET_COLORS[labels[i]])
    patch.set_alpha(0.7)

ax.set_yticklabels([textwrap.fill(l, 25) for l in labels], fontsize=9)
ax.set_xlabel("Scope Note Length (characters)")
ax.set_title("Scope Note Length Distribution by Facet", fontsize=14, fontweight="bold")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/08_scope_length_boxplot.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 08_scope_length_boxplot.png")

# ─── 9. Top Parent Terms — Treemap-style bar ───

parent_counts = df["parent_term"].value_counts().head(25)
fig, ax = plt.subplots(figsize=(14, 8))
colors_bar = sns.color_palette("viridis", len(parent_counts))
bars = ax.barh(range(len(parent_counts)), parent_counts.values, color=colors_bar, edgecolor="white")
ax.set_yticks(range(len(parent_counts)))
ax.set_yticklabels([textwrap.fill(t, 50) for t in parent_counts.index], fontsize=8)
ax.set_xlabel("Number of Direct Children")
ax.set_title("Top 25 Parent Terms by Number of Children", fontsize=14, fontweight="bold")
ax.invert_yaxis()
for bar, val in zip(bars, parent_counts.values):
    ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2, str(val),
            va="center", fontsize=8, fontweight="bold")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/09_top_parents.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 09_top_parents.png")

# ─── 10. Facet-specific Word Clouds (2x3 grid) ───

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

for idx, facet in enumerate(FACET_ORDER[:6]):
    facet_terms = df[df["hierarchy"] == facet]["preferred_term"].str.lower()
    freq = Counter()
    for t in facet_terms:
        freq.update(w for w in t.split() if w not in stopwords and len(w) > 2)

    wc = WordCloud(width=600, height=400, background_color="white",
                   colormap="tab20", max_words=80, min_font_size=6)
    wc.generate_from_frequencies(freq)
    axes[idx].imshow(wc, interpolation="bilinear")
    axes[idx].axis("off")
    axes[idx].set_title(facet, fontsize=12, fontweight="bold")

plt.suptitle("Word Clouds by Facet — Top 6", fontsize=18, fontweight="bold", y=1.01)
plt.tight_layout()
fig.savefig(f"{FIGDIR}/10_facet_wordclouds.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 10_facet_wordclouds.png")

print("\n✅ All static visualizations saved to src/analysis/figures/")
