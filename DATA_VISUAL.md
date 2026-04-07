# Data Visualization — AAT Museum Subset

This is the analysis and exhibit layer of the Mills Museum project. It takes the AAT dataset, digs through it, and presents findings as an interactive local website.



## What it does

The exhibit app loads a parquet snapshot of the AAT museum subset and builds interactive charts on the fly — facet distributions, century heatmaps, taxonomy depth, geographic coverage, keyword trends, and more. Everything renders in a single Gradio page at `localhost:7860`.

## The dataset can change

Right now this uses `KeeganC/aat-museum-subset` (44K rows, 12 columns). But the code is built around the schema, not the specific rows. If you swap in a different AAT subset with the same column structure, the charts and analysis will regenerate to match. The schema it expects:

```
subject_id, preferred_term, variant_terms, scope_note,
hierarchy, facet, record_type, parent_id, parent_term,
sort_order, term_id, root_id
```



## Running locally

From the repo root:

```bash
pip install -r requirements.txt
python -m src.frontend.data_story_exhibit
```

Then open http://127.0.0.1:7860 in your browser.

If the parquet file is missing, download it first:

```bash
python src/analysis/load_dataset.py
```

That pulls from HuggingFace and caches to `src/analysis/data_cache/`.

## What needs to exist

- `src/analysis/data_cache/aat_museum_subset.parquet`
- `src/frontend/mills.jpg`

The analysis scripts in `src/analysis/` (01 through 09) generated the static figures in `src/analysis/figures/`. You don't need to rerun them — the exhibit app builds its own charts live. But the scripts are there if you want to see how the numbers were found.
