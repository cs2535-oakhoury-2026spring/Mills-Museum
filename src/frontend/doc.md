# Frontend Guide

This directory contains every user-facing experience in the repository. The important thing to understand is that there is not just one frontend here. There are three related but separate interfaces:

1. A Gradio keyword-review app in Python.
2. A React/Vite keyword-review app for the browser.
3. A Gradio data exhibit focused on the AAT dataset rather than image tagging.

## Main Python files

### `gradio.py`

This is the Python-side keyword generation and review interface.

What it does:

- Lets staff upload one or more artwork images.
- Optionally accepts title and medium text.
- Calls the retrieval and reranking pipeline for each image.
- Displays the current keyword set for review.
- Lets the reviewer uncheck weak terms.
- Regenerates only the removed slots from the unused candidate pool.
- Exports selected results as CSV.

Important architectural idea:

- This file is mostly UI orchestration.
- It does not define the machine-learning models itself.
- The runtime expects the embedding model, reranking model, and vector collection to be initialized elsewhere and registered through `configure_backend_runtime(...)`.

### `keyword_feedback.py`

This file contains the small state-management rules used by the Gradio review workflow.

It answers questions like:

- Which terms are currently visible?
- Which ones has the user selected?
- Which ones have already been rejected?
- Which replacement terms are still allowed to appear?

This file is important because it keeps the review behavior predictable. Once a user rejects a keyword, the regeneration logic is designed not to show that same rejected term again for the same image.

### `CHANGELOG.md`

Team-local notes for frontend changes. It is useful historical context, but not the runtime source of truth.

## Subdirectories

### `web/`

This is the React/Vite browser application.

Main structure:

- `web/package.json`: local frontend scripts and dependencies.
- `web/src/App.jsx`: top-level application state and flow control.
- `web/src/components/`: upload, processing, review, result, and modal UI pieces.
- `web/src/utils/`: keyword adapters, export helpers, and shared style helpers.
- `web/src/styles/`: theme and CSS files.
- `web/public/`: static public assets.

How it works:

- The app moves through upload, processing, and review phases.
- Each uploaded file is sent to `POST {VITE_API_URL}/predict`.
- Backend responses are converted into UI-friendly keyword objects.
- Reviewers can include or exclude keywords, search within a result, copy them, and export them.

Important detail:

- This is a separate implementation from `gradio.py`.
- It solves a similar product problem, but through a JavaScript browser frontend rather than a Python Gradio app.

### `data_viz/`

This folder contains the Gradio data exhibit.

Main file:

- `data_story_exhibit.py`

What it does:

- Loads the museum-focused AAT parquet dataset.
- Computes chart data and descriptive summary sections.
- Builds a Gradio experience that feels more like an exhibit than a plain admin screen.

This is not the artwork keyword-review tool. It is the analysis/exhibit presentation layer.

### `design/`

This folder stores design references and source materials, including Figma-related files and the `mills.jpg` image used by the exhibit.

This area is mostly visual reference material, not core logic.

### `notebooks/`

This folder contains exploratory notebooks used during development, prototyping, or demonstrations.

These notebooks are useful context, but they are not the primary runtime codepath.

## How the frontend pieces fit together

### Gradio keyword workflow

- `gradio.py` builds the interface.
- `keyword_feedback.py` manages keyword review state.
- Backend model objects are injected from outside the file.

### React keyword workflow

- `web/src/App.jsx` owns the batch state.
- Child components in `web/src/components/` render each phase of the workflow.
- Utility helpers in `web/src/utils/` keep export formatting and API adaptation consistent.

### Data exhibit workflow

- `data_viz/data_story_exhibit.py` loads the analysis dataset and presents it interactively.

## Good places to start depending on the task

- Want to change the Python keyword-review flow: start with `gradio.py`.
- Want to change selection/regeneration behavior: start with `keyword_feedback.py`.
- Want to change the browser-based UI: start with `web/src/App.jsx` and `web/src/components/`.
- Want to change chart storytelling or exhibit presentation: start with `data_viz/data_story_exhibit.py`.
