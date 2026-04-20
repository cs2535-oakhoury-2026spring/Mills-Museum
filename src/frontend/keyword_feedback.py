"""
Keyword selection and rejection logic for the MCAM review workflow.

Each processed image carries an ImageKeywordState dict that tracks:
  - candidate_terms:  the full ranked pool returned by retrieval + reranking
  - visible_terms:    the subset currently shown in the UI checkboxes
  - selected_terms:   which visible terms the user has accepted (checked)
  - rejected_terms:   terms the user has explicitly rejected (unchecked then regenerated)
  - displayed_terms:  every term that has ever appeared in the UI (prevents re-showing)
  - target_count:     how many keywords we aim to keep

When the user unchecks terms and clicks "Regenerate", the rejected slots are
filled from the unused tail of candidate_terms, skipping anything already
shown or rejected.
"""
from __future__ import annotations

from typing import Any

# Type aliases for readability -- both are plain dicts in practice.
KeywordCandidate = dict[str, Any]
ImageKeywordState = dict[str, Any]


def candidate_key(candidate: KeywordCandidate) -> str:
    """Derive a stable unique key for a candidate, preferring term_id over label."""
    term_id = candidate.get("term_id")
    label = candidate.get("label", "")
    return str(term_id or label)


def dedupe_candidates(candidates: list[KeywordCandidate]) -> list[KeywordCandidate]:
    """Remove duplicate terms while keeping the first ranked copy of each one."""
    deduped: list[KeywordCandidate] = []
    seen: set[str] = set()

    for candidate in candidates:
        key = candidate_key(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            {
                "key": key,
                "label": candidate["label"],
                "score": float(candidate["score"]),
                "term_id": candidate.get("term_id"),
            }
        )

    return deduped


def initialize_image_result(
    image: Any,
    candidates: list[KeywordCandidate],
    target_count: int,
) -> ImageKeywordState:
    """Build the initial state dict for one image after retrieval+reranking."""
    ranked_candidates = dedupe_candidates(candidates)
    # Show only the first `target_count` terms up front. The remainder stays in
    # reserve so the user can reject terms and ask for replacements later.
    visible_terms = [candidate["key"] for candidate in ranked_candidates[:target_count]]
    adjusted_target_count = min(target_count, len(visible_terms))

    return {
        "image": image,
        "candidate_terms": ranked_candidates,
        "visible_terms": visible_terms,
        "selected_terms": visible_terms.copy(),
        "rejected_terms": [],
        "displayed_terms": visible_terms.copy(),
        "target_count": adjusted_target_count,
    }


def sync_selected_terms(
    result: ImageKeywordState,
    selected_terms: list[str] | None,
) -> ImageKeywordState:
    """Update the result to reflect the user's current checkbox selections."""
    # Only terms currently visible in the UI are allowed to remain selected.
    visible_terms = result.get("visible_terms", [])
    selected_set = set(selected_terms or [])
    result["selected_terms"] = [
        term_key for term_key in visible_terms if term_key in selected_set
    ]
    return result


def regenerate_removed_terms(
    result: ImageKeywordState,
) -> tuple[ImageKeywordState, int, int]:
    """
    Replace unchecked (rejected) terms with the next-best unused candidates.

    Returns (updated_result, removed_count, replacement_count).
    replacement_count may be less than removed_count if the candidate pool is exhausted.
    """
    visible_terms = result.get("visible_terms", [])
    selected_terms = result.get("selected_terms", [])
    target_count = result.get("target_count", len(visible_terms))

    # Split the current visible list into kept terms and explicitly removed terms.
    # The removed terms become ineligible for future regeneration results.
    selected_set = set(selected_terms)
    kept_terms = [term_key for term_key in visible_terms if term_key in selected_set]
    removed_terms = [term_key for term_key in visible_terms if term_key not in selected_set]
    needed_replacements = max(target_count - len(kept_terms), 0)

    rejected_terms = set(result.get("rejected_terms", []))
    rejected_terms.update(removed_terms)
    displayed_terms = set(result.get("displayed_terms", []))

    # Block anything already kept, rejected, or previously shown from being reused
    blocked_terms = set(kept_terms) | rejected_terms | displayed_terms
    replacement_terms: list[str] = []

    for candidate in result.get("candidate_terms", []):
        term_key = candidate["key"]
        if term_key in blocked_terms:
            continue
        replacement_terms.append(term_key)
        blocked_terms.add(term_key)
        if len(replacement_terms) >= needed_replacements:
            break

    # Merge kept terms with fresh replacements; auto-select all of them
    result["visible_terms"] = kept_terms + replacement_terms
    result["selected_terms"] = result["visible_terms"].copy()
    result["rejected_terms"] = list(rejected_terms)
    result["displayed_terms"] = list(displayed_terms | set(replacement_terms))

    return result, len(removed_terms), len(replacement_terms)


def candidate_lookup(result: ImageKeywordState) -> dict[str, KeywordCandidate]:
    """Build a key -> candidate dict for fast lookup during rendering."""
    return {
        candidate["key"]: candidate for candidate in result.get("candidate_terms", [])
    }


def export_labels(result: ImageKeywordState) -> list[str]:
    """Return human-readable labels for all currently selected terms."""
    candidates_by_key = candidate_lookup(result)
    selected_keys = set(result.get("selected_terms", []))
    labels: list[str] = []

    for term_key in result.get("visible_terms", []):
        if term_key not in selected_keys:
            continue
        candidate = candidates_by_key.get(term_key)
        if candidate is None:
            continue
        labels.append(candidate["label"])

    return labels
