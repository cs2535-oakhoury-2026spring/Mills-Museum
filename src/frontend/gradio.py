from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import tempfile

import gradio as gr
import torch
from PIL import Image

from src.frontend.keyword_feedback import (
    candidate_lookup,
    export_labels,
    initialize_image_result,
    regenerate_removed_terms,
    sync_selected_terms,
)


DEFAULT_KEYWORD_COUNT = 10
DEFAULT_CANDIDATE_POOL_SIZE = 40
REPO_DEMO_IMAGES: list[str] = []
EXPORT_DIR: str | None = None


def empty_app_state() -> dict:
    return {"all_results": {}, "current_index": 0}


def configure_backend_runtime(collection, embedding_model, reranking_model):
    globals()["collection"] = collection
    globals()["embedding_model"] = embedding_model
    globals()["reranking_model"] = reranking_model


def configure_demo_assets(
    image_paths: list[str] | None = None,
    export_dir: str | None = None,
):
    normalized_images = []
    for image_path in image_paths or []:
        resolved = str(Path(image_path).expanduser().resolve())
        if Path(resolved).exists():
            normalized_images.append(resolved)
    globals()["REPO_DEMO_IMAGES"] = normalized_images

    if export_dir:
        export_path = Path(export_dir).expanduser().resolve()
        export_path.mkdir(parents=True, exist_ok=True)
        globals()["EXPORT_DIR"] = str(export_path)


def get_backend_runtime():
    missing = [
        name
        for name in ("embedding_model", "reranking_model", "collection")
        if name not in globals()
    ]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            "Missing backend runtime objects: "
            f"{joined}. Launch this UI from the notebook/runtime where the "
            "Qwen models and Chroma collection have already been initialized."
        )
    return globals()["embedding_model"], globals()["reranking_model"], globals()["collection"]


def preview_image(files, index):
    if not files:
        return None, "No images selected"
    index = max(0, min(index, len(files) - 1))
    return Image.open(files[index]), f"Preview {index + 1} of {len(files)}"


def preview_next(files, index):
    index = min(index + 1, len(files) - 1) if files else 0
    img, counter = preview_image(files, index)
    return img, counter, index


def preview_prev(files, index):
    index = max(index - 1, 0) if files else 0
    img, counter = preview_image(files, index)
    return img, counter, index


def on_upload(files):
    if not files:
        return None, "No images selected", 0
    img, counter = preview_image(files, 0)
    return img, counter, 0


def default_repo_files():
    return REPO_DEMO_IMAGES.copy() or None


def initialize_upload_defaults():
    files = default_repo_files()
    if not files:
        return None, None, "No images selected", 0, "Upload images to start."

    image, counter = preview_image(files, 0)
    return (
        files,
        image,
        counter,
        0,
        f"Loaded {len(files)} repository demo image(s). Click Generate Keywords to run the model.",
    )


def build_keyword_choices(result):
    candidates_by_key = candidate_lookup(result)
    choices: list[tuple[str, str]] = []

    for term_key in result.get("visible_terms", []):
        candidate = candidates_by_key.get(term_key)
        if candidate is None:
            continue
        display = f"{candidate['label']}  |  {candidate['score'] * 100:.1f}% match"
        choices.append((display, term_key))

    return choices, result.get("selected_terms", []).copy()


def build_review_summary(result):
    visible_count = len(result.get("visible_terms", []))
    selected_count = len(result.get("selected_terms", []))
    rejected_count = len(result.get("rejected_terms", []))
    remaining_options = max(
        len(result.get("candidate_terms", [])) - len(result.get("displayed_terms", [])),
        0,
    )

    error_message = result.get("error")
    if error_message:
        return (
            "<div class='summary-card error-card'>"
            "<strong>Image could not be processed.</strong><br>"
            f"{error_message}"
            "</div>"
        )

    target_count = result.get("target_count", visible_count)
    pending_replacements = max(target_count - selected_count, 0)

    return (
        "<div class='summary-card'>"
        f"<div><strong>{selected_count} of {target_count}</strong> keywords currently selected</div>"
        f"<div>{pending_replacements} marked for replacement, "
        f"{rejected_count} rejected so far, {remaining_options} unused alternatives left in the ranked pool</div>"
        "</div>"
    )


def build_action_feedback(message, kind="info"):
    if not message:
        message = "Review the suggestions, uncheck any weak matches, then regenerate to fill the open slots."
    return f"<div class='feedback-card {kind}-card'>{message}</div>"


def build_art_query(image):
    return {"image": image, "text": ""}


def generate_ranked_candidates(
    image,
    target_count=DEFAULT_KEYWORD_COUNT,
    candidate_pool_size=DEFAULT_CANDIDATE_POOL_SIZE,
):
    embedding_model, reranking_model, collection = get_backend_runtime()

    art_query = build_art_query(image)
    query_input = [art_query]

    image_features = embedding_model.process(query_input)
    image_features = torch.nn.functional.normalize(image_features, p=2, dim=1)

    results = collection.query(
        query_embeddings=image_features.cpu().float().tolist(),
        n_results=max(target_count, candidate_pool_size),
    )

    labels = []
    docs = []
    term_ids = []

    if results.get("documents"):
        documents = results["documents"][0]
        raw_metadatas = results.get("metadatas") or []
        metadata_list = raw_metadatas[0] if raw_metadatas else [{} for _ in documents]
        if len(metadata_list) < len(documents):
            metadata_list = metadata_list + [{} for _ in range(len(documents) - len(metadata_list))]
        for document, metadata in zip(documents, metadata_list):
            docs.append({"text": document})
            labels.append(metadata.get("term_label", document))
            term_ids.append(metadata.get("term_id"))

    if not docs:
        return []

    rerank_inputs = {
        "instruction": (
            "Retrieve Art & Architecture Thesaurus terms relevant to the given image. "
            "Prefer specific, visually grounded labels."
        ),
        "query": art_query,
        "documents": docs,
        "fps": 1.0,
    }

    scores = reranking_model.process(rerank_inputs)
    ranked = sorted(zip(scores, labels, term_ids), reverse=True)

    return [
        {"label": label, "score": float(score), "term_id": term_id}
        for score, label, term_id in ranked
    ]


def current_result(state):
    current_index = state.get("current_index", 0)
    return state.get("all_results", {}).get(current_index)


def render_current_image(state, message=None, kind="info"):
    result = current_result(state)
    if result is None:
        return (
            None,
            "No image loaded",
            gr.update(choices=[], value=[]),
            "",
            build_action_feedback(message or "Upload images to begin.", kind),
        )

    choices, selected_values = build_keyword_choices(result)
    counter = (
        f"Artwork {state['current_index'] + 1} of {len(state['all_results'])}"
        if state.get("all_results")
        else "No image loaded"
    )
    return (
        result.get("image"),
        counter,
        gr.update(choices=choices, value=selected_values),
        build_review_summary(result),
        build_action_feedback(message or result.get("status_message"), kind),
    )


def process_multiple_images(images, state):
    state = empty_app_state()

    if not images:
        return (
            None,
            "No image loaded",
            gr.update(choices=[], value=[]),
            "",
            build_action_feedback("Select one or more artwork images to begin."),
            "",
            state,
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(value="Upload images to start.", visible=True),
        )

    processed_count = 0
    for idx, image_path in enumerate(images):
        image = None
        try:
            image = Image.open(image_path)
            ranked_candidates = generate_ranked_candidates(image)
            result = initialize_image_result(image, ranked_candidates, DEFAULT_KEYWORD_COUNT)
            result["status_message"] = (
                "Suggestions ready. Uncheck any weak keywords, then regenerate only those slots."
            )
            result["source_path"] = str(image_path)
            state["all_results"][idx] = result
            processed_count += 1
        except Exception as exc:
            state["all_results"][idx] = {
                "image": image,
                "candidate_terms": [],
                "visible_terms": [],
                "selected_terms": [],
                "rejected_terms": [],
                "displayed_terms": [],
                "target_count": 0,
                "error": str(exc),
                "status_message": "Processing failed for this image.",
                "source_path": str(image_path),
            }

    if not state["all_results"]:
        return (
            None,
            "No image loaded",
            gr.update(choices=[], value=[]),
            "",
            build_action_feedback("No images could be processed.", "error"),
            "",
            state,
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(value="Processing failed.", visible=True),
        )

    state["current_index"] = 0
    image, counter, checkbox_update, summary, feedback = render_current_image(
        state,
        f"Generated suggestions for {processed_count} image(s).",
        "success" if processed_count else "error",
    )

    return (
        image,
        counter,
        checkbox_update,
        summary,
        feedback,
        "",
        state,
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(value="Keywords generated.", visible=True),
    )


def update_selections(selected_terms, state):
    result = current_result(state)
    if result is None:
        return state, "", build_action_feedback("Upload and process images first.")

    sync_selected_terms(result, selected_terms)
    removed_count = max(result.get("target_count", 0) - len(result.get("selected_terms", [])), 0)
    if removed_count:
        message = (
            f"{removed_count} keyword(s) marked for replacement. Click Regenerate Removed Keywords to fill those slots."
        )
    else:
        message = "All current keywords are selected."

    return state, build_review_summary(result), build_action_feedback(message, "info")


def regenerate_current_image(selected_terms, state):
    result = current_result(state)
    if result is None:
        return (*render_current_image(state, "Upload and process images first.", "error"), "", state)

    sync_selected_terms(result, selected_terms)
    if len(result.get("selected_terms", [])) == len(result.get("visible_terms", [])):
        return (
            *render_current_image(
                state,
                "Uncheck one or more keywords first. The app will replace exactly the number you removed.",
            ),
            "",
            state,
        )

    result, removed_count, replacement_count = regenerate_removed_terms(result)

    if replacement_count < removed_count:
        message = (
            f"Replaced {replacement_count} of {removed_count} removed keyword(s). "
            "The candidate pool ran out of unused alternatives."
        )
        kind = "warning"
    else:
        message = (
            f"Replaced {removed_count} keyword(s) with {replacement_count} new suggestion(s)."
        )
        kind = "success"

    result["status_message"] = message
    return (*render_current_image(state, message, kind), "", state)


def next_image(state):
    if not state.get("all_results"):
        return (*render_current_image(state), state)
    state["current_index"] = min(
        state["current_index"] + 1, len(state["all_results"]) - 1
    )
    return (*render_current_image(state), state)


def previous_image(state):
    if not state.get("all_results"):
        return (*render_current_image(state), state)
    state["current_index"] = max(state["current_index"] - 1, 0)
    return (*render_current_image(state), state)


def upload_more():
    repo_files = default_repo_files()
    preview_image_value = None
    preview_counter_text = "No images selected"
    status_text_value = "Upload images to start."

    if repo_files:
        preview_image_value, preview_counter_text = preview_image(repo_files, 0)
        status_text_value = (
            f"Loaded {len(repo_files)} repository demo image(s). Click Generate Keywords to run the model."
        )

    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(value=status_text_value, visible=True),
        gr.update(value=repo_files),
        preview_image_value,
        None,
        "No image loaded",
        gr.update(choices=[], value=[]),
        "",
        build_action_feedback("Select one or more artwork images to begin."),
        "",
        gr.update(value=None, visible=False),
        empty_app_state(),
        preview_counter_text,
        0,
    )


def export_results(state):
    if not state.get("all_results"):
        return "No processed results to export yet.", None, build_action_feedback(
            "Generate keywords before exporting.", "warning"
        )

    output = []
    csv_rows = []
    for idx in sorted(state["all_results"].keys()):
        result = state["all_results"][idx]
        labels = export_labels(result)
        output.append(f"Image {idx + 1}: {', '.join(labels) if labels else 'No selected keywords'}")
        candidate_by_key = candidate_lookup(result)
        selected_keys = set(result.get("selected_terms", []))
        for term_key in result.get("visible_terms", []):
            if term_key not in selected_keys:
                continue
            candidate = candidate_by_key.get(term_key)
            if candidate is None:
                continue
            csv_rows.append(
                {
                    "image_index": idx + 1,
                    "source_path": result.get("source_path", ""),
                    "keyword": candidate["label"],
                    "term_id": candidate.get("term_id") or "",
                    "score": f"{candidate['score']:.6f}",
                }
            )

    export_root = Path(EXPORT_DIR or (Path(tempfile.gettempdir()) / "mcam_exports"))
    export_root.mkdir(parents=True, exist_ok=True)
    export_path = export_root / f"mcam_keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with export_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["image_index", "source_path", "keyword", "term_id", "score"],
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    feedback = build_action_feedback(
        f"Prepared CSV export at {export_path}. Use the download button to save it.",
        "success",
    )
    return (
        "\n\n".join(output),
        gr.update(value=str(export_path), visible=True),
        feedback,
    )


css = """
:root {
    --app-bg: linear-gradient(180deg, #f3efe7 0%, #fcfaf6 100%);
    --surface: rgba(255, 252, 246, 0.94);
    --surface-strong: #fffaf0;
    --ink: #2b241f;
    --muted: #6d6157;
    --accent: #355c4d;
    --accent-soft: #dce9e2;
    --warning: #9d6b2f;
    --warning-soft: #f7e8ce;
    --error: #8e3b32;
    --error-soft: #f7ddd8;
    --success: #2f6b54;
    --success-soft: #d9eee4;
    --border: rgba(53, 92, 77, 0.18);
    --shadow: 0 18px 60px rgba(58, 44, 33, 0.08);
}

.gradio-container {
    background: var(--app-bg);
    color: var(--ink);
}

.app-shell {
    max-width: 1180px;
    margin: 0 auto;
    padding: 20px 0 32px;
}

.hero {
    background: linear-gradient(135deg, rgba(53, 92, 77, 0.95), rgba(98, 63, 41, 0.92));
    border-radius: 28px;
    color: #fdf9f2;
    padding: 30px 32px;
    box-shadow: var(--shadow);
    margin-bottom: 18px;
}

.hero h1 {
    margin: 0 0 8px;
    font-size: 2.25rem;
    line-height: 1.05;
}

.hero p {
    margin: 0;
    max-width: 780px;
    color: rgba(253, 249, 242, 0.88);
    font-size: 1rem;
}

.surface,
.summary-card,
.feedback-card,
.step-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 22px;
    box-shadow: var(--shadow);
}

.step-card {
    padding: 20px 22px;
    min-height: 100%;
}

.step-card h3 {
    margin: 0 0 8px;
    font-size: 1.05rem;
}

.step-card p {
    margin: 0;
    color: var(--muted);
}

.summary-card,
.feedback-card {
    padding: 14px 16px;
    font-size: 0.98rem;
}

.summary-card div + div,
.feedback-card div + div {
    margin-top: 4px;
}

.info-card {
    background: rgba(255, 252, 246, 0.96);
}

.success-card {
    background: var(--success-soft);
    border-color: rgba(47, 107, 84, 0.25);
}

.warning-card {
    background: var(--warning-soft);
    border-color: rgba(157, 107, 47, 0.25);
}

.error-card {
    background: var(--error-soft);
    border-color: rgba(142, 59, 50, 0.25);
}

.preview-nav {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 12px !important;
    height: 100% !important;
}

.section-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: var(--shadow);
    padding: 22px !important;
}

.caption {
    color: var(--muted);
    font-size: 0.94rem;
}

.counter-box textarea,
.counter-box input,
.status-box textarea,
.status-box input {
    text-align: center !important;
    color: var(--ink) !important;
}

.gr-button-primary {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
"""

theme = gr.themes.Soft(
    primary_hue="emerald",
    secondary_hue="stone",
    neutral_hue="zinc",
).set(
    body_background_fill="transparent",
    block_background_fill="rgba(255, 252, 246, 0.88)",
    block_border_width="1px",
    block_border_color="rgba(53, 92, 77, 0.18)",
    block_radius="22px",
    button_large_radius="999px",
)

LOGO_PATH = str(Path(__file__).parent / "~/media/logo.png")

with gr.Blocks(css=css, theme=theme, title="MCAM Art Keyword Generator", favicon_path=LOGO_PATH) as interface:
    with gr.Column(elem_classes=["app-shell"]):
        gr.HTML(
            """
            <section class="hero">
              <h1>MCAM Art Keyword Generator</h1>
              <p>Upload artwork images, review the suggested AAT keywords, remove anything weak, and regenerate only the rejected slots. The interface is built to keep the review step obvious for museum staff with minimal technical background.</p>
            </section>
            """
        )

        with gr.Row():
            gr.HTML(
                """
                <div class="step-card">
                  <h3>1. Upload artwork</h3>
                  <p>Bring in one or many images. You can preview them before running the model.</p>
                </div>
                """
            )
            gr.HTML(
                """
                <div class="step-card">
                  <h3>2. Remove weak keywords</h3>
                  <p>Uncheck anything that feels wrong, too broad, or visually unsupported.</p>
                </div>
                """
            )
            gr.HTML(
                """
                <div class="step-card">
                  <h3>3. Regenerate only those slots</h3>
                  <p>The app keeps the accepted keywords and fills the exact number you removed with new alternatives.</p>
                </div>
                """
            )

        state = gr.State(empty_app_state())
        preview_index = gr.State(0)

        with gr.Column(visible=True, elem_classes=["section-card"]) as upload_section:
            with gr.Row(equal_height=True):
                with gr.Column(scale=5):
                    current_image = gr.Image(
                        label="Artwork Preview",
                        type="pil",
                        height=540,
                    )
                with gr.Column(scale=3):
                    gr.Markdown(
                        "### Before you generate\n"
                        "Use the preview controls to look through your uploaded images.\n\n"
                        "When you click **Generate Keywords**, the runtime will retrieve a larger candidate pool, rerank it, and store enough extra suggestions so regeneration can happen without reusing rejected terms."
                    )
                    with gr.Column(elem_classes=["preview-nav"]):
                        preview_prev_btn = gr.Button("Previous", variant="secondary")
                        preview_counter = gr.Textbox(
                            value="No images selected",
                            interactive=False,
                            show_label=False,
                            container=False,
                            elem_classes=["counter-box"],
                        )
                        preview_next_btn = gr.Button("Next", variant="secondary")

            with gr.Row():
                with gr.Column(scale=3):
                    upload_input = gr.File(
                        file_count="multiple",
                        file_types=["image"],
                        label="Artwork Images",
                        value=default_repo_files,
                    )
                with gr.Column(scale=2):
                    process_btn = gr.Button("Generate Keywords", variant="primary", size="lg")
                    status_text = gr.Textbox(
                        label="Pipeline Status",
                        interactive=False,
                        value="Upload images to start.",
                        elem_classes=["status-box"],
                    )

        with gr.Column(visible=False, elem_classes=["section-card"]) as nav_section:
            with gr.Row(equal_height=True):
                with gr.Column(scale=5):
                    current_image_review = gr.Image(
                        label="Current Artwork",
                        type="pil",
                        height=540,
                    )
                    with gr.Row():
                        prev_btn = gr.Button("Previous Artwork", variant="secondary")
                        image_counter = gr.Textbox(
                            value="No image loaded",
                            interactive=False,
                            show_label=False,
                            container=False,
                            elem_classes=["counter-box"],
                        )
                        next_btn = gr.Button("Next Artwork", variant="secondary")

                with gr.Column(scale=4):
                    gr.Markdown("### Review suggested keywords")
                    gr.Markdown(
                        "Keep the terms that fit. Uncheck the ones you do not want. Regeneration will preserve the accepted terms and only replace the removed slots."
                    )
                    review_summary = gr.HTML("")
                    keyword_checkboxes = gr.CheckboxGroup(
                        choices=[],
                        value=[],
                        label="Current keyword set",
                        interactive=True,
                    )
                    action_feedback = gr.HTML(
                        build_action_feedback("Review the suggestions, uncheck any weak matches, then regenerate to fill the open slots.")
                    )
                    with gr.Row():
                        regenerate_btn = gr.Button(
                            "Regenerate Removed Keywords",
                            variant="primary",
                            size="lg",
                        )
                        export_btn = gr.Button("Export Selected Keywords", variant="secondary")
                    download_csv_btn = gr.DownloadButton(
                        "Download CSV Export",
                        visible=False,
                    )
                    export_output = gr.Textbox(
                        label="Export Preview",
                        lines=10,
                        placeholder="Your selected keywords will appear here.",
                    )
                    upload_more_btn = gr.Button("Start a New Batch", variant="secondary")

    upload_input.change(
        fn=on_upload,
        inputs=[upload_input],
        outputs=[current_image, preview_counter, preview_index],
    )

    interface.load(
        fn=initialize_upload_defaults,
        inputs=[],
        outputs=[upload_input, current_image, preview_counter, preview_index, status_text],
    )

    preview_next_btn.click(
        fn=preview_next,
        inputs=[upload_input, preview_index],
        outputs=[current_image, preview_counter, preview_index],
    )

    preview_prev_btn.click(
        fn=preview_prev,
        inputs=[upload_input, preview_index],
        outputs=[current_image, preview_counter, preview_index],
    )

    process_btn.click(
        fn=lambda: gr.update(value="Generating keyword suggestions...", visible=True),
        inputs=[],
        outputs=[status_text],
    )

    process_btn.click(
        fn=process_multiple_images,
        inputs=[upload_input, state],
        outputs=[
            current_image_review,
            image_counter,
            keyword_checkboxes,
            review_summary,
            action_feedback,
            export_output,
            state,
            upload_section,
            nav_section,
            status_text,
        ],
    )

    keyword_checkboxes.change(
        fn=update_selections,
        inputs=[keyword_checkboxes, state],
        outputs=[state, review_summary, action_feedback],
    )

    regenerate_btn.click(
        fn=regenerate_current_image,
        inputs=[keyword_checkboxes, state],
        outputs=[
            current_image_review,
            image_counter,
            keyword_checkboxes,
            review_summary,
            action_feedback,
            export_output,
            state,
        ],
    )

    next_btn.click(
        fn=next_image,
        inputs=[state],
        outputs=[
            current_image_review,
            image_counter,
            keyword_checkboxes,
            review_summary,
            action_feedback,
            state,
        ],
    )

    prev_btn.click(
        fn=previous_image,
        inputs=[state],
        outputs=[
            current_image_review,
            image_counter,
            keyword_checkboxes,
            review_summary,
            action_feedback,
            state,
        ],
    )

    export_btn.click(
        fn=export_results,
        inputs=[state],
        outputs=[export_output, download_csv_btn, action_feedback],
    )

    upload_more_btn.click(
        fn=upload_more,
        inputs=[],
        outputs=[
            upload_section,
            nav_section,
            status_text,
            upload_input,
            current_image,
            current_image_review,
            image_counter,
            keyword_checkboxes,
            review_summary,
            action_feedback,
            export_output,
            download_csv_btn,
            state,
            preview_counter,
            preview_index,
        ],
    )

if __name__ == "__main__":
    print("Launching Gradio interface...")
    interface.launch(share=True)
