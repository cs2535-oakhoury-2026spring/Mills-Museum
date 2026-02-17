# Task: Semantic Deduplication of Museum Term Labels

## Objective

You have a parquet file of ~58,800 museum vocabulary terms. Many labels are semantically similar or near-duplicates (e.g., "oil painting" vs "oil piece", "hand knives" vs "hawkbill knives"). Your job is to **embed all term labels into vectors, cluster semantically similar ones, and produce a deduplicated dataset** with one canonical label per cluster.

---

## Input

- **File**: `/Users/alazarmanakelew/PycharmProjects/Mills-Museum/filtration/Train Data.parquet`
- **Rows**: 58,799
- **Columns**: `term_id` (string), `term_label` (string), `language_id` (string, 19% null), `term_note` (string, 19% null)
- **Key stats**:
  - 56,317 unique labels (some exact duplicates exist across different term_ids)
  - Labels are short: avg 1.72 words, median 2 words, max 11 words
  - 1,783 labels contain non-ASCII characters (accents/diacritics)
  - `language_id` and `term_note` are always null together (11,288 rows)

## Steps

### Step 1: Load and Inspect

```
- Read the parquet file with pandas
- Print shape, column dtypes, and first 10 rows
- Print value_counts of term_label to confirm duplicates
```

### Step 2: Extract Unique Labels

```
- Get the list of unique term_labels (56,317 values)
- You will embed these unique labels, NOT all 58,799 rows
- Keep a mapping from each unique label back to all its term_ids
```

### Step 3: Generate Embeddings

```
- Use sentence-transformers library with model 'all-MiniLM-L6-v2'
- Encode all 56,317 unique labels
  - Use batch_size=256 and show_progress_bar=True
- Normalize the embeddings to unit vectors (L2 norm) so dot product = cosine similarity
- Result: a numpy array of shape (56317, 384)
```

### Step 4: Cluster Similar Labels

**Use FAISS + Union-Find, NOT agglomerative clustering** (agglomerative would need a 56k×56k distance matrix — too much memory).

```
Approach:
1. Build a FAISS IndexFlatIP (inner product) index from the normalized embeddings
2. For each embedding, search for its k=20 nearest neighbors
3. For each neighbor pair where cosine similarity >= THRESHOLD, union them
4. Use a Union-Find (disjoint set) data structure to group connected components
5. Each connected component = one cluster of near-duplicate labels

- Set THRESHOLD = 0.85 as initial value
  - This is cosine similarity (not distance), so 0.85 = very similar
  - Lower threshold = more aggressive merging
  - Higher threshold = more conservative, keeps more labels
```

### Step 5: Select Canonical Labels

```
For each cluster:
- If cluster has 1 member → keep it as-is
- If cluster has 2+ members:
  - Pick the canonical label using this priority:
    1. Prefer labels that have a non-null term_note (they're more "official")
    2. Among those, prefer the shortest label (likely the most general/clean form)
    3. Tiebreak: alphabetically first
  - Log the merge: print each cluster's members so the user can audit
```

### Step 6: Build Output Dataset

```
- Create a new dataframe with only the rows whose term_label is the canonical label
- If multiple rows share a canonical label (exact duplicates), keep only one per label
  - Prefer the row with a non-null term_note
- Add a column 'merged_labels' that lists all the other labels that were merged into this one
- Add a column 'cluster_size' with how many labels were in the cluster
```

### Step 7: Save and Report

```
- Save the deduplicated dataframe to:
  /Users/alazarmanakelew/PycharmProjects/Mills-Museum/filtration/Train Data Deduped.parquet

- Also save a CSV audit log to:
  /Users/alazarmanakelew/PycharmProjects/Mills-Museum/filtration/dedup_audit.csv
  Columns: cluster_id, canonical_label, merged_labels (semicolon-separated), cluster_size

- Print a summary:
  - Original unique labels: X
  - Deduplicated labels: Y
  - Labels removed: Z
  - Largest clusters (top 10) with their members
  - Distribution of cluster sizes
```

---

## Important Constraints

1. **Do NOT merge labels across different languages.** If `language_id` differs between two labels, do not cluster them together even if embeddings are similar (e.g., an English term and its French equivalent should stay separate). For the 11,288 rows with null `language_id`, treat null as its own language group.

2. **Threshold tuning**: Before committing to 0.85, first run the clustering and print 20 random multi-member clusters. If clusters look too aggressive (merging things that shouldn't be merged), raise to 0.90. If too conservative (obvious duplicates not merged), lower to 0.80.

3. **Non-ASCII labels**: Sentence-transformers handles unicode fine, no special preprocessing needed. Do NOT strip accents.

4. **Do not modify term_ids.** Every original term_id must map to exactly one canonical label in the output. Include a separate mapping file if needed.

5. **Install dependencies if missing**: `sentence-transformers`, `faiss-cpu`, `pandas`, `pyarrow`.

---

## Expected Outcome

- A cleaned parquet file with fewer rows, where semantically redundant labels have been collapsed
- An audit trail showing every merge decision
- A printed summary the user can review before using the data downstream