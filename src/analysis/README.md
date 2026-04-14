# Analysis Directory

This directory is reduced to the files used for the standalone analysis dashboard.

## Keep

- `09_dashboard.py`: builds `figures/dashboard.html`
- `load_dataset.py`: downloads or caches a parquet snapshot
- `data_cache/`: local parquet snapshots
- `figures/dashboard.html`: generated dashboard output

## Switch datasets

Download a different collection:

```bash
python src/analysis/load_dataset.py --dataset your-hf-dataset --output src/analysis/data_cache/your_snapshot.parquet
```

Build the dashboard from that snapshot:

```bash
AAT_ANALYSIS_DATA_PATH=src/analysis/data_cache/your_snapshot.parquet python src/analysis/09_dashboard.py
```
