import gradio as gr
import torch
from PIL import Image


def preview_image(files, index):
    if not files or len(files) == 0:
        return None, "—"
    index = max(0, min(index, len(files) - 1))
    return Image.open(files[index]), f"{index + 1} of {len(files)}"


def preview_next(files, index):
    index = min(index + 1, len(files) - 1) if files else 0
    img, counter = preview_image(files, index)
    return img, counter, index


def preview_prev(files, index):
    index = max(index - 1, 0) if files else 0
    img, counter = preview_image(files, index)
    return img, counter, index


def on_upload(files):
    if not files or len(files) == 0:
        return None, "—", 0
    img, counter = preview_image(files, 0)
    return img, counter, 0


def process_multiple_images(images, state):
    state = {"all_results": {}, "current_index": 0}

    if not images or len(images) == 0:
        return (
            None,
            gr.update(choices=[], value=[]),
            "",
            "—",
            state,
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
        )

    for idx, image_path in enumerate(images):
        try:
            image = Image.open(image_path)
            art_query = {"image": image, "text": ""}
            query_input = [art_query]

            image_features = embedding_model.process(query_input)
            image_features = torch.nn.functional.normalize(image_features, p=2, dim=1)

            results = collection.query(
                query_embeddings=image_features.cpu().float().tolist(), n_results=10
            )

            labels = []
            input_docs = []

            if results["documents"]:
                for doc, metadatas in zip(
                    results["documents"][0], results["metadatas"][0]
                ):
                    input_docs.append({"text": doc})
                    labels.append(metadatas["term_label"])

            rerank_inputs = {
                "instruction": "Retrieve Art & Architecture Thesaurus terms relevant to the given image.",
                "query": art_query,
                "documents": input_docs,
                "fps": 1.0,
            }

            scores = reranking_model.process(rerank_inputs)
            sorted_results = sorted(zip(scores, labels), reverse=True)

            state["all_results"][idx] = {
                "image": image,
                "keywords": [label for _, label in sorted_results],
                "scores": [score for score, _ in sorted_results],
                "selected": [True] * len(sorted_results),
            }

        except Exception as e:
            print(f"Error processing image {idx}: {e}")
            state["all_results"][idx] = {
                "image": (
                    Image.open(image_path)
                    if isinstance(image_path, str)
                    else image_path
                ),
                "keywords": [],
                "scores": [],
                "selected": [],
            }

    img, counter, checkbox_update = show_image(0, state)

    return (
        img,
        checkbox_update,
        "",
        counter,
        state,
        gr.update(visible=False),  # hide upload section
        gr.update(visible=True),  # show nav section
        gr.update(visible=False),  # hide status
    )


def show_image(index, state):
    all_results = state["all_results"]
    if index not in all_results:
        return None, "—", gr.update(choices=[], value=[])

    state["current_index"] = index
    result = all_results[index]

    keyword_choices = [
        f"{kw} ({score * 100:.1f}%)"
        for kw, score in zip(result["keywords"], result["scores"])
    ]
    selected_keywords = [
        keyword_choices[i] for i, sel in enumerate(result["selected"]) if sel
    ]

    counter = f"Image {index + 1} of {len(all_results)}"
    return (
        result["image"],
        counter,
        gr.update(choices=keyword_choices, value=selected_keywords),
    )


def update_selections(selected_keywords, state):
    all_results = state["all_results"]
    current_index = state["current_index"]
    if current_index not in all_results:
        return state
    result = all_results[current_index]
    for i in range(len(result["keywords"])):
        keyword_display = f"{result['keywords'][i]} ({result['scores'][i] * 100:.1f}%)"
        result["selected"][i] = keyword_display in selected_keywords
    return state


def next_image(state):
    idx = state["current_index"]
    next_idx = min(idx + 1, len(state["all_results"]) - 1)
    img, counter, cb = show_image(next_idx, state)
    return img, counter, cb, state


def previous_image(state):
    idx = state["current_index"]
    prev_idx = max(idx - 1, 0)
    img, counter, cb = show_image(prev_idx, state)
    return img, counter, cb, state


def upload_more():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(
            visible=True, value="", placeholder="Generate keywords to get started."
        ),
        None,
        "—",
        gr.update(choices=[], value=[]),
        "",
        {"all_results": {}, "current_index": 0},
        "—",
        0,
    )


def export_results(state):
    all_results = state["all_results"]
    output = []
    for idx in sorted(all_results.keys()):
        result = all_results[idx]
        selected_kw = [
            result["keywords"][i] for i, sel in enumerate(result["selected"]) if sel
        ]
        output.append(f"Image {idx + 1}: {', '.join(selected_kw)}")
    return "\n\n".join(output)


# ── UI ───────────────────────────────────────────────────────────────────────

css = """
.preview-nav {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 12px !important;
    height: 500px !important;
}
.preview-nav button {
    width: 100% !important;
}
.centered-text textarea {
    text-align: center !important;
}
"""

with gr.Blocks(css=css) as interface:
    gr.Markdown("# MCAM Art Keyword Generator")
    gr.Markdown(
        "Upload artwork images to automatically generate AAT keywords for cataloging."
    )

    state = gr.State({"all_results": {}, "current_index": 0})
    preview_index = gr.State(0)

    # ── Upload section ───────────────────────────────────────────────────
    with gr.Column(visible=True) as upload_section:
        with gr.Row(equal_height=True):

            # Image viewer
            with gr.Column(scale=3):
                current_image = gr.Image(
                    label="Artwork Preview",
                    type="pil",
                    height=500,
                    width=500,
                )

            # Preview nav — vertically centered to the right
            with gr.Column(scale=1, min_width=140, elem_classes=["preview-nav"]):
                preview_prev_btn = gr.Button("← Previous")
                preview_counter = gr.Textbox(
                    value="—",
                    interactive=False,
                    show_label=False,
                    container=False,
                    elem_classes=["centered-text"],
                )
                preview_next_btn = gr.Button("Next →")

        with gr.Row():
            with gr.Column():
                upload_input = gr.File(
                    file_count="multiple",
                    file_types=["image"],
                    label="Select Images",
                )
                process_btn = gr.Button("Generate Keywords", variant="primary")
                status_text = gr.Textbox(
                    label="Status",
                    interactive=False,
                    placeholder="Generate keywords to get started.",
                    visible=True,
                )

    # ── Review section ───────────────────────────────────────────────────
    with gr.Column(visible=False) as nav_section:

        current_image_review = gr.Image(
            label="Artwork",
            type="pil",
            height=500,
            width=500,
        )

        with gr.Row():
            prev_btn = gr.Button("← Previous")
            image_counter = gr.Textbox(
                value="—",
                interactive=False,
                show_label=False,
                container=False,
                elem_classes=["centered-text"],
            )
            next_btn = gr.Button("Next →")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Keywords")
                gr.Markdown(
                    "Uncheck any keywords you'd like to remove before exporting."
                )
                keyword_checkboxes = gr.CheckboxGroup(
                    choices=[],
                    label="",
                    interactive=True,
                )
            with gr.Column(scale=1):
                export_output = gr.Textbox(
                    label="Exported Keywords",
                    lines=12,
                )

        with gr.Row():
            export_btn = gr.Button("Export Selected Keywords", variant="primary")
            upload_more_btn = gr.Button("Upload New Images", variant="secondary")

    # ── Events ───────────────────────────────────────────────────────────

    upload_input.change(
        fn=on_upload,
        inputs=[upload_input],
        outputs=[current_image, preview_counter, preview_index],
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
        fn=lambda: gr.update(value="Processing...", visible=True),
        inputs=[],
        outputs=[status_text],
    )

    process_btn.click(
        fn=process_multiple_images,
        inputs=[upload_input, state],
        outputs=[
            current_image_review,
            keyword_checkboxes,
            export_output,
            image_counter,
            state,
            upload_section,
            nav_section,
            status_text,
        ],
    )

    keyword_checkboxes.change(
        fn=update_selections,
        inputs=[keyword_checkboxes, state],
        outputs=[state],
    )

    next_btn.click(
        fn=next_image,
        inputs=[state],
        outputs=[current_image_review, image_counter, keyword_checkboxes, state],
    )

    prev_btn.click(
        fn=previous_image,
        inputs=[state],
        outputs=[current_image_review, image_counter, keyword_checkboxes, state],
    )

    export_btn.click(
        fn=export_results,
        inputs=[state],
        outputs=[export_output],
    )

    upload_more_btn.click(
        fn=upload_more,
        inputs=[],
        outputs=[
            upload_section,
            nav_section,
            status_text,
            current_image,
            image_counter,
            keyword_checkboxes,
            export_output,
            state,
            preview_counter,
            preview_index,
        ],
    )

print("Launching Gradio interface...")
interface.launch(share=True)
