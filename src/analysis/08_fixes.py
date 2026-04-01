"""Fix: language pie (merge tiny slices to Other), material matrix (zero diagonal), facet similarity (zero diagonal)."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import textwrap
import numpy as np

sns.set_theme(style="whitegrid")
FIGDIR = "src/analysis/figures"
df = pd.read_parquet("src/analysis/data_cache/aat_museum_subset.parquet")

# ─── Fix 1: Language Scripts Pie — merge Arabic + Cyrillic into "Other" ───

cjk = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]')
arabic = re.compile(r'[\u0600-\u06ff]')
cyrillic = re.compile(r'[\u0400-\u04ff]')

lang_counts = Counter()
for variants in df["variant_terms"]:
    for v in variants:
        v_str = str(v)
        if cjk.search(v_str):
            lang_counts["CJK"] += 1
        elif arabic.search(v_str) or cyrillic.search(v_str):
            lang_counts["Other"] += 1
        else:
            lang_counts["Latin"] += 1

fig, ax = plt.subplots(figsize=(8, 8))
labels = ["Latin", "CJK", "Other"]
sizes = [lang_counts[l] for l in labels]
explode = [0, 0.08, 0.12]
colors_pie = ["#3498db", "#e74c3c", "#95a5a6"]
wedges, texts, autotexts = ax.pie(
    sizes, labels=labels, autopct="%1.1f%%", explode=explode, colors=colors_pie,
    startangle=140, textprops={"fontsize": 13}, pctdistance=0.78
)
for t in autotexts:
    t.set_fontweight("bold")
ax.set_title("Script Distribution Across All 334K Variant Terms", fontsize=15, fontweight="bold", pad=15)
fig.savefig(f"{FIGDIR}/07_language_scripts.png", dpi=150, bbox_inches="tight")
plt.close()
print("fixed 07_language_scripts.png")

# ─── Fix 2: Material Co-occurrence — zero diagonal, no self-pairs ───

stopwords_set = {"and", "of", "the", "for", "in", "with", "a", "an", "to", "or"}

top_materials = ["wood", "metal", "stone", "glass", "paper", "ceramic", "textile",
                 "leather", "bronze", "iron", "steel", "copper", "gold", "silver",
                 "clay", "silk", "cotton", "wool", "marble"]

cooccurrence = Counter()
for note in df["scope_note"].dropna().str.lower():
    found = list(set(w for w in top_materials if w in note))
    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            if found[i] != found[j]:
                pair = tuple(sorted([found[i], found[j]]))
                cooccurrence[pair] += 1

cooc_matrix = pd.DataFrame(0, index=top_materials, columns=top_materials)
for (a, b), count in cooccurrence.items():
    cooc_matrix.loc[a, b] = count
    cooc_matrix.loc[b, a] = count

np.fill_diagonal(cooc_matrix.values, 0)

fig, ax = plt.subplots(figsize=(13, 11))
mask = np.eye(len(top_materials), dtype=bool)
sns.heatmap(cooc_matrix, cmap="YlOrRd", annot=True, fmt="d", mask=mask,
            linewidths=0.5, ax=ax, square=True, vmin=0,
            cbar_kws={"label": "Co-occurrences", "shrink": 0.8})
ax.set_title("Material Co-occurrence in Scope Notes", fontsize=15, fontweight="bold", pad=15)
for label in ax.get_xticklabels():
    label.set_rotation(45)
    label.set_ha("right")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/18_material_cooccurrence.png", dpi=150, bbox_inches="tight")
plt.close()
print("fixed 18_material_cooccurrence.png")

# ─── Fix 3: Facet Similarity — zero diagonal, better color range ───

facet_vocabs = {}
for facet in df["hierarchy"].unique():
    words = set()
    for term in df[df["hierarchy"] == facet]["preferred_term"].str.lower():
        words.update(term.split())
    facet_vocabs[facet] = words

facets_list = sorted(facet_vocabs.keys())
jaccard_matrix = pd.DataFrame(0.0, index=facets_list, columns=facets_list)
for i, f1 in enumerate(facets_list):
    for j, f2 in enumerate(facets_list):
        if i < j:
            inter = len(facet_vocabs[f1] & facet_vocabs[f2])
            union = len(facet_vocabs[f1] | facet_vocabs[f2])
            sim = inter / union if union > 0 else 0
            jaccard_matrix.loc[f1, f2] = sim
            jaccard_matrix.loc[f2, f1] = sim

fig, ax = plt.subplots(figsize=(12, 10))
mask = np.eye(len(facets_list), dtype=bool)
sns.heatmap(jaccard_matrix, cmap="YlGnBu", annot=True, fmt=".3f", mask=mask,
            linewidths=0.5, ax=ax, square=True, vmin=0, vmax=0.12,
            cbar_kws={"label": "Jaccard Similarity", "shrink": 0.8})
ax.set_title("Facet Vocabulary Similarity (Jaccard Index)", fontsize=15, fontweight="bold", pad=15)
ax.set_xticklabels([textwrap.fill(l, 15) for l in facets_list], rotation=45, ha="right", fontsize=8)
ax.set_yticklabels([textwrap.fill(l, 15) for l in facets_list], fontsize=8)
plt.tight_layout()
fig.savefig(f"{FIGDIR}/19_facet_similarity.png", dpi=150, bbox_inches="tight")
plt.close()
print("fixed 19_facet_similarity.png")
