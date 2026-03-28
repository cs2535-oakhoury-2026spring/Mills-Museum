"""Network graph of parent-child relationships + extra deep dives."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import seaborn as sns
from collections import Counter
import re
import textwrap

sns.set_theme(style="whitegrid")
FIGDIR = "src/analysis/figures"

df = pd.read_parquet("src/analysis/data_cache/aat_museum_subset.parquet")
subject_ids = set(df["subject_id"])

# ─── 1. Network Graph — Top sub-trees per facet ───

G = nx.DiGraph()
term_map = dict(zip(df["subject_id"], df["preferred_term"]))
facet_map = dict(zip(df["subject_id"], df["hierarchy"]))

for facet in ["Furnishings and Equipment", "Materials", "Living Organisms", "Styles and Periods"]:
    facet_df = df[df["hierarchy"] == facet]
    top_parents = facet_df["parent_term"].value_counts().head(3).index
    for parent_name in top_parents:
        subset = facet_df[facet_df["parent_term"] == parent_name].head(8)
        parent_ids = subset["parent_id"].unique()
        for pid in parent_ids:
            if pid in term_map:
                G.add_node(term_map[pid], facet=facet, is_parent=True)
        for _, row in subset.iterrows():
            child = row["preferred_term"]
            G.add_node(child, facet=facet, is_parent=False)
            if row["parent_id"] in term_map:
                G.add_edge(term_map[row["parent_id"]], child)

facet_colors = {
    "Furnishings and Equipment": "#e74c3c",
    "Materials": "#3498db",
    "Living Organisms": "#2ecc71",
    "Styles and Periods": "#f39c12",
}

node_colors = []
node_sizes = []
for node in G.nodes():
    data = G.nodes[node]
    facet = data.get("facet", "Furnishings and Equipment")
    node_colors.append(facet_colors.get(facet, "#95a5a6"))
    node_sizes.append(300 if data.get("is_parent") else 80)

fig, ax = plt.subplots(figsize=(20, 16))
pos = nx.spring_layout(G, k=2.5, iterations=80, seed=42)
nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, arrows=True, arrowsize=8, edge_color="#bdc3c7")
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes, alpha=0.8)

parent_nodes = [n for n in G.nodes() if G.nodes[n].get("is_parent")]
labels = {n: textwrap.fill(n, 12) for n in parent_nodes}
nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7, font_weight="bold")

patches = [mpatches.Patch(color=c, label=f) for f, c in facet_colors.items()]
ax.legend(handles=patches, loc="upper left", fontsize=10)
ax.set_title("AAT Taxonomy Network — Top Sub-trees from 4 Facets", fontsize=16, fontweight="bold")
ax.axis("off")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/20_taxonomy_network.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 20_taxonomy_network.png")

# ─── 2. Year Distribution Histogram ───

year_pattern = re.compile(r'\b(1[0-9]{3}|20[0-2][0-9])\b')
all_years = []
for note in df["scope_note"].dropna():
    all_years.extend(int(m.group(1)) for m in year_pattern.finditer(note))

fig, ax = plt.subplots(figsize=(14, 5))
ax.hist(all_years, bins=100, color="#3498db", edgecolor="white", alpha=0.8)
ax.set_xlabel("Year")
ax.set_ylabel("Mentions in Scope Notes")
ax.set_title("Temporal Distribution of Year References in AAT Scope Notes", fontsize=14, fontweight="bold")
ax.axvline(1500, color="red", linestyle="--", alpha=0.5, label="1500 CE")
ax.axvline(1800, color="orange", linestyle="--", alpha=0.5, label="1800 CE")
ax.legend()
plt.tight_layout()
fig.savefig(f"{FIGDIR}/21_year_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 21_year_distribution.png")

# ─── 3. Scope Note Complexity Score ───

df_scope = df[df["scope_note"].notna()].copy()
df_scope["note_len"] = df_scope["scope_note"].str.len()
df_scope["note_words"] = df_scope["scope_note"].str.split().str.len()
df_scope["avg_word_len"] = df_scope["note_len"] / df_scope["note_words"]
df_scope["sentence_count"] = df_scope["scope_note"].str.count(r'[.!?]+')
df_scope["variant_count"] = df_scope["variant_terms"].apply(len)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].hist(df_scope["note_words"], bins=80, color="#2ecc71", edgecolor="white", alpha=0.8)
axes[0, 0].set_title("Word Count in Scope Notes", fontweight="bold")
axes[0, 0].set_xlabel("Words")

axes[0, 1].hist(df_scope["sentence_count"], bins=30, color="#e74c3c", edgecolor="white", alpha=0.8)
axes[0, 1].set_title("Sentence Count in Scope Notes", fontweight="bold")
axes[0, 1].set_xlabel("Sentences")

axes[1, 0].hist(df_scope["avg_word_len"], bins=50, color="#f39c12", edgecolor="white", alpha=0.8)
axes[1, 0].set_title("Average Word Length in Scope Notes", fontweight="bold")
axes[1, 0].set_xlabel("Avg chars per word")

facet_complexity = df_scope.groupby("hierarchy").agg(
    avg_words=("note_words", "mean"),
    avg_sentences=("sentence_count", "mean"),
    avg_word_len=("avg_word_len", "mean"),
).sort_values("avg_words", ascending=True)

y_pos = range(len(facet_complexity))
axes[1, 1].barh(y_pos, facet_complexity["avg_words"], color="#3498db", alpha=0.8)
axes[1, 1].set_yticks(y_pos)
axes[1, 1].set_yticklabels([textwrap.fill(f, 20) for f in facet_complexity.index], fontsize=8)
axes[1, 1].set_title("Avg Scope Note Length by Facet", fontweight="bold")
axes[1, 1].set_xlabel("Avg Words")

plt.suptitle("Scope Note Complexity Analysis", fontsize=16, fontweight="bold", y=1.01)
plt.tight_layout()
fig.savefig(f"{FIGDIR}/22_scope_complexity.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 22_scope_complexity.png")

# ─── 4. Multilingual Coverage by Facet ───

def count_scripts(variants):
    cjk = sum(1 for v in variants if re.search(r'[\u4e00-\u9fff]', str(v)))
    arabic = sum(1 for v in variants if re.search(r'[\u0600-\u06ff]', str(v)))
    latin = len(variants) - cjk - arabic
    return pd.Series({"latin": latin, "cjk": cjk, "arabic": arabic})

script_counts = df["variant_terms"].apply(count_scripts)
df_lang = pd.concat([df[["hierarchy"]], script_counts], axis=1)

facet_lang = df_lang.groupby("hierarchy")[["latin", "cjk", "arabic"]].mean()
facet_lang = facet_lang.sort_values("cjk", ascending=True)

fig, ax = plt.subplots(figsize=(12, 7))
facet_lang.plot(kind="barh", stacked=True, ax=ax,
                color=["#3498db", "#e74c3c", "#2ecc71"], edgecolor="white")
ax.set_title("Average Multilingual Coverage per Term by Facet", fontsize=14, fontweight="bold")
ax.set_xlabel("Avg Variant Terms per Entry")
ax.set_yticklabels([textwrap.fill(f, 25) for f in facet_lang.index], fontsize=9)
ax.legend(["Latin script", "CJK", "Arabic"], title="Script")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/23_multilingual_coverage.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 23_multilingual_coverage.png")

# ─── 5. Fun stat: Most "described" terms ───

print("\n" + "=" * 60)
print("LONGEST SCOPE NOTES (most detailed descriptions)")
print("=" * 60)
df_scope_sorted = df_scope.nlargest(10, "note_len")
for _, row in df_scope_sorted.iterrows():
    print(f"  '{row['preferred_term']}' [{row['hierarchy']}]")
    print(f"    {row['note_len']:,} chars, {row['note_words']} words")
    print(f"    Preview: {row['scope_note'][:150]}...")
    print()

# ─── 6. Terms with most translations ───

print("=" * 60)
print("MOST MULTILINGUAL TERMS (most variant names)")
print("=" * 60)
df["variant_count"] = df["variant_terms"].apply(len)
top_multilingual = df.nlargest(15, "variant_count")
for _, row in top_multilingual.iterrows():
    scripts = count_scripts(row["variant_terms"])
    print(f"  '{row['preferred_term']}' → {row['variant_count']} variants")
    print(f"    Latin: {scripts['latin']}, CJK: {scripts['cjk']}, Arabic: {scripts['arabic']}")
    print(f"    Facet: {row['hierarchy']}")
    print()

print("✅ Network and extra analyses complete")
