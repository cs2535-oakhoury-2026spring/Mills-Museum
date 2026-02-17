#!/usr/bin/env python3
"""CLI entrypoint for semantic dedup pipeline."""

try:
    from .semantic_dedup_core import main
except ImportError:
    from semantic_dedup_core import main


if __name__ == "__main__":
    main()
