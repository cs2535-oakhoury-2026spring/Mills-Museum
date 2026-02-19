#!/usr/bin/env python3
"""Semantic deduplication pipeline for museum term labels.

Implements the workflow in CODEX.md:
- Embed unique labels with sentence-transformers (`all-MiniLM-L6-v2`)
- Cluster with FAISS IndexFlatIP + Union-Find (language-aware, no cross-language merges)
- Select canonical labels per cluster
- Build deduplicated parquet + audit CSV + full term_id mapping CSV
- Compute two before/after metrics:
  1) Semantic Collision Rate (quality)
  2) Normalized Token Entropy (diversity)

Dependencies (CPU only):
    pip install pandas pyarrow sentence-transformers faiss-cpu numpy
"""

from __future__ import annotations

import argparse
import importlib.metadata
import math
import random
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

LANG_NULL_TOKEN = "__NULL_LANGUAGE__"
DEFAULT_MODEL = "all-MiniLM-L6-v2"


def _is_dist_installed(dist_name: str) -> bool:
    name = dist_name.casefold()
    for dist in importlib.metadata.distributions():
        md_name = (dist.metadata.get("Name") or "").casefold()
        if md_name == name:
            return True
    return False


def _pip_install(packages: List[str]) -> None:
    cmd = [sys.executable, "-m", "pip", "install", *packages]
    print(f"Attempting dependency install: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def check_dependencies(auto_install_deps: bool) -> None:
    missing = []

    try:
        import faiss  # noqa: F401
    except ImportError:
        missing.append("faiss-cpu")

    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
    except ImportError:
        missing.append("sentence-transformers")

    if missing and auto_install_deps:
        _pip_install(missing)
        missing = []
        try:
            import faiss  # noqa: F401
            from sentence_transformers import SentenceTransformer  # noqa: F401
        except ImportError as exc:
            raise SystemExit(
                "Dependency auto-install ran but imports still fail. "
                "Please install manually: pip install faiss-cpu sentence-transformers"
            ) from exc

    if missing:
        raise SystemExit(
            "Missing dependencies: "
            + ", ".join(missing)
            + ". Install with: pip install faiss-cpu sentence-transformers"
        )

    if _is_dist_installed("faiss-gpu"):
        print(
            "Warning: faiss-gpu appears installed. "
            "This pipeline is designed for CPU FAISS (`faiss-cpu`)."
        )


class UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


@dataclass
class Cluster:
    cluster_id: str
    language_key: str
    canonical_label: str
    members: List[str]

    @property
    def merged_labels(self) -> List[str]:
        return [x for x in self.members if x != self.canonical_label]

    @property
    def cluster_size(self) -> int:
        return len(self.members)


def normalize_language(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna(LANG_NULL_TOKEN)


def print_step1_inspection(df: pd.DataFrame) -> None:
    print("\n=== Step 1: Load and Inspect ===")
    print(f"Shape: {df.shape}")
    print("Dtypes:")
    print(df.dtypes.to_string())
    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))
    print("\nTop term_label value_counts (20):")
    print(df["term_label"].value_counts(dropna=False).head(20).to_string())


def l2_normalize(arr: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return arr / norms


def encode_labels(
    labels: List[str],
    model_name: str,
    batch_size: int,
    device: str | None,
) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    model_kwargs = {}
    if device:
        model_kwargs["device"] = device
    model = SentenceTransformer(model_name, **model_kwargs)
    embeddings = model.encode(
        labels,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    embeddings = embeddings.astype(np.float32, copy=False)
    embeddings = l2_normalize(embeddings)
    return embeddings


def cluster_language_labels(
    language_key: str,
    labels: List[str],
    label_to_global_index: Dict[str, int],
    embeddings: np.ndarray,
    threshold: float,
    k_neighbors: int,
) -> List[List[str]]:
    import faiss

    if not labels:
        return []
    if len(labels) == 1:
        return [labels.copy()]

    subset_global_idx = np.array([label_to_global_index[label] for label in labels])
    subset_embeddings = embeddings[subset_global_idx]

    dim = subset_embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(subset_embeddings)

    k = min(k_neighbors, len(labels))
    sims, neigh = index.search(subset_embeddings, k)

    uf = UnionFind(len(labels))
    for i in range(len(labels)):
        for j_pos in range(k):
            j = int(neigh[i, j_pos])
            if j < 0 or j == i:
                continue
            if float(sims[i, j_pos]) >= threshold:
                uf.union(i, j)

    grouped: Dict[int, List[str]] = {}
    for i, label in enumerate(labels):
        root = uf.find(i)
        grouped.setdefault(root, []).append(label)

    # deterministic ordering
    clusters = [sorted(members) for members in grouped.values()]
    clusters.sort(key=lambda c: (len(c), c[0]), reverse=True)
    return clusters


def cluster_all_languages(
    language_to_labels: Dict[str, List[str]],
    label_to_global_index: Dict[str, int],
    embeddings: np.ndarray,
    threshold: float,
    k_neighbors: int,
) -> Dict[str, List[List[str]]]:
    out: Dict[str, List[List[str]]] = {}
    for language_key, labels in language_to_labels.items():
        out[language_key] = cluster_language_labels(
            language_key=language_key,
            labels=labels,
            label_to_global_index=label_to_global_index,
            embeddings=embeddings,
            threshold=threshold,
            k_neighbors=k_neighbors,
        )
    return out


def choose_canonical_label(
    language_key: str,
    members: List[str],
    has_note_lookup: Dict[Tuple[str, str], bool],
) -> str:
    # Priority:
    # 1) any non-null term_note
    # 2) shortest label
    # 3) alphabetical (case-insensitive then case-sensitive)
    ranked = sorted(
        members,
        key=lambda x: (
            not has_note_lookup.get((language_key, x), False),
            len(x),
            x.casefold(),
            x,
        ),
    )
    return ranked[0]


def build_clusters_with_canonicals(
    clustered: Dict[str, List[List[str]]],
    has_note_lookup: Dict[Tuple[str, str], bool],
) -> List[Cluster]:
    cluster_rows: List[Cluster] = []
    running_id = 0
    for language_key, clusters in clustered.items():
        for members in clusters:
            running_id += 1
            canonical = choose_canonical_label(language_key, members, has_note_lookup)
            cluster_rows.append(
                Cluster(
                    cluster_id=f"{language_key}::{running_id}",
                    language_key=language_key,
                    canonical_label=canonical,
                    members=sorted(members),
                )
            )
    return cluster_rows


def print_random_cluster_preview(
    clustered: Dict[str, List[List[str]]],
    sample_size: int,
    seed: int,
) -> None:
    multi = []
    for language_key, clusters in clustered.items():
        for members in clusters:
            if len(members) > 1:
                multi.append((language_key, members))

    print("\n=== Threshold Preview @ 0.85 (20 random multi-member clusters) ===")
    if not multi:
        print("No multi-member clusters found at threshold 0.85")
        return

    random.seed(seed)
    sampled = random.sample(multi, min(sample_size, len(multi)))
    for i, (language_key, members) in enumerate(sampled, start=1):
        language_id = None if language_key == LANG_NULL_TOKEN else language_key
        print(f"{i:02d}. language_id={language_id}, size={len(members)}")
        print("    " + " | ".join(members))


def prepare_label_structures(
    df: pd.DataFrame,
) -> Tuple[List[str], Dict[str, int], Dict[str, List[str]], Dict[Tuple[str, str], bool]]:
    # Global unique labels for embedding (as required).
    unique_labels = df["term_label"].drop_duplicates().tolist()
    label_to_global_index = {label: i for i, label in enumerate(unique_labels)}

    # Language-aware unique label groups.
    label_pairs = (
        df[["language_key", "term_label"]]
        .drop_duplicates()
        .sort_values(["language_key", "term_label"])
    )
    language_to_labels: Dict[str, List[str]] = {}
    for language_key, g in label_pairs.groupby("language_key", sort=True):
        language_to_labels[language_key] = g["term_label"].tolist()

    # For canonical selection priority #1 (has non-null note).
    note_presence = (
        df.assign(has_note=df["term_note"].notna())
        .groupby(["language_key", "term_label"], as_index=False)["has_note"]
        .max()
    )
    has_note_lookup = {
        (row.language_key, row.term_label): bool(row.has_note)
        for row in note_presence.itertuples(index=False)
    }

    print("\n=== Step 2: Unique Labels ===")
    print(f"Unique term_labels (global): {len(unique_labels)}")
    print(
        "Language groups (unique labels): "
        + ", ".join(
            f"{(None if k == LANG_NULL_TOKEN else k)}={len(v)}"
            for k, v in language_to_labels.items()
        )
    )
    return unique_labels, label_to_global_index, language_to_labels, has_note_lookup


def build_lookup_tables(clusters: List[Cluster]) -> Dict[Tuple[str, str], Cluster]:
    lookup: Dict[Tuple[str, str], Cluster] = {}
    for cluster in clusters:
        for label in cluster.members:
            lookup[(cluster.language_key, label)] = cluster
    return lookup


def pick_best_row_for_label(group: pd.DataFrame) -> pd.Series:
    # Keep one row for a canonical label when exact duplicates exist:
    # prefer non-null note, then smallest term_id for deterministic behavior.
    sorted_group = group.assign(
        _has_note=group["term_note"].notna().astype(int),
        _term_id_num=pd.to_numeric(group["term_id"], errors="coerce"),
    ).sort_values(
        by=["_has_note", "_term_id_num", "term_id"],
        ascending=[False, True, True],
    )
    return sorted_group.iloc[0]


def make_audit_df(clusters: List[Cluster]) -> pd.DataFrame:
    rows = []
    for c in clusters:
        rows.append(
            {
                "cluster_id": c.cluster_id,
                "canonical_label": c.canonical_label,
                "merged_labels": ";".join(c.merged_labels),
                "cluster_size": c.cluster_size,
            }
        )
    return pd.DataFrame(rows)


def semantic_collision_rate(
    labels_by_language: Dict[str, List[str]],
    label_to_global_index: Dict[str, int],
    embeddings: np.ndarray,
    threshold: float,
) -> Tuple[float, float]:
    import faiss

    total = 0
    collisions = 0
    sims_accum: List[float] = []

    for _, labels in labels_by_language.items():
        n = len(labels)
        if n == 0:
            continue
        if n == 1:
            total += 1
            sims_accum.append(0.0)
            continue

        idx = np.array([label_to_global_index[label] for label in labels])
        emb = embeddings[idx]
        index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb)
        sims, _ = index.search(emb, 2)  # self + nearest non-self
        nn = sims[:, 1]
        total += n
        collisions += int((nn >= threshold).sum())
        sims_accum.extend(nn.tolist())

    rate = collisions / total if total else 0.0
    avg_nn = float(np.mean(sims_accum)) if sims_accum else 0.0
    return rate, avg_nn


def tokenize(text: str) -> List[str]:
    # Unicode-aware, keeps apostrophes in words.
    return re.findall(r"[^\W_]+(?:'[^\W_]+)?", text.casefold(), flags=re.UNICODE)


def normalized_token_entropy(labels: Iterable[str]) -> Tuple[float, int, int]:
    token_counts: Dict[str, int] = {}
    total_tokens = 0
    for label in labels:
        for tok in tokenize(label):
            token_counts[tok] = token_counts.get(tok, 0) + 1
            total_tokens += 1

    vocab_size = len(token_counts)
    if total_tokens == 0 or vocab_size <= 1:
        return 0.0, vocab_size, total_tokens

    probs = [count / total_tokens for count in token_counts.values()]
    entropy = -sum(p * math.log(p) for p in probs)
    max_entropy = math.log(vocab_size)
    normalized = entropy / max_entropy if max_entropy > 0 else 0.0
    return normalized, vocab_size, total_tokens


def summarize_clusters(clusters: List[Cluster], top_n: int = 10) -> None:
    print("\n=== Largest Clusters (Top 10) ===")
    biggest = sorted(clusters, key=lambda c: c.cluster_size, reverse=True)[:top_n]
    for i, c in enumerate(biggest, start=1):
        language_id = None if c.language_key == LANG_NULL_TOKEN else c.language_key
        print(
            f"{i:02d}. cluster_id={c.cluster_id} language_id={language_id} "
            f"size={c.cluster_size} canonical={c.canonical_label}"
        )
        print("    members: " + " | ".join(c.members))

    print("\n=== Cluster Size Distribution ===")
    size_dist = pd.Series([c.cluster_size for c in clusters]).value_counts().sort_index()
    print(size_dist.to_string())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Semantic deduplication pipeline")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/data.parquet"),
        help="Input parquet path",
    )
    parser.add_argument(
        "--output-parquet",
        type=Path,
        default=Path("data/data_deduped.parquet"),
        help="Output deduplicated parquet path",
    )
    parser.add_argument(
        "--audit-csv",
        type=Path,
        default=Path("data/dedup_audit.csv"),
        help="Output audit CSV path",
    )
    parser.add_argument(
        "--mapping-csv",
        type=Path,
        default=Path("data/dedup_term_id_mapping.csv"),
        help="Output full term_id->canonical mapping CSV path",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=DEFAULT_MODEL,
        help="Sentence-transformer model name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=256,
        help="Embedding batch size",
    )
    parser.add_argument(
        "--k-neighbors",
        type=int,
        default=20,
        help="FAISS neighbors for union step",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Cosine similarity threshold for final clustering",
    )
    parser.add_argument(
        "--preview-threshold",
        type=float,
        default=0.85,
        help="Threshold used for mandatory preview clusters",
    )
    parser.add_argument(
        "--sample-preview",
        type=int,
        default=20,
        help="Random multi-cluster previews to print",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for preview sampling",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Optional sentence-transformers device (e.g., cpu, cuda)",
    )
    parser.add_argument(
        "--copy-input-backup",
        action="store_true",
        help="Create an explicit input backup copy next to input file",
    )
    parser.add_argument(
        "--auto-install-deps",
        action="store_true",
        help="Attempt pip install for missing deps (faiss-cpu, sentence-transformers)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    check_dependencies(auto_install_deps=args.auto_install_deps)

    if args.threshold <= 0 or args.threshold > 1:
        raise SystemExit("--threshold must be in (0, 1].")
    if args.preview_threshold <= 0 or args.preview_threshold > 1:
        raise SystemExit("--preview-threshold must be in (0, 1].")
    if args.k_neighbors < 2:
        raise SystemExit("--k-neighbors must be at least 2.")

    input_path: Path = args.input
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    if args.copy_input_backup:
        backup_path = input_path.with_name(input_path.stem + " (Copy).parquet")
        if not backup_path.exists():
            backup_path.write_bytes(input_path.read_bytes())
            print(f"Created backup copy: {backup_path}")
        else:
            print(f"Backup copy already exists: {backup_path}")

    df = pd.read_parquet(input_path)
    required = {"term_id", "term_label", "language_id", "term_note"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise SystemExit(f"Missing required columns: {sorted(missing_cols)}")

    # Keep source unchanged; operate on an in-memory copy with normalized dtypes.
    df = df.copy()
    for col in ["term_id", "term_label", "language_id", "term_note"]:
        df[col] = df[col].astype("string")
    df["language_key"] = normalize_language(df["language_id"])

    print_step1_inspection(df)

    (
        unique_labels,
        label_to_global_index,
        language_to_labels,
        has_note_lookup,
    ) = prepare_label_structures(df)

    print("\n=== Step 3: Generate Embeddings ===")
    print(f"Model: {args.model_name}")
    print(f"Unique labels to embed: {len(unique_labels)}")
    embeddings = encode_labels(
        labels=unique_labels,
        model_name=args.model_name,
        batch_size=args.batch_size,
        device=args.device,
    )
    print(f"Embeddings shape: {embeddings.shape}")

    print("\n=== Step 4: Cluster Similar Labels (Preview) ===")
    preview_clustered = cluster_all_languages(
        language_to_labels=language_to_labels,
        label_to_global_index=label_to_global_index,
        embeddings=embeddings,
        threshold=args.preview_threshold,
        k_neighbors=args.k_neighbors,
    )
    print_random_cluster_preview(
        clustered=preview_clustered,
        sample_size=args.sample_preview,
        seed=args.seed,
    )

    print("\n=== Step 4: Final Clustering ===")
    if args.threshold != args.preview_threshold:
        print(
            f"Final threshold differs from preview. "
            f"Preview={args.preview_threshold}, Final={args.threshold}"
        )
        final_clustered = cluster_all_languages(
            language_to_labels=language_to_labels,
            label_to_global_index=label_to_global_index,
            embeddings=embeddings,
            threshold=args.threshold,
            k_neighbors=args.k_neighbors,
        )
    else:
        final_clustered = preview_clustered
    print("Clustering complete.")

    print("\n=== Step 5: Select Canonical Labels ===")
    clusters = build_clusters_with_canonicals(final_clustered, has_note_lookup)
    print(f"Total clusters: {len(clusters)}")
    summarize_clusters(clusters)

    # Build per-label lookup tables.
    cluster_lookup = build_lookup_tables(clusters)

    # Add canonical data to every original row (for mapping and selections).
    def lookup_cluster(row: pd.Series) -> Cluster:
        return cluster_lookup[(row["language_key"], row["term_label"])]

    mapped_clusters = df.apply(lookup_cluster, axis=1)
    df["cluster_id"] = mapped_clusters.map(lambda c: c.cluster_id)
    df["canonical_label"] = mapped_clusters.map(lambda c: c.canonical_label)
    df["cluster_size"] = mapped_clusters.map(lambda c: c.cluster_size)
    df["merged_labels"] = mapped_clusters.map(lambda c: ";".join(c.merged_labels))

    print("\n=== Step 6: Build Output Dataset ===")
    # Keep only canonical-label rows, then keep one row per canonical label/language_key.
    canonical_rows = df[df["term_label"] == df["canonical_label"]].copy()
    canonical_rows["_has_note"] = canonical_rows["term_note"].notna().astype(int)
    canonical_rows["_term_id_num"] = pd.to_numeric(canonical_rows["term_id"], errors="coerce")
    deduped_rows = (
        canonical_rows.sort_values(
            by=[
                "language_key",
                "canonical_label",
                "_has_note",
                "_term_id_num",
                "term_id",
            ],
            ascending=[True, True, False, True, True],
        )
        .drop_duplicates(subset=["language_key", "canonical_label"], keep="first")
        .drop(columns=["_has_note", "_term_id_num"])
        .reset_index(drop=True)
    )
    deduped_rows["term_label"] = deduped_rows["canonical_label"]
    deduped_rows["language_id"] = deduped_rows["language_key"].replace({LANG_NULL_TOKEN: pd.NA})

    deduped = deduped_rows[
        [
            "term_id",
            "term_label",
            "language_id",
            "term_note",
            "merged_labels",
            "cluster_size",
            "cluster_id",
        ]
    ].copy()

    # Full mapping file so every original term_id maps exactly once.
    mapping_df = df[
        [
            "term_id",
            "term_label",
            "language_id",
            "canonical_label",
            "cluster_id",
            "cluster_size",
        ]
    ].copy()

    # Required audit file schema.
    audit_df = make_audit_df(clusters)

    args.output_parquet.parent.mkdir(parents=True, exist_ok=True)
    args.audit_csv.parent.mkdir(parents=True, exist_ok=True)
    args.mapping_csv.parent.mkdir(parents=True, exist_ok=True)

    deduped.to_parquet(args.output_parquet, index=False)
    audit_df.to_csv(args.audit_csv, index=False)
    mapping_df.to_csv(args.mapping_csv, index=False)

    print("\n=== Step 7: Save and Report ===")
    print(f"Saved deduplicated parquet: {args.output_parquet}")
    print(f"Saved audit CSV:          {args.audit_csv}")
    print(f"Saved mapping CSV:        {args.mapping_csv}")

    original_unique = int(df["term_label"].nunique(dropna=True))
    dedup_unique = int(deduped["term_label"].nunique(dropna=True))
    removed = original_unique - dedup_unique

    print("\nSummary:")
    print(f"- Original unique labels: {original_unique}")
    print(f"- Deduplicated labels:    {dedup_unique}")
    print(f"- Labels removed:         {removed}")

    print("\n=== Metrics (Before vs After) ===")
    # Quality metric: semantic collision rate at final threshold.
    before_collision, before_avg_nn = semantic_collision_rate(
        labels_by_language=language_to_labels,
        label_to_global_index=label_to_global_index,
        embeddings=embeddings,
        threshold=args.threshold,
    )

    # Build after label groups from chosen canonical labels.
    after_labels_by_language: Dict[str, List[str]] = {}
    for c in clusters:
        after_labels_by_language.setdefault(c.language_key, []).append(c.canonical_label)

    after_collision, after_avg_nn = semantic_collision_rate(
        labels_by_language=after_labels_by_language,
        label_to_global_index=label_to_global_index,
        embeddings=embeddings,
        threshold=args.threshold,
    )

    # Diversity metric: normalized token entropy over unique labels.
    before_entropy, before_vocab, before_tokens = normalized_token_entropy(
        sorted(set(unique_labels))
    )
    after_unique_labels = sorted(set(deduped["term_label"].dropna().tolist()))
    after_entropy, after_vocab, after_tokens = normalized_token_entropy(after_unique_labels)

    print(
        "Quality metric (Semantic Collision Rate @ threshold): "
        f"{before_collision:.4f} -> {after_collision:.4f} "
        f"(delta {after_collision - before_collision:+.4f})"
    )
    print(
        "Quality helper (Avg nearest-neighbor cosine): "
        f"{before_avg_nn:.4f} -> {after_avg_nn:.4f}"
    )
    print(
        "Diversity metric (Normalized Token Entropy): "
        f"{before_entropy:.4f} -> {after_entropy:.4f} "
        f"(delta {after_entropy - before_entropy:+.4f})"
    )
    print(
        f"Diversity helper (vocab/tokens): "
        f"{before_vocab}/{before_tokens} -> {after_vocab}/{after_tokens}"
    )

    print("\n=== Metric Tests ===")
    test_quality = after_collision <= before_collision
    test_diversity = after_entropy >= (before_entropy * 0.90)
    print(
        f"[{'PASS' if test_quality else 'FAIL'}] Semantic collision rate did not increase"
    )
    print(
        f"[{'PASS' if test_diversity else 'FAIL'}] Normalized token entropy retained at >=90%"
    )


if __name__ == "__main__":
    main()
