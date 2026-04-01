"""Advanced analysis — co-occurrence networks, TF-IDF, clustering."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import re
import textwrap

sns.set_theme(style="whitegrid")
FIGDIR = "src/analysis/figures"

df = pd.read_parquet("src/analysis/data_cache/aat_museum_subset.parquet")

# ─── 1. TF-IDF Top Terms per Facet ───

print("=" * 60)
print("TF-IDF — MOST DISTINCTIVE TERMS PER FACET")
print("=" * 60)

facet_docs = df.groupby("hierarchy")["preferred_term"].apply(lambda x: " ".join(x.str.lower())).reset_index()
facet_docs.columns = ["facet", "text"]

tfidf = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2))
tfidf_matrix = tfidf.fit_transform(facet_docs["text"])
feature_names = tfidf.get_feature_names_out()

for i, facet in enumerate(facet_docs["facet"]):
    scores = tfidf_matrix[i].toarray().flatten()
    top_idx = scores.argsort()[-15:][::-1]
    top_terms = [(feature_names[j], scores[j]) for j in top_idx]
    print(f"\n  [{facet}]")
    for term, score in top_terms:
        bar = "█" * int(score * 100)
        print(f"    {term:30s} {score:.4f} {bar}")

# ─── 2. Scope Note Topic Clusters ───

print("\n" + "=" * 60)
print("SCOPE NOTE CLUSTERING (K-Means on TF-IDF)")
print("=" * 60)

df_scope = df[df["scope_note"].notna()].copy()
sample = df_scope.sample(min(8000, len(df_scope)), random_state=42)

scope_tfidf = TfidfVectorizer(max_features=3000, stop_words="english", min_df=3, max_df=0.8)
scope_matrix = scope_tfidf.fit_transform(sample["scope_note"])

n_clusters = 8
km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
sample["cluster"] = km.fit_predict(scope_matrix)

scope_features = scope_tfidf.get_feature_names_out()
for c in range(n_clusters):
    center = km.cluster_centers_[c]
    top_idx = center.argsort()[-10:][::-1]
    top_words = [scope_features[j] for j in top_idx]
    count = (sample["cluster"] == c).sum()
    dominant_facet = sample[sample["cluster"] == c]["hierarchy"].mode().iloc[0]
    print(f"\n  Cluster {c} ({count:,} terms, dominant: {dominant_facet}):")
    print(f"    Keywords: {', '.join(top_words)}")

# ─── 3. PCA Visualization of Clusters ───

pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(scope_matrix.toarray())
sample["pca_x"] = coords[:, 0]
sample["pca_y"] = coords[:, 1]

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

scatter1 = axes[0].scatter(sample["pca_x"], sample["pca_y"], c=sample["cluster"],
                          cmap="Set2", alpha=0.4, s=8)
axes[0].set_title("Scope Note Clusters (K-Means, k=8)", fontweight="bold")
axes[0].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} var)")
axes[0].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} var)")
plt.colorbar(scatter1, ax=axes[0], label="Cluster")

facet_map = {f: i for i, f in enumerate(df["hierarchy"].value_counts().index)}
sample["facet_num"] = sample["hierarchy"].map(facet_map)
scatter2 = axes[1].scatter(sample["pca_x"], sample["pca_y"], c=sample["facet_num"],
                          cmap="Set3", alpha=0.4, s=8)
axes[1].set_title("Same PCA — Colored by Facet", fontweight="bold")
axes[1].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} var)")
axes[1].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} var)")

plt.tight_layout()
fig.savefig(f"{FIGDIR}/17_pca_clusters.png", dpi=150, bbox_inches="tight")
plt.close()
print("\n✓ 17_pca_clusters.png")

# ─── 4. Co-occurrence of Facet Keywords ───

print("\n" + "=" * 60)
print("KEYWORD CO-OCCURRENCE IN SCOPE NOTES")
print("=" * 60)

domain_words = ["wood", "metal", "stone", "glass", "paper", "ceramic", "textile", "leather",
                "ivory", "bronze", "iron", "steel", "copper", "gold", "silver", "clay",
                "silk", "cotton", "wool", "marble", "granite", "ivory", "bone", "shell"]

cooccurrence = Counter()
for note in df["scope_note"].dropna().str.lower():
    found = [w for w in domain_words if w in note]
    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            pair = tuple(sorted([found[i], found[j]]))
            cooccurrence[pair] += 1

print("Top 20 material co-occurrences in scope notes:")
for pair, count in cooccurrence.most_common(20):
    print(f"  {pair[0]:10s} + {pair[1]:10s} → {count:>4d} co-occurrences")

# ─── 5. Co-occurrence Heatmap ───

top_materials = ["wood", "metal", "stone", "glass", "paper", "ceramic", "textile",
                 "leather", "bronze", "iron", "steel", "copper", "gold", "silver",
                 "clay", "silk", "cotton", "wool", "marble"]

cooc_matrix = pd.DataFrame(0, index=top_materials, columns=top_materials)
for (a, b), count in cooccurrence.items():
    if a in top_materials and b in top_materials:
        cooc_matrix.loc[a, b] = count
        cooc_matrix.loc[b, a] = count

fig, ax = plt.subplots(figsize=(12, 10))
mask = cooc_matrix == 0
sns.heatmap(cooc_matrix, cmap="YlOrRd", annot=True, fmt="d", mask=mask,
            linewidths=0.5, ax=ax, square=True)
ax.set_title("Material Co-occurrence in Scope Notes", fontsize=14, fontweight="bold")
plt.tight_layout()
fig.savefig(f"{FIGDIR}/18_material_cooccurrence.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 18_material_cooccurrence.png")

# ─── 6. Scope Note Coverage Analysis ───

print("\n" + "=" * 60)
print("SCOPE NOTE COVERAGE — WHICH TERMS LACK DESCRIPTIONS?")
print("=" * 60)

no_scope = df[df["scope_note"].isna()]
has_scope = df[df["scope_note"].notna()]

print(f"\n  Without scope note: {len(no_scope):,} ({100*len(no_scope)/len(df):.1f}%)")
print(f"\n  Missing scope notes by facet:")
for facet in df["hierarchy"].value_counts().index:
    total = (df["hierarchy"] == facet).sum()
    missing = (no_scope["hierarchy"] == facet).sum()
    pct = 100 * missing / total if total > 0 else 0
    bar = "█" * int(pct)
    print(f"    {facet:40s} {missing:>5,}/{total:>5,} ({pct:>5.1f}%) {bar}")

# ─── 7. Duplicate / Near-duplicate term detection ───

print("\n" + "=" * 60)
print("NEAR-DUPLICATE PREFERRED TERMS")
print("=" * 60)

term_lower = df["preferred_term"].str.lower().str.strip()
dupes = term_lower.value_counts()
dupes = dupes[dupes > 1]
print(f"  Terms appearing more than once: {len(dupes):,}")
print(f"  Top 20 duplicated terms:")
for term, count in dupes.head(20).items():
    facets = df[term_lower == term]["hierarchy"].unique()
    print(f"    '{term}' × {count} — facets: {', '.join(facets)}")

# ─── 8. Facet Similarity Based on Shared Vocabulary ───

print("\n" + "=" * 60)
print("FACET SIMILARITY (Jaccard on preferred term vocabulary)")
print("=" * 60)

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
        if i <= j:
            inter = len(facet_vocabs[f1] & facet_vocabs[f2])
            union = len(facet_vocabs[f1] | facet_vocabs[f2])
            sim = inter / union if union > 0 else 0
            jaccard_matrix.loc[f1, f2] = sim
            jaccard_matrix.loc[f2, f1] = sim

fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(jaccard_matrix, cmap="Blues", annot=True, fmt=".2f",
            linewidths=0.5, ax=ax, square=True, vmin=0, vmax=0.5)
ax.set_title("Facet Vocabulary Similarity (Jaccard Index)", fontsize=14, fontweight="bold")
ax.set_xticklabels([textwrap.fill(l, 15) for l in facets_list], rotation=45, ha="right", fontsize=8)
ax.set_yticklabels([textwrap.fill(l, 15) for l in facets_list], fontsize=8)
plt.tight_layout()
fig.savefig(f"{FIGDIR}/19_facet_similarity.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ 19_facet_similarity.png")

print("\n✅ Advanced analysis complete")
