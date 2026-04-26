# Retrieval Pipeline Findings

Results from testing on Modal (A100 GPU) with the SigLIP + Qwen reranker pipeline.

## What we tested

- **Retrieval model**: SigLIP (ViT-SO400M-14-SigLIP-384, WebLI pretrained) via OpenCLIP
- **Reranker model**: Qwen3-VL-Reranker-2B (multimodal vision-language reranker)
- **Vector store**: ChromaDB with cosine similarity, 44,225 AAT terms embedded with SigLIP text encoder
- **Selection**: LangChain MMR (Maximal Marginal Relevance) for diverse candidate retrieval

## What changed from the current MCAM.ipynb

The current notebook uses **Qwen3-VL-Embedding-2B** for both text embedding and image querying. This produces terrible results (max ~17% confidence, irrelevant keywords like "cornice planes" and "Mezilaurus") because Qwen's embedding space doesn't align text and image modalities well.

Swapping retrieval to **SigLIP** (designed specifically for cross-modal text-image alignment) and keeping **Qwen as a reranker only** produced dramatically better results.

## Results

### Mills Museum building (Spanish Colonial Revival, stone lion sculptures)

| Rank | Keyword | Confidence |
|------|---------|-----------|
| 1 | bixie (mythical guardian lion) | 55.86% |
| 2 | simhasikha (lion architectural element) | 45.90% |
| 3 | simhapatti (lion motif) | 45.70% |
| 4 | haciendas | 34.38% |
| 5 | gardens of rest | 33.01% |
| 6 | chiwei (roof ornament) | 32.42% |
| 7 | ceremonial gates | 32.03% |
| 8 | lion-head spouts | 30.27% |

Mean confidence: 32.9% (up from 10.4% with Qwen embedding)

Previous best run with Qwen embedding: "Spanish Colonial Revival" at 51.56% appeared once with pool=96, lambda=0.78, but was lost with other settings. The SigLIP pipeline consistently surfaces lion/guardian and architectural terms.

### Hokusai - The Great Wave

| Rank | Keyword | Confidence |
|------|---------|-----------|
| 1 | Hokusai School | 50.00% |
| 2 | bokashi (printing technique) | 49.02% |
| 3 | Japanese painting styles | 38.28% |
| 4 | tidal waves | 35.74% |
| 5 | Nagasaki | 26.56% |
| 6 | roiling cloud brush strokes | 16.41% |

Mean confidence: 29.64%. Top results are genuinely accurate for this artwork.

## Recommended changes to MCAM.ipynb

### 1. Swap embedding model (highest impact)

Replace Qwen3-VL-Embedding-2B with SigLIP for retrieval. Keep Qwen3-VL-Reranker-2B for scoring.

**Why**: SigLIP is trained with a contrastive objective that aligns text and image embeddings in the same space. Qwen's embedding model produces separate text/image spaces that don't cross-match well. This single change took max confidence from ~17% to ~56%.

### 2. Use a two-stage retrieve-then-rerank pipeline

Stage 1: SigLIP embeds the image, queries ChromaDB for top candidates via MMR.
Stage 2: Qwen reranker scores each candidate against the image with its vision-language model.

**Why**: SigLIP is fast at retrieval (one forward pass) but shallow. Qwen's reranker is slow but deeply understands image content. Combining them gets the best of both.

### 3. Tune MMR parameters

Best settings found so far:
- `CANDIDATE_POOL_SIZE = 128` (fetch 128 from VDB, return top 12)
- `MMR_LAMBDA = 0.72` (balance between relevance and diversity)

**Why**: Too small a pool misses good candidates. Too much diversity (low lambda) loses the most relevant terms. 128/0.72 was the sweet spot across test images.

### 4. Embed AAT terms with scope notes

Instead of embedding just the term name, embed `"preferred_term : scope_note"`. This gives SigLIP more context to match against.

**Why**: "bixie" alone is cryptic, but "bixie : mythical winged guardian creatures in Chinese architecture" gives the text encoder much more to work with when comparing against an image of stone lions.

### 5. Add artwork metadata to queries (optional)

When title or medium is known, include it as text context alongside the image embedding.

**Why**: A multimodal query like "Title: Mills Hall. Medium: stone and stucco" helps the reranker prioritize architectural terms over, say, painting techniques. This didn't help with Qwen embedding (made it worse) but should help with the SigLIP + reranker pipeline.

## What still needs work

- **Confidence scores are still modest** (max ~56%). This is partly inherent to the 44K-term AAT — many terms are highly specialized and the model has to pick from a huge, sparse vocabulary.
- **Geographic bias**: SigLIP tends to surface Asian architectural terms for Western buildings (e.g., "Shinden", "Loudong" for Mills Museum). This may be a bias in the WebLI training data. A post-filter or weighted penalty for culturally mismatched terms could help.
- **No text-only fallback**: When SigLIP retrieval returns poor candidates, there's no fallback to text-based search. A hybrid approach could help.
- **Sunflower and Starry Night runs** were interrupted by HuggingFace timeouts during parallel execution. Run them one at a time to complete the evaluation.
