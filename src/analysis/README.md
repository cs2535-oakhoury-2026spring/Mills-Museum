# Analysis on Art & Architecture Thesaurus (Getty Research Institute)

This directory contains the code and data for an interactive visual analysis of 44,225 terms from the Getty AAT (Art & Architecture Thesaurus).

## What is the AAT?

The Art & Architecture Thesaurus is a structured vocabulary maintained by the Getty Research Institute. It organizes terms for art, architecture, and material culture into 12 broad categories called "facets" (e.g., Furnishings & Equipment, Styles & Periods, Materials). Museums, libraries, and cultural institutions use these terms to catalog their collections.

## Directory Structure

```
src/analysis/
├── 09_dashboard.py          # Builds the interactive HTML dashboard
├── load_dataset.py           # Downloads and caches the AAT dataset
├── data_cache/               # Cached Parquet snapshots (not in git)
│   └── aat_museum_subset.parquet
├── figures/                  # Generated charts and the final dashboard
│   ├── dashboard.html        # The main output — open in a browser
│   └── *.png                 # Static chart images from earlier analysis
└── README.md                 # This file
```

## Quick Start

### 1. Install dependencies

```bash
pip install pandas plotly pyarrow datasets
```

### 2. Run the dashboard builder

```bash
python src/analysis/09_dashboard.py
```

This will:
- Load the dataset from `data_cache/` (or download it from HuggingFace on first run)
- Build 7 interactive Plotly charts
- Write a single self-contained HTML file to `figures/dashboard.html`

### 3. Open the dashboard

```bash
open src/analysis/figures/dashboard.html
```

## Using a Different Dataset

To analyze a different collection from HuggingFace:

```bash
# Download and cache a new dataset
python src/analysis/load_dataset.py --dataset your-hf-dataset --output src/analysis/data_cache/custom.parquet

# Build the dashboard from that snapshot
AAT_ANALYSIS_DATA_PATH=src/analysis/data_cache/custom.parquet python src/analysis/09_dashboard.py
```

## What the Dashboard Shows

| Chart | Section | What it reveals |
|-------|---------|-----------------|
| Facet Donut | The Collection | Which of the 12 facets has the most terms |
| Century Heatmap | Through Time | When each facet's terms were most active historically |
| Hierarchy Sunburst | Hierarchy | Parent-child structure — click to drill in |
| Keyword Trends | Trending | When popular words peaked across centuries |
| Depth Violin | Depth | How deep each facet's taxonomy tree goes |
| Geographic Area | Geography | Which world regions appear over time |
| Script Pie | Languages | Latin vs CJK vs other writing systems |

See `figures/doc.md` and `data_cache/doc.md` for details on each subdirectory.
