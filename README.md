# Mills Museum — MCAM Keyword Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5-646cff?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-38bdf8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

**Mills College Art Museum** tooling to suggest **Art & Architecture Thesaurus (AAT)** keywords from artwork images, review them in the browser, and export for cataloging (including CSV workflows for **EmbARK**).

| Audience | Start here |
|----------|------------|
| **Developers** | [**Technical handover →**](docs/technical-handover.md) |
| **Museum staff** | [**User guide →**](docs/mcam-keyword-generator-user-guide.md) |

---

<!-- Replace with a real screenshot when available -->
![MCAM Keyword Generator — screenshot placeholder](https://via.placeholder.com/960x540/1e2a44/d8e4f5?text=MCAM+Keyword+Generator+%28add+screenshot+to+docs%2F%29)

---

## Quick start (frontend)

```bash
git clone https://github.com/cs2535-oakhoury-2026spring/Mills-Museum.git
cd Mills-Museum/src/frontend/web
npm install
cp .env.example .env.local  # optional: create .env.local — see handover
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). Point **`VITE_API_URL`** in **`.env.local`** at your running Colab/ngrok backend so uploads and `/facets` work. Full setup, proxy notes, and **`npm run build`** / **`dist/`** workflow are in the [**technical handover**](docs/technical-handover.md).

From the **repository root** you can also run:

```bash
npm install
npm run dev
```

(Uses `--prefix src/frontend/web` — see root `package.json`.)

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| **UI** | React 18, Vite 5, Tailwind CSS v4, Motion, Lucide React |
| **Inference & API** | FastAPI, uvicorn, ChromaDB, LangChain (`langchain-chroma`), Hugging Face Hub |
| **Hosting / demo** | Google Colab, ngrok |
| **Legacy / alt UI** | Gradio (`src/frontend/gradio.py`) |

---

## Repository map

```
Mills-Museum/
├── colab/                 # mcam_server.ipynb — full stack + tunnel
├── docs/                  # Staff user guide + technical handover
├── media/                 # Logo (imported by Vite from repo root)
├── scripts/               # HF uploads, data pipeline
├── src/
│   ├── analysis/          # Dashboards, parquet, figures
│   └── frontend/
│       ├── web/           # ★ Main React + Vite app
│       └── …              # Gradio, Python helpers, design assets
├── README.md
└── LICENSE
```

---

## Documentation

- **[`docs/technical-handover.md`](docs/technical-handover.md)** — Onboarding: repo layout, local vs Colab, `dist/` policy, file-by-file frontend guide.
- **[`docs/mcam-keyword-generator-user-guide.md`](docs/mcam-keyword-generator-user-guide.md)** — End-user steps (non-technical).


<details>
  <summary>Architecture Diagram</summary>
  
  ```mermaid
  ---


config:
  theme: base
  themeVariables:
    primaryColor: '#DCE4F5'
    primaryBorderColor: '#3B528B'
    primaryTextColor: '#1E2332'
    secondaryColor: '#F8F9FC'
    secondaryBorderColor: '#D2D7E4'
    secondaryTextColor: '#646D7D'
    tertiaryColor: '#FFFFFF'
    lineColor: '#9BA3B8'
    fontFamily: ''
    fontSize: 14px
    clusterBkg: '#F8F9FC'
    clusterBorder: '#D2D7E4'
  flowchart:
    curve: basis
    padding: 16
    nodeSpacing: 40
    rankSpacing: 55
title: MCAM Keyword Pipeline — AI Architecture
---
flowchart TB
 subgraph PERCEPTION["fa:fa-eye Perception"]
        CAPTIONER["fa:fa-comment-dots <b>Artwork captioner</b><br>Generates natural-language description<br>subject, medium, colors, technique, etc<br><br><i>LLaVA v1.6 Mistral 7B · Q4_K_M</i>"]
        IMG_EMBED["fa:fa-cube <b>Image embedder</b><br>Encodes image into same<br>vector space as AAT terms<br><br><i>ViT-SO400M-14-SigLIP-384</i>"]
        TXT_EMBED["fa:fa-cube <b>Text embedder</b><br>Encodes caption into same<br>vector space as AAT terms<br><br><i>ViT-SO400M-14-SigLIP-384</i>"]
        TXT_VEC[/"fa:fa-braille <b>Text vector</b><br><code>[0.67, 0.03, −0.55, …]</code>"/]
        IMG_VEC[/"fa:fa-braille <b>Image vector</b><br><code>[0.42, −0.18, 0.91, …]</code>"/]
  end
 subgraph RETRIEVAL["fa:fa-search Retrieval"]
        FUSION{{"fa:fa-code-branch <b>Dual-query fusion</b><br>query_bias splits retrieval out of total keywords<br><br>pure image vs pure text <br>0.0 - 1.0<br><br><i>defaults to 0.5<br>(half from each embedding)</i>"}}
        MMR["fa:fa-random <b>MMR search</b><br>Maximal Marginal Relevance<br>k × 4 candidates for diversity<br><br><i>λ controls relevance vs. diversity</i>"]
        CHROMADB[("fa:fa-database <b>ChromaDB</b><br>19.9k pre-computed AAT embeddings<br>Cosine · HNSW index")]
        DEDUP["fa:fa-filter <b>Deduplicate + merge</b><br>Combine image &amp; text results<br>Remove duplicate terms"]
  end
 subgraph OFFLINE["fa:fa-cogs Offline — AAT Embedding Pipeline (setup once)"]
        AAT_RAW["fa:fa-globe <b>Getty AAT</b><br>Art &amp; Architecture Thesaurus<br>relational database<br><br><i>482k terms from vocab.getty.edu</i>"]
        AAT_FILTER["fa:fa-cut <b>Selective filtering</b><br>Remove:<br>Irrelevant facets<br>Deeply nested terms<br>Non-english terms<br>Terms without scope note<br>etc<br><br><i>482k → 19.9k terms</i>"]
        AAT_SRC["fa:fa-book <b>Filtered AAT dataset</b><br>19.9k curated art terms<br>with scope notes + hierarchies + facets<br><br><i>KeeganCarey/aat-selectively-filtered</i>"]
        EMBED_NB@{ label: "fa:fa-flask <b style=\"color:\">Embedding notebook</b><br>Batch-embeds all terms<br>with scope notes + hierarchy context<br>into vector database<br><br><i>embed_aat_keywords.ipynb<br>ViT-SO400M-14-SigLIP-384</i>" }
        HF_UPLOAD[("fa:fa-cloud-upload <b>Upload to HuggingFace</b><br>Persistent ChromaDB pushed via<br>hf_api.upload_folder<br><br><i>KeeganCarey/mcam-vdb</i>")]
  end
 subgraph SCORING["fa:fa-sort-amount-down Scoring"]
        CANDIDATES(["fa:fa-tags <b>Candidate AAT terms</b><br>Oversampled diverse matches from<br>vector similarity"])
        RERANKER["fa:fa-balance-scale <b>Vision reranker</b><br>Each candidate is scored against original artwork via vision-language classifier head → 0–100% confidence<br><br><i>Qwen3-VL-Reranker-2B</i><br>"]
        RANKED(["fa:fa-list-ol <b>Ranked keywords</b><br>Sorted by confidence %<br>Progressively updated in real time"])
  end
 subgraph OUTPUT_SEC["fa:fa-check-circle Output"]
        REVIEW["fa:fa-user-check <b>Human review</b><br>Museum staff accept or reject AI-suggested keywords<br><br>Final Keyword selection is exported as a csv<br><br><i>React frontend · SSE streaming</i>"]
  end
    CAPTIONER -- description text --> TXT_EMBED
    TXT_EMBED --> TXT_VEC
    IMG_EMBED --> IMG_VEC
    FUSION --> MMR
    MMR --> CHROMADB
    CHROMADB --> DEDUP
    CANDIDATES --> RERANKER
    RERANKER --> RANKED
    ARTWORK(["fa:fa-image <b>Artwork image</b><br>Museum artwork + Generation Settings"]) -- image --> CAPTIONER & IMG_EMBED
    TXT_VEC --> FUSION
    IMG_VEC --> FUSION
    DEDUP -- "oil painting · portrait · vase" --> CANDIDATES
    ARTWORK -. image .-> RERANKER
    CANDIDATES -. initial keywords (unscored)<br>displayed immediately .-> REVIEW
    RANKED -- "scores backfilled progressively<br>94.2% · 87.1% · 72.8% …" --> REVIEW
    AAT_SRC -- "19.9k terms + scope notes" --> EMBED_NB
    EMBED_NB -- populated vector database --> HF_UPLOAD
    HF_UPLOAD -. "download pre-embedded<br>vector database on startup" .-> CHROMADB
    AAT_RAW -- full relational DB export --> AAT_FILTER
    AAT_FILTER -- "19.9k curated terms" --> AAT_SRC

    EMBED_NB@{ shape: rect}
     CAPTIONER:::pink
     IMG_EMBED:::purple
     TXT_EMBED:::purple
     TXT_VEC:::vec
     IMG_VEC:::vec
     FUSION:::purple
     MMR:::teal
     CHROMADB:::db
     DEDUP:::teal
     AAT_RAW:::muted
     AAT_FILTER:::coral
     AAT_SRC:::muted
     EMBED_NB:::purple
     HF_UPLOAD:::muted
     CANDIDATES:::teal
     RERANKER:::coral
     RANKED:::coral
     REVIEW:::green
     ARTWORK:::input
    classDef input fill:#FFF7DC,stroke:#B48214,stroke-width:2px,color:#6B4D0A
    classDef pink fill:#FCE8F1,stroke:#C24178,stroke-width:2px,color:#7A1A42
    classDef purple fill:#EDE6FC,stroke:#6D4AB9,stroke-width:2px,color:#3E2470
    classDef teal fill:#DCF5F0,stroke:#148C78,stroke-width:2px,color:#0A5C4E
    classDef coral fill:#FFEEDC,stroke:#D26923,stroke-width:2px,color:#7A3A0E
    classDef green fill:#E1F8E6,stroke:#288C46,stroke-width:2px,color:#165C28
    classDef muted fill:#EEEFF4,stroke:#828B9B,stroke-width:2px,color:#4A5060
    classDef db fill:#DCF5F0,stroke:#148C78,stroke-width:3px,color:#0A5C4E
    classDef vec fill:#F5F0FF,stroke:#6D4AB9,stroke-width:1.5px,color:#3E2470
    linkStyle 0 stroke:#C24178,stroke-width:2px,fill:none
    linkStyle 1 stroke:#6D4AB9,stroke-width:2px,fill:none
    linkStyle 2 stroke:#6D4AB9,stroke-width:2px,fill:none
    linkStyle 3 stroke:#148C78,stroke-width:2px,fill:none
    linkStyle 4 stroke:#148C78,stroke-width:2px,fill:none
    linkStyle 5 stroke:#148C78,stroke-width:2px,fill:none
    linkStyle 6 stroke:#D26923,stroke-width:2px,fill:none
    linkStyle 7 stroke:#D26923,stroke-width:2px,fill:none
    linkStyle 8 stroke:#C24178,stroke-width:2px,fill:none
    linkStyle 9 stroke:#6D4AB9,stroke-width:2px,fill:none
    linkStyle 10 stroke:#6D4AB9,stroke-width:2px,fill:none
    linkStyle 11 stroke:#6D4AB9,stroke-width:2px,fill:none
    linkStyle 12 stroke:#148C78,stroke-width:2px,fill:none
    linkStyle 13 stroke:#D26923,stroke-width:2px,fill:none
    linkStyle 14 stroke:#148C78,stroke-width:1.5px,fill:none
    linkStyle 15 stroke:#288C46,stroke-width:2px,fill:none
    linkStyle 16 stroke:#828B9B,stroke-width:2px,fill:none
    linkStyle 17 stroke:#6D4AB9,stroke-width:2px,fill:none
    linkStyle 18 stroke:#828B9B,stroke-width:1.5px,fill:none
    linkStyle 19 stroke:#828B9B,stroke-width:2px,fill:none
    linkStyle 20 stroke:#D26923,stroke-width:2px,fill:none
  ```
</details>

---

## Credits

Course project repository **cs2535-oakhoury-2026spring** — Mills College Art Museum keyword pipeline. See [`LICENSE`](LICENSE) (MIT, © 2026 cs2535-oakhoury-2026spring).

---

## License

[MIT](LICENSE)
