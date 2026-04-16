# ─── MCAM Art Keyword Generator — HuggingFace Spaces ─────────────────────────
#
# SDK: Docker  |  Hardware: T4 small (free)  |  Port: 7860
#
# Build stages:
#   1. frontend  — npm install + vite build → static/
#   2. runtime   — Python deps, pre-downloaded models, FastAPI server

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 1: Build the React frontend
# ═══════════════════════════════════════════════════════════════════════════════
FROM node:20-slim AS frontend

WORKDIR /repo

# Copy what Vite needs — preserving directory structure so the
# ../../../../media/logo.png import in App.jsx resolves correctly.
COPY src/frontend/web/package.json src/frontend/web/package-lock.json* src/frontend/web/
COPY src/frontend/web/vite.config.mjs src/frontend/web/
COPY src/frontend/web/index.html src/frontend/web/
COPY src/frontend/web/.env.production src/frontend/web/
COPY src/frontend/web/src/ src/frontend/web/src/
COPY media/ media/

WORKDIR /repo/src/frontend/web
RUN npm install && npx vite build
# Output: /repo/src/frontend/web/dist/

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2: Python runtime with CUDA
# ═══════════════════════════════════════════════════════════════════════════════
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/data/hf_cache \
    TRANSFORMERS_CACHE=/data/hf_cache \
    HF_DATASETS_CACHE=/data/hf_cache/datasets

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev git curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# ── Python dependencies ──────────────────────────────────────────────────────
COPY spaces/requirements.txt .

# Install llama-cpp-python from prebuilt CUDA 12.4 wheel, then the rest
RUN pip install --no-cache-dir --prefer-binary \
        llama-cpp-python \
        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 \
    && pip install --no-cache-dir -r requirements.txt

# ── Application code ─────────────────────────────────────────────────────────
COPY spaces/app.py .

# ── Built frontend ───────────────────────────────────────────────────────────
COPY --from=frontend /repo/src/frontend/web/dist/ /app/static/

# ── Create non-root user (HF Spaces expects uid 1000) ───────────────────────
RUN useradd -m -u 1000 appuser \
    && mkdir -p /data/hf_cache \
    && chown -R appuser:appuser /app /data

# ── Pre-download models & VDB (baked into image for fast cold starts) ────────
ARG HF_TOKEN=""
ENV HF_TOKEN=${HF_TOKEN}

USER appuser

RUN python -c "\
from huggingface_hub import hf_hub_download, snapshot_download; \
print('Downloading VDB...'); \
snapshot_download(repo_id='KeeganCarey/mcam-vdb', repo_type='dataset'); \
print('Downloading reranker GGUF...'); \
hf_hub_download(repo_id='mradermacher/Qwen3-VL-Reranker-2B-i1-GGUF', filename='Qwen3-VL-Reranker-2B.i1-Q6_K.gguf'); \
hf_hub_download(repo_id='mradermacher/Qwen3-VL-Reranker-2B-GGUF', filename='Qwen3-VL-Reranker-2B.mmproj-Q8_0.gguf'); \
print('Downloading Qwen3-VL-Embedding-2B...'); \
hf_hub_download(repo_id='Qwen/Qwen3-VL-Embedding-2B', filename='scripts/qwen3_vl_embedding.py'); \
print('Pre-download complete.'); \
"

EXPOSE 7860
CMD ["python", "app.py"]
