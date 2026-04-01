"""Hierarchy & taxonomy analysis — parent-child relationships, tree structure."""
import pandas as pd
from collections import Counter, defaultdict

df = pd.read_parquet("src/analysis/data_cache/aat_museum_subset.parquet")

print("=" * 60)
print("PARENT-CHILD RELATIONSHIP ANALYSIS")
print("=" * 60)

children_per_parent = df.groupby("parent_id").size()
print(f"  Total unique parents: {len(children_per_parent):,}")
print(f"  Avg children per parent: {children_per_parent.mean():.1f}")
print(f"  Median: {children_per_parent.median():.0f}")
print(f"  Max: {children_per_parent.max()} (parent_id={children_per_parent.idxmax()})")

leaf_ids = set(df["subject_id"]) - set(df["parent_id"])
print(f"\n  Leaf nodes (no children): {len(leaf_ids):,} ({100 * len(leaf_ids) / len(df):.1f}%)")
print(f"  Internal nodes (have children): {len(df) - len(leaf_ids):,}")

print("\n  Children count distribution:")
bins = [(1, 1), (2, 2), (3, 5), (6, 10), (11, 25), (26, 50), (51, 100), (101, 500)]
for lo, hi in bins:
    count = ((children_per_parent >= lo) & (children_per_parent <= hi)).sum()
    print(f"    {lo:>3d}-{hi:>3d} children: {count:>5,} parents")

print("\n" + "=" * 60)
print("TREE DEPTH RECONSTRUCTION")
print("=" * 60)

parent_map = dict(zip(df["subject_id"], df["parent_id"]))
term_map = dict(zip(df["subject_id"], df["preferred_term"]))
all_ids = set(df["subject_id"])

def get_depth(subject_id, memo={}):
    if subject_id in memo:
        return memo[subject_id]
    pid = parent_map.get(subject_id)
    if pid is None or pid not in parent_map or pid == subject_id:
        memo[subject_id] = 0
        return 0
    depth = get_depth(pid, memo) + 1
    memo[subject_id] = depth
    return depth

depths = {}
for sid in df["subject_id"]:
    depths[sid] = get_depth(sid)

df["tree_depth"] = df["subject_id"].map(depths)

depth_dist = df["tree_depth"].value_counts().sort_index()
print("Tree depth distribution:")
for d, count in depth_dist.items():
    bar = "█" * max(1, int(50 * count / depth_dist.max()))
    pct = 100 * count / len(df)
    print(f"  Depth {d:>2d}: {count:>6,} ({pct:>5.1f}%) {bar}")

max_depth_row = df.loc[df["tree_depth"].idxmax()]
print(f"\n  Deepest term: '{max_depth_row['preferred_term']}' at depth {max_depth_row['tree_depth']}")

print("\n  Path of deepest term:")
sid = max_depth_row["subject_id"]
path = []
visited = set()
while sid in parent_map and sid not in visited:
    visited.add(sid)
    path.append(term_map.get(sid, str(sid)))
    sid = parent_map[sid]
for i, p in enumerate(reversed(path)):
    print(f"    {'  ' * i}└─ {p}")

print("\n" + "=" * 60)
print("FACET × DEPTH MATRIX")
print("=" * 60)

facet_depth = df.groupby(["hierarchy", "tree_depth"]).size().unstack(fill_value=0)
print(facet_depth.to_string())

print("\n" + "=" * 60)
print("BRANCHING FACTOR BY FACET")
print("=" * 60)

for facet in df["hierarchy"].value_counts().head(6).index:
    facet_df = df[df["hierarchy"] == facet]
    facet_parents = facet_df.groupby("parent_id").size()
    avg_branch = facet_parents.mean()
    max_branch = facet_parents.max()
    print(f"  {facet:40s} → avg branching: {avg_branch:.1f}, max: {max_branch}")

print("\n" + "=" * 60)
print("ORPHAN / ROOT DETECTION")
print("=" * 60)

parent_ids_in_data = set(df["parent_id"])
subject_ids = set(df["subject_id"])
external_parents = parent_ids_in_data - subject_ids
print(f"  Parents that are NOT in the dataset: {len(external_parents):,}")
print(f"  These are references to higher-level AAT nodes not in this subset")

roots_in_data = df[~df["parent_id"].isin(subject_ids)]
print(f"  Root-level entries (parent not in dataset): {len(roots_in_data):,}")
print(f"  Distribution by facet:")
for facet, count in roots_in_data["hierarchy"].value_counts().items():
    print(f"    {facet:40s} → {count:>5,}")

print("\n" + "=" * 60)
print("LARGEST SUB-TREES (by subject_id)")
print("=" * 60)

children_map = defaultdict(list)
for _, row in df.iterrows():
    if row["parent_id"] in subject_ids:
        children_map[row["parent_id"]].append(row["subject_id"])

def subtree_size(node_id, memo={}):
    if node_id in memo:
        return memo[node_id]
    size = 1
    for child in children_map.get(node_id, []):
        size += subtree_size(child, memo)
    memo[node_id] = size
    return size

internal_nodes = subject_ids - leaf_ids
sizes = {nid: subtree_size(nid) for nid in list(internal_nodes)[:5000]}
top_subtrees = sorted(sizes.items(), key=lambda x: -x[1])[:20]
print("Top 20 largest sub-trees:")
for nid, size in top_subtrees:
    name = term_map.get(nid, "?")
    facet = df.loc[df["subject_id"] == nid, "hierarchy"].iloc[0]
    print(f"  {name:50s} [{facet:20s}] → {size:>5,} descendants")
