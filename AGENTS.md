# Repository Guidelines

## Project Overview
- This repository contains a Python-based museum keywording project with two main areas:
  - `src/frontend/`: Gradio UI and reviewer feedback flows.
  - `src/analysis/` and `src/hf_upload_scripts/`: data analysis notebooks/scripts and dataset publishing utilities.
- Tests currently live under `tests/frontend_test/` and `tests/filtration_test/`.

## Working Style
- Make focused, minimal changes that match the existing code style.
- Prefer fixing the root cause instead of layering workarounds.
- Avoid changing generated outputs, large datasets, media assets, or analysis artifacts unless the task explicitly requires it.
- Read large files in chunks.

## Python Conventions
- Target Python `3.12+` as declared in `pyproject.toml`.
- Preserve existing type hint style, `pathlib.Path` usage, and small helper-oriented functions.
- Keep imports grouped in the current repository style.
- Do not add inline comments unless the user asks for them.

## Testing
- Use `pytest` for validation.
- Start with the smallest relevant test target, then broaden only if needed.
- Common targeted commands:
  - `python -m pytest tests/frontend_test/test_keyword_feedback.py -q`
  - `python -m pytest tests/filtration_test/test_semantic_dedup_core.py -q`
  - `python -m pytest -q`

## Frontend Notes
- The UI entrypoint is `src/frontend/gradio.py`.
- Backend runtime objects are expected to be configured externally before launching the Gradio UI.
- When editing frontend flows, preserve the current state-driven review workflow and export behavior.

## Data and Analysis Notes
- Treat `data/`, `media/`, and `AAT_terms/` as project assets; do not reorganize or mass-edit them unless required.
- Analysis scripts under `src/analysis/` may produce derived outputs; keep incidental output files out of version control.

## Dependency Notes
- Primary dependency declarations are split across `pyproject.toml` and `requirements.txt`.
- If a task depends on running the app or tests, verify the needed packages are available in the active environment before finishing.

## Tooling
- Prefer `rg` / `rg --files` for search.
- Prefer `apply_patch` for edits.
- Do not create commits or branches unless the user asks.
