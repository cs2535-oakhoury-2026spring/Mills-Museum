# Data Visualization

This repo has two visualization paths:

- `src/frontend/data_story_exhibit.py` for the Gradio exhibit
- `src/analysis/09_dashboard.py` for the standalone analysis dashboard

Both expect an AAT-style parquet snapshot with this schema:

```text
subject_id, preferred_term, variant_terms, scope_note,
hierarchy, facet, record_type, parent_id, parent_term,
sort_order, term_id, root_id
```

## Dataset setup

Fetch the default dataset snapshot:

```bash
python src/analysis/load_dataset.py
```

Fetch a different keyword collection:

```bash
python src/analysis/load_dataset.py --dataset your-hf-dataset --output src/analysis/data_cache/your_snapshot.parquet
```

## Standalone dashboard

Build the dashboard with the default snapshot:

```bash
python src/analysis/09_dashboard.py
```

Build it from a different snapshot:

```bash
AAT_ANALYSIS_DATA_PATH=src/analysis/data_cache/your_snapshot.parquet python src/analysis/09_dashboard.py
```

## Gradio exhibit

From the repo root:

```bash
pip install -r requirements.txt
python -m src.frontend.data_story_exhibit
```
