"""Download and cache an analysis dataset snapshot."""
import argparse
from pathlib import Path

from datasets import load_dataset

CACHE_DIR = Path(__file__).resolve().parent / "data_cache"
DEFAULT_DATASET = "KeeganC/aat-museum-subset"
DEFAULT_SPLIT = "train"
DEFAULT_OUTPUT = CACHE_DIR / "aat_museum_subset.parquet"

def load_aat_dataset(dataset_name: str = DEFAULT_DATASET, split: str = DEFAULT_SPLIT, output_path: Path = DEFAULT_OUTPUT):
    """Load a dataset from HuggingFace and cache it locally as parquet."""
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--split", default=DEFAULT_SPLIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    df = load_aat_dataset(dataset_name=args.dataset, split=args.split, output_path=args.output)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nFirst 3 rows:\n{df.head(3)}")
    print(f"\nNull counts:\n{df.isnull().sum()}")
