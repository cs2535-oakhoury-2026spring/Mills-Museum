"""
MCAM Art Keyword Generator — HuggingFace Spaces Server

Loads a multi-collection ChromaDB from HuggingFace, embeds query images,
retrieves + reranks AAT keywords, and serves the React frontend.

Configuration via environment variables:
    COLLECTION_NAME  — which ChromaDB collection to query (default: aat_terms_qwen2b)
    EMBEDDING_TYPE   — "qwen" or "openclip" (default: qwen)
    VDB_REPO         — HF dataset repo for the VDB (default: KeeganCarey/mcam-vdb)
    TERM_COUNT       — default number of keywords to return (default: 20)
    LAMBDA_MULT      — MMR diversity parameter (default: 0.96)
"""

import os
import sys
import math
import base64
import io
import importlib.util
from typing import Optional

import torch
import chromadb
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download, snapshot_download
from langchain_chroma import Chroma
from llama_cpp import Llama
from PIL import Image
from tqdm import tqdm

# ─── Configuration ────────────────────────────────────────────────────────────

COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "aat_terms_qwen2b")
EMBEDDING_TYPE = os.environ.get("EMBEDDING_TYPE", "qwen")
VDB_REPO = os.environ.get("VDB_REPO", "KeeganCarey/mcam-vdb")
TERM_COUNT = int(os.environ.get("TERM_COUNT", "20"))
LAMBDA_MULT = float(os.environ.get("LAMBDA_MULT", "0.96"))

EMBEDDING_MODELS = {
    "qwen": {"model_id": "Qwen/Qwen3-VL-Embedding-2B"},
    "openclip": {"model_id": "ViT-SO400M-14-SigLIP-384", "pretrained": "webli"},
}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {DEVICE}")

# ─── Load Vector Store ────────────────────────────────────────────────────────

print(f"Downloading VDB from {VDB_REPO}...")
VDB_PATH = snapshot_download(repo_id=VDB_REPO, repo_type="dataset")

_chroma_client = chromadb.PersistentClient(path=VDB_PATH)
available_collections = [c.name for c in _chroma_client.list_collections()]
print(f"Available collections: {available_collections}")

assert COLLECTION_NAME in available_collections, (
    f"Collection '{COLLECTION_NAME}' not found. Available: {available_collections}"
)

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=VDB_PATH,
    collection_metadata={"hnsw:space": "cosine"},
)
print(f"Loaded '{COLLECTION_NAME}' — {vectorstore._collection.count()} documents")

# Pre-compute facets and hierarchies
_all_meta = vectorstore._collection.get(include=["metadatas"])
AVAILABLE_FACETS = sorted(set(
    m.get("facet", "") for m in _all_meta["metadatas"] if m.get("facet")
))
AVAILABLE_HIERARCHIES = sorted(set(
    m.get("hierarchy", "") for m in _all_meta["metadatas"] if m.get("hierarchy")
))
del _all_meta
print(f"Facets ({len(AVAILABLE_FACETS)}): {AVAILABLE_FACETS}")
print(f"Hierarchies ({len(AVAILABLE_HIERARCHIES)}): {AVAILABLE_HIERARCHIES}")

# ─── Load Embedding Model ────────────────────────────────────────────────────

try:
    import flash_attn  # noqa: F401
    ATTN_IMPL = "flash_attention_2"
    print("Flash Attention available")
except ImportError:
    ATTN_IMPL = "sdpa"
    print("Using SDPA attention")

embed_cfg = EMBEDDING_MODELS[EMBEDDING_TYPE]
_embed_model_id = embed_cfg["model_id"]

if EMBEDDING_TYPE == "qwen":
    _script = hf_hub_download(repo_id=_embed_model_id, filename="scripts/qwen3_vl_embedding.py")
    _spec = importlib.util.spec_from_file_location("qwen3_vl_embedding", _script)
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["qwen3_vl_embedding"] = _mod
    _spec.loader.exec_module(_mod)

    _embedding_model = _mod.Qwen3VLEmbedder(
        model_name_or_path=_embed_model_id,
        dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        attn_implementation=ATTN_IMPL,
    )

    def embed_image(image: Image.Image) -> list[float]:
        features = _embedding_model.process([{"image": image, "text": ""}])
        features = torch.nn.functional.normalize(features, p=2, dim=1)
        return features.cpu().float().squeeze().tolist()

elif EMBEDDING_TYPE == "openclip":
    import open_clip

    _pretrained = embed_cfg.get("pretrained", "webli")
    _oc_model, _, _oc_preprocess = open_clip.create_model_and_transforms(
        _embed_model_id, pretrained=_pretrained, device=DEVICE,
    )
    _oc_model.eval()

    def embed_image(image: Image.Image) -> list[float]:
        img_tensor = _oc_preprocess(image).unsqueeze(0).to(DEVICE)
        with torch.no_grad(), torch.amp.autocast(DEVICE):
            features = _oc_model.encode_image(img_tensor)
            features = torch.nn.functional.normalize(features, p=2, dim=1)
        return features.cpu().float().squeeze().tolist()

else:
    raise ValueError(f"Unknown EMBEDDING_TYPE: {EMBEDDING_TYPE}")

print(f"Loaded {EMBEDDING_TYPE} embedding model: {_embed_model_id}")

# ─── Load Reranker ────────────────────────────────────────────────────────────

print("Loading Qwen3-VL-Reranker-2B GGUF...")
_reranker_gguf = hf_hub_download(
    repo_id="mradermacher/Qwen3-VL-Reranker-2B-i1-GGUF",
    filename="Qwen3-VL-Reranker-2B.i1-Q6_K.gguf",
)
_reranker_mmproj = hf_hub_download(
    repo_id="mradermacher/Qwen3-VL-Reranker-2B-GGUF",
    filename="Qwen3-VL-Reranker-2B.mmproj-Q8_0.gguf",
)

_reranker_llm = Llama(
    model_path=_reranker_gguf,
    clip_model_path=_reranker_mmproj,
    n_ctx=4096,
    n_gpu_layers=-1,
    logits_all=False,
    verbose=False,
)
print("Reranker loaded!")


def _pil_to_data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def rerank_with_gguf(
    instruction: str, query: dict, documents: list[dict]
) -> list[float]:
    img_uri = _pil_to_data_uri(query["image"]) if query.get("image") else None
    query_text = query.get("text", "")
    scores = []

    for doc in tqdm(documents, desc="Reranking"):
        user_content = []
        if img_uri:
            user_content.append({"type": "image_url", "image_url": {"url": img_uri}})
        user_content.append({
            "type": "text",
            "text": (
                f"Instruction: {instruction}\n"
                f"Query: {query_text}\n"
                f"Document: {doc['text']}\n"
                "Is the Document relevant to the Query? Answer only 'yes' or 'no'."
            ),
        })

        messages = [
            {"role": "system", "content": "Judge whether the Document is relevant to the Query. Answer only 'yes' or 'no'."},
            {"role": "user", "content": user_content},
        ]

        resp = _reranker_llm.create_chat_completion(
            messages=messages,
            max_tokens=1,
            logprobs=True,
            top_logprobs=10,
            temperature=0.0,
        )

        top_lps = resp["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
        lp_map = {entry["token"].strip().lower(): entry["logprob"] for entry in top_lps}
        lp_yes = lp_map.get("yes", -100.0)
        lp_no = lp_map.get("no", -100.0)
        scores.append(math.exp(lp_yes) / (math.exp(lp_yes) + math.exp(lp_no)))

    return scores


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(title="MCAM Art Keyword Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/collections")
async def list_collections():
    return {
        "active": COLLECTION_NAME,
        "available": available_collections,
    }


@app.get("/facets")
async def list_facets():
    return {
        "facets": AVAILABLE_FACETS,
        "hierarchies": AVAILABLE_HIERARCHIES,
    }


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    term_count: int = Form(default=TERM_COUNT),
    facets: Optional[str] = Form(default=None),
    hierarchies: Optional[str] = Form(default=None),
):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    query_embedding = embed_image(image)

    # Build optional where-filter
    conditions = []
    if facets:
        facet_list = [f.strip() for f in facets.split(",")]
        conditions.append({"facet": {"$in": facet_list}})
    if hierarchies:
        hierarchy_list = [h.strip() for h in hierarchies.split(",")]
        conditions.append({"hierarchy": {"$in": hierarchy_list}})

    where_filter = None
    if len(conditions) == 1:
        where_filter = conditions[0]
    elif len(conditions) > 1:
        where_filter = {"$and": conditions}

    mmr_docs = vectorstore.max_marginal_relevance_search_by_vector(
        embedding=query_embedding,
        k=term_count,
        fetch_k=term_count * 4,
        lambda_mult=LAMBDA_MULT,
        filter=where_filter,
    )

    labels = []
    input_docs = []
    doc_metadata = []
    for doc in mmr_docs:
        term = doc.metadata.get("preferred_term", doc.page_content.split(":")[0])
        labels.append(term)
        input_docs.append({"text": doc.page_content})
        doc_metadata.append(doc.metadata)

    scores = rerank_with_gguf(
        instruction="Retrieve Art & Architecture Thesaurus terms relevant to the given image.",
        query={"image": image, "text": ""},
        documents=input_docs,
    )

    sorted_results = sorted(zip(scores, labels, doc_metadata), reverse=True)

    keywords = [
        {
            "label": label,
            "score": round(float(score) * 100, 1),
            "facet": meta.get("facet", ""),
            "hierarchy": meta.get("hierarchy", ""),
            "subject_id": meta.get("subject_id", ""),
        }
        for score, label, meta in sorted_results
    ]

    return {"keywords": keywords}


# Serve the built React frontend as a catch-all (after API routes)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
else:
    print(f"Warning: static directory not found at {STATIC_DIR}")


if __name__ == "__main__":
    import uvicorn
    # HF Spaces expects port 7860
    uvicorn.run(app, host="0.0.0.0", port=7860)
