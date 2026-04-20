#!/usr/bin/env python3
"""
Tiny wrapper script for the semantic deduplication pipeline.

The real implementation lives in `semantic_dedup_core.py`.
This file exists so users have a clean executable entrypoint and so the core
logic can stay importable for testing.
"""

try:
    from .semantic_dedup_core import main
except ImportError:
    from semantic_dedup_core import main


if __name__ == "__main__":
    main()
