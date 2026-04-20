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

---

## Credits

Course project repository **cs2535-oakhoury-2026spring** — Mills College Art Museum keyword pipeline. See [`LICENSE`](LICENSE) (MIT, © 2026 cs2535-oakhoury-2026spring).

---

## License

[MIT](LICENSE)
