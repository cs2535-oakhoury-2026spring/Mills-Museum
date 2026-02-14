# Changelog

[!NOTE] Please make sure to include what changed as you make commits. This is so we can keep track, commit messages are not
that in-depth.


## v1 - Feb 14, 2026
On Feb 14, 2026, the project was reorganized to support a cleaner filtration workflow: the semantic dedup pipeline was split into two files (`filtration/semantic_dedup_core.py` for logic and `filtration/semantic_dedup_pipeline.py` as the runner), the original parquet was moved and renamed to `data/data.parquet`, generated parquet/csv artifacts were removed from `filtration/`, core tests were added under `tests/filtration_test`, and GitHub Actions automation was added in `.github/workflows/filtration-tests.yml` to run the filtration tests on every push using CPU-compatible dependencies (including `faiss-cpu`).
