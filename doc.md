# Repository Guide

This repository is the working codebase for a Mills College Art Museum project that tries to make AAT keyword labeling easier for museum staff. In plain terms, the project has three major parts:

1. A keyword-generation and review interface for artwork images.
2. A data exhibit and analysis layer built on a museum-focused subset of the Getty Art & Architecture Thesaurus.
3. Data-preparation scripts used to build, clean, deduplicate, and publish supporting datasets.

If someone is new to the repository, the most important folders are:

- `src/frontend/`: all user-facing interfaces.
- `src/analysis/`: dataset loading and AAT analysis/dashboard work.
- `scripts/`: data utilities and the semantic deduplication pipeline.

## How the project is organized

### User-facing applications

There are two frontend styles in this repository:

- A Python/Gradio workflow in `src/frontend/gradio.py` for uploading artwork images, generating keywords, reviewing them, and exporting the results.
- A React/Vite browser app in `src/frontend/web/` that performs a similar keyword-review flow but talks to a backend API over HTTP.

There is also a separate Gradio-based data exhibit in `src/frontend/data_viz/data_story_exhibit.py`. That app is not the keyword-review tool. It is an interactive presentation of the AAT dataset and project findings.

### Analysis work

The analysis side lives in `src/analysis/`. It includes:

- `load_dataset.py`: downloads or loads a cached parquet snapshot of the curated AAT dataset.
- `09_dashboard.py`: builds a standalone HTML dashboard from that dataset.
- `data_cache/`: cached parquet data used by both analysis and exhibit code.
- `figures/`: dashboard output and older exploratory figures.

### Data and pipeline scripts

Most of the heavy data-preparation work lives outside `src/` under `scripts/`. The most important operational area is:

- `scripts/pipeline/filtration/semantic_dedup_core.py`

That script embeds term labels, clusters similar labels within each language, chooses canonical labels, and writes cleaned outputs plus audit files. Other scripts in `scripts/hf_upload_scripts/` and `scripts/pipeline/filtration/` publish datasets to Hugging Face or prepare museum-specific tables.

## Files worth reading first

- `README.md`: project overview and overall goals.
- `src/frontend/doc.md`: detailed guide to the user-facing application code.
- `src/analysis/doc.md`: detailed guide to the analysis and dashboard code.
- `pyproject.toml`: Python package configuration.
- `package.json`: root npm shortcuts for the React app.
- `CHANGELOG.md`: project change log.

## Common commands

- `uv run mills-data-exhibit`: run the Gradio data exhibit.
- `npm run dev`: start the React frontend from the repository root.
- `npm run build`: build the React frontend from the repository root.
- `python -m unittest tests/frontend_test/test_keyword_feedback.py`: run the Python review-logic tests.

## Important notes

- Some folders contain generated artifacts rather than hand-written source, especially `src/analysis/figures/` and `src/analysis/data_cache/`.
- Several scripts under `scripts/` are operational utilities with hard-coded paths or publishing targets. They are useful, but they are not polished general-purpose tools.
- The frontend and analysis sections are documented in more detail in the two remaining directory-level `doc.md` files under `src/frontend/` and `src/analysis/`.
