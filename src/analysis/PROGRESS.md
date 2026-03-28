# AAT Museum Subset — Deep Analysis Progress

**Dataset**: `KeeganC/aat-museum-subset` (HuggingFace)
**Size**: 44,225 rows x 12 columns
**Date**: 2026-03-26

---

## Dataset Overview

The dataset is a subset of the **Art & Architecture Thesaurus (AAT)** — Getty's controlled vocabulary of 50,000+ terms used to describe art, architecture, and cultural heritage. This subset contains 44,225 concept records, each with preferred terms, multilingual variants, scope notes, and hierarchical positioning.

### Columns
| Column | Type | Unique | Nulls | Notes |
|--------|------|--------|-------|-------|
| subject_id | int64 | 44,225 | 0 | Unique AAT identifier |
| preferred_term | string | 42,974 | 0 | Canonical English name |
| variant_terms | array | — | 0 | Multilingual synonyms (avg 7.6 per entry) |
| scope_note | string | 36,632 | 7,168 | Definition/description |
| hierarchy | string | 12 | 0 | Top-level facet name |
| facet | string | 12 | 0 | Facet code (e.g. V.T, F.FL) |
| record_type | string | 1 | 0 | Always "C" (concept) |
| parent_id | int64 | 9,033 | 0 | Parent node ID |
| parent_term | string | 8,905 | 0 | Parent node name |
| sort_order | int64 | 427 | 0 | Sort position |
| term_id | int64 | 44,225 | 0 | Unique term ID |
| root_id | int64 | 12 | 0 | Root facet ID |

---

## Key Findings

### 1. Facet Distribution — Dominated by Furnishings

The AAT subset is heavily skewed toward physical objects:

| Facet | Count | % |
|-------|-------|---|
| **Furnishings and Equipment** | 16,157 | **36.5%** |
| Styles and Periods | 5,682 | 12.8% |
| Components | 5,611 | 12.7% |
| Materials | 4,680 | 10.6% |
| Built Environment | 3,508 | 7.9% |
| Processes and Techniques | 2,229 | 5.0% |
| Living Organisms | 2,224 | 5.0% |
| People | 2,150 | 4.9% |
| Color | 591 | 1.3% |
| Design Elements | 568 | 1.3% |
| Events | 554 | 1.3% |
| Physical and Mental Activities | 271 | 0.6% |

**Insight**: Over a third of all AAT terms relate to furniture, tools, and equipment — reflecting the thesaurus's practical museum cataloging purpose.

### 2. Multilingual Richness — 334K Variant Terms

Each entry averages **7.6 variant names** (total: 334,694 variants across all entries).

- **88.5% Latin script** (English, French, Spanish, Dutch, German, etc.)
- **11.3% CJK** (Chinese, Japanese, Korean — significant presence)
- **0.2% Arabic script**
- **0.0% Cyrillic** (only 5 terms)

The most translated term is **"scrolled pediments"** with 53 variants. Terms like "lead white" show 12 CJK variants — the Chinese art conservation vocabulary is deeply represented.

**Implication for Mills Museum**: When matching AAT terms, the multilingual variants can help match non-English catalog entries or descriptions.

### 3. Hierarchy — 12 Levels Deep, 82.8% Leaves

The taxonomy reconstructed from parent-child links goes 11 levels deep:
- **82.8% are leaf nodes** (no children)
- **34.6% sit at depth 0** (root-level, parent not in this subset)
- Only 785 terms (1.8%) are at depth 6+

**Deepest path** (11 levels): `Eukaryota → Animalia → Arthropoda → Hexapoda → Insecta → Lepidoptera → Papilionoidea → Nymphalidae → Morphinae → Morphini → Morpho → Morpho menelaus`

**Living Organisms** is by far the deepest facet (Linnaean taxonomy), while **Color** and **Design Elements** are shallow (max depth 4-5).

The **largest sub-tree** is `Eukaryota` with 2,094 descendants.

### 4. Century References — 19th Century Peak

Mining century references from scope notes reveals a clear temporal pattern:

| Century | Mentions | Trend |
|---------|----------|-------|
| 3rd-10th | 10-45 each | Low baseline |
| 11th-14th | 30-73 | Medieval growth |
| 15th | 102 | Renaissance uptick |
| 16th | 168 | Significant rise |
| 17th | 255 | Continued growth |
| 18th | 329 | Strong presence |
| **19th** | **562** | **Peak — Industrial Revolution** |
| 20th | 220 | Modern decline |

**Insight**: The 19th century dominates — the Industrial Revolution created a massive proliferation of new tools, materials, processes, and styles that the AAT needed to catalog. The **Styles and Periods** facet has the strongest temporal presence (123 mentions of 19th c alone).

### 5. Geographic Coverage — Asia and Europe Neck-and-Neck

| Region | Scope Note Mentions |
|--------|-------------------|
| Asian | 2,278 |
| European | 2,264 |
| African | 1,348 |
| Americas | 1,112 |
| Middle Eastern | 269 |

**Surprise**: Asian references slightly edge out European ones. The AAT is more globally representative than one might assume for a Getty product.

The **Styles and Periods** facet has the strongest geographic concentration, while **Furnishings and Equipment** is the most geographically diverse.

### 6. Material Co-occurrence — Wood + Metal Reign Supreme

The most frequently co-mentioned materials in scope notes:

| Pair | Co-occurrences |
|------|---------------|
| Wood + Metal | 320 |
| Stone + Wood | 140 |
| Glass + Metal | 138 |
| Paper + Wood | 114 |
| Metal + Silver | 107 |
| Gold + Silver | 94 |

**Insight**: Wood and metal are the foundational materials of the AAT's world — they co-occur far more than any other pair. The textile cluster (silk + cotton + wool) forms its own sub-community.

### 7. Scope Note Coverage Gaps

83.8% of terms have scope notes, but coverage varies wildly:

| Facet | Missing % |
|-------|-----------|
| **Furnishings and Equipment** | **32.0%** |
| **Styles and Periods** | **26.5%** |
| Components | 5.2% |
| Events | 3.8% |
| Living Organisms | 2.5% |
| All others | < 2% |

**Actionable**: 5,172 Furnishings terms lack descriptions — this is the biggest documentation gap in the subset. For the Mills Museum pipeline, these undescribed terms may be harder to match accurately.

### 8. Duplicate Terms Across Facets

1,127 preferred terms appear more than once — same word, different meaning in different facets:
- "wings" (6x) — appears in Components and Furnishings
- "slides" (5x) — Furnishings, Components, Built Environment
- "panels" (5x) — Design Elements, Events, Components
- "hammers" (5x) — Furnishings and Components

**Implication**: Term matching must be facet-aware. A naive keyword match for "wings" could return architectural components or bird-related terms.

### 9. TF-IDF Distinctive Terms

Each facet has highly characteristic vocabulary:
- **Living Organisms**: Quercus, Pinus, Populus (Latin genus names)
- **People**: Artists, painters, makers, designers
- **Physical Activities**: Games, gardening, sports, bowling
- **Design Elements**: Crosses, grain, symbols, scrolls, güls
- **Events**: Holidays, exhibitions, festivals, ceremonies
- **Color**: Blue, yellow, dark, purplish, grayish

### 10. K-Means Clustering on Scope Notes (k=8)

Unsupervised clustering of scope note text reveals natural topic groups:
- **Cluster 0** (4,722 terms): General objects — "designed, small, worn, material"
- **Cluster 4** (527 terms): Historical/cultural — "style, culture, period, BCE, century"
- **Cluster 5** (54 terms): Color specification — "universal color language standard"
- **Cluster 6** (406 terms): Biological — "species, genus, native, family, wood, tree"
- **Cluster 7** (130 terms): Ethnographic — "African, ethnic, group, inhabiting"

### 11. Facet Vocabulary Similarity

Jaccard similarity on preferred term word sets shows:
- **Components ↔ Furnishings**: 0.11 (highest cross-facet similarity)
- **Built Environment ↔ Components**: 0.07
- **Materials ↔ Furnishings**: 0.06
- **Color ↔ everything**: ~0.01 (most isolated vocabulary)

### 12. Most Detailed Scope Notes

The richest descriptions are for **Chinese architectural terms**:
1. yìxínggǒng (Components) — 2,804 chars, 441 words
2. Tang (Styles and Periods) — 2,536 chars, 400 words
3. yán'é (Components) — 1,989 chars, 329 words
4. Yüan (Styles and Periods) — 1,974 chars, 300 words

**Insight**: Chinese architectural terminology receives extraordinarily detailed scope notes compared to Western terms — suggesting significant scholarly investment in cross-cultural documentation.

---

## Relevance to Mills Museum Project

1. **Keyword matching complexity**: With 42,974 unique preferred terms + 334K variants, the matching pipeline must handle massive vocabulary. The multilingual variants (especially CJK) could be leveraged for broader matching.

2. **Facet disambiguation**: 1,127 duplicate terms mean the pipeline needs facet-aware matching — "wings" in architecture vs. biology vs. furniture.

3. **Scope note gaps**: 32% of Furnishings terms lack descriptions — these may need special handling in the embedding/matching pipeline since there's less text to embed.

4. **Hierarchy depth variation**: Living Organisms go 11 levels deep while Colors are 4 levels — the Qwen embedder may need to weight hierarchical context differently by facet.

5. **Temporal bias**: The dataset is strongest for 16th-19th century material culture — matching may be less reliable for very ancient or very modern pieces.

---

## Visualizations Generated

### Static (PNG)
| # | File | Description |
|---|------|-------------|
| 1 | `01_facet_donut.png` | Facet distribution donut chart |
| 2 | `02_term_wordcloud.png` | Word cloud of all preferred terms |
| 3 | `03_century_heatmap.png` | Century references by facet heatmap |
| 4 | `04_geo_by_facet.png` | Geographic references by facet |
| 5 | `05_depth_violin.png` | Tree depth violin plots by facet |
| 6 | `06_variant_distribution.png` | Variant term count distribution |
| 7 | `07_language_scripts.png` | Script distribution pie chart |
| 8 | `08_scope_length_boxplot.png` | Scope note length by facet |
| 9 | `09_top_parents.png` | Top 25 parent terms by child count |
| 10 | `10_facet_wordclouds.png` | Per-facet word clouds (2x3 grid) |
| 17 | `17_pca_clusters.png` | PCA of scope note clusters |
| 18 | `18_material_cooccurrence.png` | Material co-occurrence heatmap |
| 19 | `19_facet_similarity.png` | Facet vocabulary Jaccard similarity |
| 20 | `20_taxonomy_network.png` | Network graph of sub-trees |
| 21 | `21_year_distribution.png` | Year reference histogram |
| 22 | `22_scope_complexity.png` | Scope note complexity analysis |
| 23 | `23_multilingual_coverage.png` | Multilingual coverage by facet |

### Interactive (HTML — open in browser)
| # | File | Description |
|---|------|-------------|
| 11 | `11_sunburst.html` | Drill-down sunburst of facets → parents |
| 12 | `12_keyword_century_heatmap.html` | Keyword trends across centuries |
| 13 | `13_treemap.html` | Full taxonomy treemap (color = variant richness) |
| 14 | `14_geo_centuries.html` | Geographic focus stacked area over centuries |
| 15 | `15_scatter_scope_variants.html` | Scope length vs variant count scatter |
| 16 | `16_facet_keywords.html` | Top keywords per facet (faceted bar chart) |

---

## Analysis Scripts

| Script | Purpose |
|--------|---------|
| `load_dataset.py` | Download and cache dataset as parquet |
| `01_deep_profile.py` | Column profiling, distributions, depth analysis |
| `02_term_analysis.py` | Multilingual analysis, temporal mining, geographic refs |
| `03_hierarchy_analysis.py` | Parent-child trees, branching factors, sub-tree sizes |
| `04_visualizations.py` | 10 static matplotlib/seaborn visualizations |
| `05_interactive_viz.py` | 6 interactive Plotly visualizations |
| `06_advanced_analysis.py` | TF-IDF, K-Means clustering, co-occurrence, similarity |
| `07_network_and_extras.py` | Network graph, year distribution, complexity analysis |

---

## Status: COMPLETE
All analysis scripts executed successfully. 23 visualizations generated. Key findings documented above.
