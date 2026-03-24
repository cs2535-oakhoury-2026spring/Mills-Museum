import unittest

import numpy as np
import pandas as pd

from src.pipeline.filtration.semantic_dedup_core import (
    LANG_NULL_TOKEN,
    choose_canonical_label,
    normalized_token_entropy,
    normalize_language,
    pick_best_row_for_label,
    semantic_collision_rate,
)

try:
    import faiss  # noqa: F401

    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class SemanticDedupCoreTest(unittest.TestCase):
    def test_normalize_language_treats_null_as_own_group(self) -> None:
        series = pd.Series(["70051", None, "70051", pd.NA, "12345"])
        got = normalize_language(series)
        self.assertEqual(got.tolist(), ["70051", LANG_NULL_TOKEN, "70051", LANG_NULL_TOKEN, "12345"])

    def test_choose_canonical_prefers_note_then_shortest_then_alpha(self) -> None:
        members = ["alpha extended", "alpha", "beta"]
        has_note_lookup = {
            ("70051", "alpha extended"): False,
            ("70051", "alpha"): True,
            ("70051", "beta"): True,
        }
        got = choose_canonical_label("70051", members, has_note_lookup)
        self.assertEqual(got, "beta")

    def test_choose_canonical_alpha_tiebreak(self) -> None:
        members = ["zeta", "beta"]
        has_note_lookup = {
            ("70051", "zeta"): True,
            ("70051", "beta"): True,
        }
        got = choose_canonical_label("70051", members, has_note_lookup)
        self.assertEqual(got, "beta")

    def test_pick_best_row_for_label_prefers_note_then_smallest_term_id(self) -> None:
        group = pd.DataFrame(
            [
                {"term_id": "3003", "term_note": None},
                {"term_id": "3002", "term_note": "has note"},
                {"term_id": "3001", "term_note": "has note"},
            ]
        )
        best = pick_best_row_for_label(group)
        self.assertEqual(best["term_id"], "3001")
        self.assertEqual(best["term_note"], "has note")

    def test_normalized_token_entropy_is_bounded(self) -> None:
        labels = ["oil painting", "oil portrait", "hand knife"]
        entropy, vocab_size, token_count = normalized_token_entropy(labels)
        self.assertGreaterEqual(entropy, 0.0)
        self.assertLessEqual(entropy, 1.0)
        self.assertEqual(vocab_size, 5)
        self.assertEqual(token_count, 6)

    def test_normalized_token_entropy_single_token_stream(self) -> None:
        labels = ["x", "x", "x"]
        entropy, vocab_size, token_count = normalized_token_entropy(labels)
        self.assertEqual(entropy, 0.0)
        self.assertEqual(vocab_size, 1)
        self.assertEqual(token_count, 3)

    @unittest.skipUnless(HAS_FAISS, "faiss-cpu not installed")
    def test_semantic_collision_rate_drops_after_merging_near_duplicates(self) -> None:
        labels = ["a", "b", "c"]
        label_to_idx = {label: i for i, label in enumerate(labels)}
        embeddings = np.array(
            [
                [1.0, 0.0],   # a
                [0.99, 0.01], # b, very close to a
                [0.0, 1.0],   # c
            ],
            dtype=np.float32,
        )
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        before = {"70051": ["a", "b", "c"]}
        after = {"70051": ["a", "c"]}

        before_rate, _ = semantic_collision_rate(
            labels_by_language=before,
            label_to_global_index=label_to_idx,
            embeddings=embeddings,
            threshold=0.95,
        )
        after_rate, _ = semantic_collision_rate(
            labels_by_language=after,
            label_to_global_index=label_to_idx,
            embeddings=embeddings,
            threshold=0.95,
        )
        self.assertGreater(before_rate, after_rate)


if __name__ == "__main__":
    unittest.main()
