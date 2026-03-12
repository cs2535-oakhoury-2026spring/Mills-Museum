import unittest

from src.frontend.keyword_feedback import (
    export_labels,
    initialize_image_result,
    regenerate_removed_terms,
    sync_selected_terms,
)


class KeywordFeedbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = [
            {"label": "portrait", "score": 0.99, "term_id": "1"},
            {"label": "oil painting", "score": 0.96, "term_id": "2"},
            {"label": "frame", "score": 0.92, "term_id": "3"},
            {"label": "canvas", "score": 0.89, "term_id": "4"},
            {"label": "museum object", "score": 0.82, "term_id": "5"},
        ]

    def test_initialize_sets_visible_and_selected_terms(self) -> None:
        result = initialize_image_result("image", self.candidates, target_count=3)
        self.assertEqual(result["target_count"], 3)
        self.assertEqual(result["visible_terms"], ["1", "2", "3"])
        self.assertEqual(result["selected_terms"], ["1", "2", "3"])

    def test_regenerate_replaces_exact_number_removed(self) -> None:
        result = initialize_image_result("image", self.candidates, target_count=3)
        sync_selected_terms(result, ["1"])

        result, removed_count, replacement_count = regenerate_removed_terms(result)

        self.assertEqual(removed_count, 2)
        self.assertEqual(replacement_count, 2)
        self.assertEqual(result["visible_terms"], ["1", "4", "5"])
        self.assertEqual(result["selected_terms"], ["1", "4", "5"])
        self.assertEqual(set(result["rejected_terms"]), {"2", "3"})

    def test_regenerate_does_not_reintroduce_rejected_terms(self) -> None:
        result = initialize_image_result("image", self.candidates, target_count=3)
        sync_selected_terms(result, ["1", "2"])
        result, _, _ = regenerate_removed_terms(result)

        sync_selected_terms(result, ["1"])
        result, _, _ = regenerate_removed_terms(result)

        for rejected_term in result["rejected_terms"]:
            self.assertNotIn(rejected_term, result["visible_terms"])

    def test_export_labels_only_returns_currently_selected_terms(self) -> None:
        result = initialize_image_result("image", self.candidates, target_count=3)
        sync_selected_terms(result, ["1", "3"])
        self.assertEqual(export_labels(result), ["portrait", "frame"])


if __name__ == "__main__":
    unittest.main()
