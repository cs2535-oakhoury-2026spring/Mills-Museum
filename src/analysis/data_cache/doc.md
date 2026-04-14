# Data Cache Directory

This directory stores local Parquet snapshots of HuggingFace datasets so that the analysis scripts can run without a network connection after the first download.

## Default File

- **`aat_museum_subset.parquet`** (~8.3 MB) — A cached copy of the [KeeganC/aat-museum-subset](https://huggingface.co/datasets/KeeganC/aat-museum-subset) dataset. Contains 44,225 rows (one per AAT term) with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `preferred_term` | string | The canonical English name (e.g., "oil painting") |
| `subject_id` | int | Unique numeric AAT identifier |
| `hierarchy` | string | Which of the 12 facets the term belongs to (e.g., "Furnishings and Equipment") |
| `parent_id` | int | The subject_id of the parent term in the taxonomy tree |
| `parent_term` | string | Human-readable name of the parent |
| `scope_note` | string (nullable) | Free-text description of the term's meaning and historical context |
| `variant_terms` | list[string] | Multilingual translations and alternate names |

## How it gets created

When `load_dataset.py` runs for the first time, it:
1. Downloads the dataset from HuggingFace using the `datasets` library
2. Converts it to a pandas DataFrame
3. Saves it as `aat_museum_subset.parquet` in this directory

On all subsequent runs, the Parquet file is loaded directly (no download).

## Using a different dataset

```bash
python src/analysis/load_dataset.py \
    --dataset your-hf-dataset-id \
    --output src/analysis/data_cache/your_snapshot.parquet
```

Then point the dashboard at it:

```bash
AAT_ANALYSIS_DATA_PATH=src/analysis/data_cache/your_snapshot.parquet \
    python src/analysis/09_dashboard.py
```

## Note

This directory is typically **not committed to git** — the Parquet file is large and can be regenerated. If it's missing, just run `load_dataset.py` to recreate it.
