"""Download and cache the KeeganC/aat-museum-subset dataset."""
import os
from datasets import load_dataset

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data_cache")

def load_aat_dataset():
    """Load dataset from HuggingFace, cache locally as parquet."""
    parquet_path = os.path.join(CACHE_DIR, "aat_museum_subset.parquet")
    if os.path.exists(parquet_path):
        import pandas as pd
        return pd.read_parquet(parquet_path)

    print("Downloading dataset from HuggingFace...")
    ds = load_dataset("KeeganC/aat-museum-subset", split="train")
    df = ds.to_pandas()

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_parquet(parquet_path)
    print(f"Saved {len(df)} rows to {parquet_path}")
    return df

if __name__ == "__main__":
    df = load_aat_dataset()
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nFirst 3 rows:\n{df.head(3)}")
    print(f"\nNull counts:\n{df.isnull().sum()}")
