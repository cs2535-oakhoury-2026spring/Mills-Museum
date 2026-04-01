"""Deep profiling of the AAT museum subset dataset."""
import pandas as pd

df = pd.read_parquet("src/analysis/data_cache/aat_museum_subset.parquet")

# variant_terms may be stored as arrays — convert to string for analysis
if df["variant_terms"].apply(type).iloc[0] != str:
    df["variant_terms_list"] = df["variant_terms"]
    df["variant_terms"] = df["variant_terms"].apply(lambda x: ", ".join(x) if isinstance(x, (list,)) else str(x))

print("=" * 60)
print("BASIC SHAPE & TYPES")
print("=" * 60)
print(f"Rows: {len(df):,}  |  Columns: {len(df.columns)}")
print(f"\nColumn types:\n{df.dtypes}\n")

print("=" * 60)
print("UNIQUE VALUES PER COLUMN")
print("=" * 60)
for col in df.columns:
    if col == "variant_terms_list":
        continue
    nuniq = df[col].nunique()
    nulls = df[col].isnull().sum()
    print(f"  {col:20s} → {nuniq:>6,} unique, {nulls:>5,} nulls")

print("\n" + "=" * 60)
print("FACET DISTRIBUTION")
print("=" * 60)
facet_counts = df["facet"].value_counts()
for facet, count in facet_counts.items():
    print(f"  {facet:50s} → {count:>6,} ({100*count/len(df):.1f}%)")

print("\n" + "=" * 60)
print("RECORD TYPE DISTRIBUTION")
print("=" * 60)
rt_counts = df["record_type"].value_counts()
for rt, count in rt_counts.items():
    print(f"  {rt:30s} → {count:>6,} ({100*count/len(df):.1f}%)")

print("\n" + "=" * 60)
print("HIERARCHY — TOP 20 ROOT HIERARCHIES")
print("=" * 60)
hierarchy_top = df["hierarchy"].str.split(",").str[0].value_counts().head(20)
for h, count in hierarchy_top.items():
    print(f"  {h.strip():50s} → {count:>6,}")

print("\n" + "=" * 60)
print("PARENT TERM — TOP 30 MOST COMMON PARENTS")
print("=" * 60)
parent_counts = df["parent_term"].value_counts().head(30)
for p, count in parent_counts.items():
    print(f"  {p:50s} → {count:>6,} children")

print("\n" + "=" * 60)
print("PREFERRED TERM — BASIC TEXT STATS")
print("=" * 60)
term_lengths = df["preferred_term"].str.len()
word_counts = df["preferred_term"].str.split().str.len()
print(f"  Avg term length: {term_lengths.mean():.1f} chars")
print(f"  Median term length: {term_lengths.median():.1f} chars")
print(f"  Max term length: {term_lengths.max()} chars → '{df.loc[term_lengths.idxmax(), 'preferred_term']}'")
print(f"  Avg word count: {word_counts.mean():.1f} words")
print(f"  Single-word terms: {(word_counts == 1).sum():,} ({100*(word_counts == 1).mean():.1f}%)")
print(f"  Multi-word terms: {(word_counts > 1).sum():,} ({100*(word_counts > 1).mean():.1f}%)")

print("\n" + "=" * 60)
print("VARIANT TERMS — STATS")
print("=" * 60)
if "variant_terms_list" in df.columns:
    variant_counts = df["variant_terms_list"].apply(lambda x: len(x) if isinstance(x, list) else 1)
else:
    variant_counts = df["variant_terms"].str.split(",").str.len()
print(f"  Avg variants per term: {variant_counts.mean():.1f}")
print(f"  Max variants: {variant_counts.max()}")
print(f"  Terms with 1 variant (just itself): {(variant_counts == 1).sum():,}")
print(f"  Terms with 5+ variants: {(variant_counts >= 5).sum():,}")

print("\n" + "=" * 60)
print("SCOPE NOTE — COVERAGE & STATS")
print("=" * 60)
has_scope = df["scope_note"].notna()
print(f"  Has scope note: {has_scope.sum():,} ({100*has_scope.mean():.1f}%)")
print(f"  Missing scope note: {(~has_scope).sum():,} ({100*(~has_scope).mean():.1f}%)")
scope_lengths = df.loc[has_scope, "scope_note"].str.len()
print(f"  Avg scope note length: {scope_lengths.mean():.1f} chars")
print(f"  Median scope note length: {scope_lengths.median():.1f} chars")
print(f"  Max scope note length: {scope_lengths.max():,} chars")

print("\n" + "=" * 60)
print("HIERARCHY DEPTH ANALYSIS")
print("=" * 60)
depths = df["hierarchy"].str.split(",").str.len()
print(f"  Avg depth: {depths.mean():.1f}")
print(f"  Max depth: {depths.max()}")
depth_dist = depths.value_counts().sort_index()
for d, count in depth_dist.items():
    bar = "█" * max(1, int(50 * count / depth_dist.max()))
    print(f"  Depth {d:>2d}: {count:>5,} {bar}")

print("\n" + "=" * 60)
print("SAMPLE DEEP HIERARCHIES (depth >= 8)")
print("=" * 60)
deep = df[depths >= 8].head(10)
for _, row in deep.iterrows():
    print(f"  {row['preferred_term']}")
    print(f"    Path: {row['hierarchy'][:120]}...")
    print()

print("\n" + "=" * 60)
print("TOP 20 MOST FREQUENT WORDS IN PREFERRED TERMS")
print("=" * 60)
from collections import Counter
all_words = Counter()
for term in df["preferred_term"].str.lower():
    all_words.update(term.split())
stopwords = {"and", "of", "the", "for", "in", "with", "a", "an", "to", "or", "by", "on", "at", "as", "is"}
filtered_words = {w: c for w, c in all_words.items() if w not in stopwords and len(w) > 2}
for word, count in Counter(filtered_words).most_common(20):
    print(f"  {word:25s} → {count:>5,}")
