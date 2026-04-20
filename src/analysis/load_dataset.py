"""
Dataset Loader for AAT Analysis
================================

Downloads the Art & Architecture Thesaurus dataset from HuggingFace and
saves a local copy as a Parquet file.  On subsequent runs, the cached
Parquet file is loaded directly (no network request).

The default dataset is "KeeganC/aat-museum-subset", a curated 44,225-term
subset of the Getty AAT hosted on HuggingFace.

Usage
-----
As a library (imported by 09_dashboard.py):

    from load_dataset import load_aat_dataset
    df = load_aat_dataset()

From the command line (to download or switch datasets):

    python src/analysis/load_dataset.py
    python src/analysis/load_dataset.py --dataset your-hf-dataset --output data_cache/custom.parquet

What the Parquet file contains
------------------------------
Each row is one AAT term with columns including:

    preferred_term  — the canonical English name (e.g., "oil painting")
    subject_id      — unique numeric AAT identifier
    hierarchy       — which of the 12 facets the term belongs to
    parent_id       — the subject_id of the term's parent in the tree
    parent_term     — human-readable name of the parent
    scope_note      — free-text description (may be null)
    variant_terms   — list of multilingual translations
"""

import argparse
from pathlib import Path

from datasets import load_dataset

# Where cached Parquet files are stored (next to this script).
CACHE_DIR = Path(__file__).resolve().parent / "data_cache"

# Default HuggingFace dataset and split to download.
DEFAULT_DATASET = "KeeganC/aat-museum-subset"
DEFAULT_SPLIT = "train"
DEFAULT_OUTPUT = CACHE_DIR / "aat_museum_subset.parquet"


def load_aat_dataset(
    dataset_name: str = DEFAULT_DATASET,
    split: str = DEFAULT_SPLIT,
    output_path: Path = DEFAULT_OUTPUT,
):
    """
    Load the AAT dataset, returning a pandas DataFrame.

    If a cached Parquet file exists at ``output_path``, it is read directly.
    Otherwise the dataset is downloaded from HuggingFace, converted to a
    DataFrame, and saved as Parquet for next time.
    """
    if output_path.exists():
        import pandas as pd
        return pd.read_parquet(output_path)

    print("Downloading dataset from HuggingFace...")
    ds = load_dataset(dataset_name, split=split)
    df = ds.to_pandas()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)
    print(f"Saved {len(df)} rows to {output_path}")
    return df


def parse_args() -> argparse.Namespace:
    """Define the small command-line interface for downloading a dataset snapshot."""
    parser = argparse.ArgumentParser(
        description="Download and cache an AAT dataset snapshot as Parquet.",
    )
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="HuggingFace dataset ID")
    parser.add_argument("--split", default=DEFAULT_SPLIT, help="Dataset split to use")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output Parquet path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    df = load_aat_dataset(dataset_name=args.dataset, split=args.split, output_path=args.output)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nFirst 3 rows:\n{df.head(3)}")
    print(f"\nNull counts:\n{df.isnull().sum()}")
