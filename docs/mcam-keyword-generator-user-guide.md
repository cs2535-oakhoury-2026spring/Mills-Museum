# MCAM Keyword Generator — User Guide

Welcome! This guide is for museum staff who use the **MCAM Keyword Generator** in a web browser. You do not need any technical background—if you are comfortable opening a link, uploading files, and clicking buttons, you can use this tool.

The generator suggests **Art & Architecture Thesaurus (AAT)** style keywords from your artwork images. Treat every suggestion as a **starting point**: always review and edit before using keywords in your collection records.

---

## How to open the tool

Your institution will give you a **single web address** (link) for the keyword tool. Open that link in Chrome, Safari, Firefox, or Edge—whichever browser you normally use.

- The same address loads the **whole application**: the pages you see and the work the tool does behind the scenes all use that one site.
- If the link does not load or you see repeated errors, contact **your IT contact** or **the person who shared the link**—they make sure the session is running and can share an updated address if needed.

---

## What you see at the top of the page

Across the top you will see the Mills College Art Museum logo and the title **MCAM Keyword Generator**, with a short line about the **Art & Architecture Thesaurus Pipeline**.

On the right, a small status pill tells you where you are in the workflow:

| Status       | What it means |
|-------------|----------------|
| **Ready**   | You can add images and change settings before generating keywords. |
| **Processing** | The tool is working through your images (usually one at a time). |
| **Review** | Results are ready; you can browse keywords, turn them on or off, and export. |

Below that, the main area changes depending on the step you are on.

---

## The big picture: three steps

```mermaid
flowchart LR
  ready[Ready]
  processing[Processing]
  review[Review]
  ready --> processing
  processing --> review
```

1. **Ready** — Upload images and adjust options, then click **Generate Keywords**.
2. **Processing** — Wait while each image is analyzed. You may see a written description appear and a progress bar move.
3. **Review** — Check suggested keywords, include or exclude them, then copy or download your results.

---

## Step 1: Ready — Upload your images

### Adding files

- **Drag and drop** image files onto the dashed “Drop images here” area, or **click** that area to browse your computer.
- Supported types: **JPEG**, **PNG**, and **WebP**.
- You can add **more than one** image at a time. They are processed **one after another**, not all at once.

### Queue and preview

- The **Queue** lists every file you added. Click a filename to show it in the **preview** above.
- If you have multiple files, use the **arrows** under the preview to move between them.
- Click **×** next to a name to **remove** that file from the queue before you generate.

### Batch errors

If something went wrong for the **entire** batch (for example, nothing could be processed), you may see a red message at the top with a short explanation. You can click **Dismiss** to hide it after you have read it.

---

## Step 2: Ready — Options before you click Generate

These controls are on the **right** side of the screen. You can adjust them before each run.

### How many keywords to request

- **# Keywords to generate** — Choose between **1** and **50** (default **20**) using the slider or the number box.

### Per-hierarchy mode (optional)

If your institution’s setup provides a hierarchy list, you may see a **Per-hierarchy** switch.

- When it is **off**, you use the single **# Keywords to generate** control above.
- When it is **on**, you set **how many keywords to pull from each category** (for example Materials, Styles and Periods) with separate sliders from **0** to **20** each.
- **0** for a category means “don’t use that category.”
- The screen shows a **total** that is the **sum** of all those numbers. You need at least **one** keyword in total (sum greater than zero) to run.
- **Query Bias** (below) still applies: it splits each category’s count between what comes from the **image alone** and what comes from the **written description** of the artwork.

### Query Bias (Image ↔ Description)

- The slider runs from **Image** on one side to **Description** on the other (from **0** to **1**, default **0.5**).
- **Toward Image** — More weight on what the tool sees in the picture.
- **Toward Description** — More weight on the automatically written description of the artwork (when that description is available).
- **0.5** means the counts are split evenly between those two sources when both are used.

### Diversity (Diverse ↔ Relevant)

- Labeled **Diversity (MMR)** on screen, from **0** to **1** (default **0.96**).
- **More Diverse** — Suggestions spread out more; less repetition of similar ideas.
- **More Relevant** — Suggestions stay closer to the single best matches.
- Most users can leave this near the default unless your project lead suggests otherwise.

### Helpful tips on the same screen

The **How it works** and **Tips** box summarizes the workflow. If the on-screen text mentions a technical address or notebook, ignore the jargon: use **only the web address your institution gave you**, and ask your contact if the page will not load.

When you are ready, click **Generate Keywords**.

---

## Step 3: Processing — What happens while you wait

The status at the top switches to **Processing**.

- You will see which image is active (for example, “Processing image **2** of **5**”).
- A **progress bar** shows overall progress through the batch.
- You may see an **AI Description** box where a short description of the artwork **types out** word by word. That text helps the tool choose keywords when your session supports it.
- Short status messages may appear (for example, that the tool is retrieving or scoring keywords).

**Important:** The full, clickable keyword list appears on the **next** step (**Review**), not as a complete grid during this waiting screen. When processing finishes for all images that succeeded, the tool moves you to **Review** automatically.

---

## Step 4: Review — Working with results

The status at the top shows **Review**.

### If one image failed

You move between images with **Previous** and **Next** (under the picture on the left). If some files failed, a small note may show how many **failed** in total.

- For a **failed** image, you will see a clear error screen with the **filename** and a **short message**, and sometimes a small preview.
- For a **successful** image, you see the normal review layout.

Failed images are **skipped** when you export a **combined CSV** of the whole batch (only successful images contribute rows). The **combined text** export can still mention errors in plain language—see [Exporting your results](#exporting-your-results).

### Layout

- **Left:** Large preview of the current image, the **filename**, and optional **retrieval** counts (how suggestions were gathered—informational only).
- **Right:** The **Keywords** panel with all suggestions for this image.

### Viewing the picture larger

Move your pointer over the image and use the control that appears to **open a larger view**. Close it with the **X**, by pressing **Escape**, or by clicking the dark area around the picture.

### AI Description (review)

If a description was created for this image, you can open **AI Description** under the preview to read the full text.

### Moving to another image or starting over

- **Previous** / **Next** — Other images from the same batch.
- **Export all** — Download a **single text file** for the **entire** batch (see below).
- **CSV** (next to Export all) — Download a **single spreadsheet-style file** for the **entire** batch.
- **Upload new** — Clear this batch and return to the **Ready** screen to choose new files.

---

## The Keywords panel

### Including and excluding keywords

Each keyword appears as a **tile** with a small **checkbox**.

- **Checked** — The keyword is **included**. It counts toward **Copy**, **TXT**, **CSV**, and batch exports.
- **Unchecked** — The keyword is **excluded**. It appears dimmed and is **not** exported.

New suggestions usually start **included**; you uncheck anything you do not want.

### Confidence percentage

You may see a **percent** on each tile. Higher numbers mean the tool is more confident that the term fits the image—still **not** a guarantee for cataloging.

While scores are still updating, you might see a short **“…”** animation instead of a number. A thin **Scoring keywords…** bar at the top of the panel can show progress until scoring is done. If scoring is interrupted, the bar may turn red and show an error state—your selections still work, but you may want to note that scores did not finish.

### Scope notes

Some keywords have a small **chevron** (arrow). Click it to read a **scope note**—extra context about how the term is meant to be used in the thesaurus.

### Filter

Use the **Filter** box to show only keywords whose text **contains** what you type. This does not remove them from the list permanently; it only hides non-matching tiles until you clear the filter.

### Group

**Group** organizes keywords under their **hierarchy** headings (for example Materials, Color). Click again to return to a flat list.

### Heatmap

**Heatmap** changes tile **background colors** to reflect confidence (stronger color usually means higher confidence). This is optional and only helps you scan the list visually.

### Copy and single-image exports

- **Copy** — Puts all **included** keywords on the clipboard as a **comma-separated** list (for pasting into email or a document).
- **TXT** — Downloads a **text file** for **this image only** (see [Exporting your results](#exporting-your-results)).
- **CSV** — Downloads a **spreadsheet file** for **this image only**, in the same column layout as the batch CSV.

These buttons are **disabled** if no keywords are included.

---

## Accession numbers and file naming

Exports use an **accession-style label** derived from each file’s **name** (not from your catalog database):

1. Take the **filename** without its extension (`.jpg`, `.png`, etc.).
2. If the name contains an **underscore** (`_`), keep only the part **before the first underscore**.

**Examples:**

| Filename              | Label used in exports |
|-----------------------|------------------------|
| `M-001.jpg`           | `M-001` |
| `2024.12_front.png`   | `2024.12` |
| `Smith_portrait.webp` | `Smith` |

**Tip:** Name files the way you want the **accession column** to read in CSV exports—for example `M-001.jpg` rather than long descriptive filenames—so spreadsheet rows line up with your object records.

---

## Exporting your results

All downloaded files are ordinary text or CSV files you can open in **Notepad**, **TextEdit**, **Word**, **Excel**, **Numbers**, or Google Sheets.

### Combined batch — Text (`mcam_keywords_export.txt`)

Click **Export all** (under the image on the left).

- You get **one file** for the **whole batch**.
- Each image gets a **block** of text. Blocks are separated by a **blank line**.
- For a **successful** image, one line looks like:  
  `AccessionLabel: keyword one, keyword two, keyword three`  
  Only **included** keywords appear. If none are included, you will see `(no keywords selected)` after the colon.
- For a **failed** image, the block shows the accession label and a line starting with `[Error]` and a short message.

### Combined batch — CSV (`mcam_keywords_export.csv`)

Click **CSV** next to **Export all**.

- **File name:** `mcam_keywords_export.csv`
- **Only successful images** appear. Failed images do not add rows.
- **One row per included keyword.**
- See [CSV format (for spreadsheets and EmbARK)](#csv-format-for-spreadsheets-and-embark) for column details.

### Current image only — Text (`{accession}_keywords.txt`)

Click **TXT** in the Keywords panel.

- **File name:** based on the accession label, for example `M-001_keywords.txt`.
- Contains the accession label, a short heading, a **bulleted list** of included keywords **with confidence** when available, and a final **comma-separated** line of the same terms.

### Current image only — CSV (`{accession}_keywords.csv`)

Click **CSV** in the Keywords panel.

- **File name:** for example `M-001_keywords.csv`.
- Same **two-column** layout as the combined batch CSV, but only for the **current** image’s included keywords.

---

## CSV format (for spreadsheets and EmbARK)

This section describes **exactly** what the CSV files contain so you can open them confidently or share them with a registrar.

### Columns

| Column name          | Contents |
|----------------------|----------|
| `accession_number`   | The label derived from the image filename (see [Accession numbers](#accession-numbers-and-file-naming)). If the tool cannot derive one, it may use `unknown`. |
| `keyword`            | The text of one included keyword (no percentage in this column). |

**First row** of the file is always the header:

```text
accession_number,keyword
```

### One object, many rows

Each keyword gets its **own row**. The same accession repeats on every row for that object.

**Example:**

```text
accession_number,keyword
M-001,landscapes (repositories)
M-001,oil paintings (visual works)
M-002,bronze (metal)
```

### Special characters (commas, quotes, new lines)

If an accession or keyword contains a **comma**, **quotation mark**, or **line break**, the file follows normal CSV rules: the value is wrapped in **double quotes**, and any `"` inside the value is doubled (`""`). You do not need to type this yourself—the tool builds the file for you. Spreadsheet programs understand this format when you open the file.

### Encoding

Files are saved as **plain text (UTF-8)**, which works well in current versions of Excel, Numbers, and Google Sheets.

### Using this file with EmbARK

EmbARK setups differ by institution. This guide does not assume a specific EmbARK screen or menu name. Use this checklist with your **registrar** or **EmbARK administrator**:

1. Open the CSV in Excel or Numbers and confirm each row looks correct (accession + one keyword).
2. Confirm which **EmbARK field** should match the **`accession_number`** column—usually the same identifier you use on the object record every day.
3. Follow your museum’s **import, bulk update, or keyword workflow** for bringing spreadsheet data into EmbARK. If your site uses a particular import template, ask whether this two-column file can be used as-is or should be copied into that template.

If anything in the file does not match EmbARK’s expectations, your administrator can help map columns or adjust the workflow—**do not** change the tool’s export format unless your technical team asks you to.

---

## Troubleshooting

### Every image failed and I am back on the upload screen

You may see a message that **every image failed** and to check the service or try again. That means nothing in that batch could be completed.

- Try again after a short wait.
- Confirm you are still using the **correct link** from your institution.
- If it keeps happening, contact **IT** or **the person who runs the session**—they can verify that the service is running.

### Some images failed but others worked

Use **Previous** and **Next** to view each result. A badge may show how many **failed**. Failed items show an error message for that file only.

- **Combined CSV** includes only **successful** images.
- **Combined text** can still list errors per file so you know which accessions to redo.

### “Scoring keywords…” never finishes or looks wrong

If the scoring bar stops with an error style, your keyword list is still there; percentages might be incomplete. You can still **include**, **exclude**, and **export**. If you need reliable scores for documentation, run that image again later or ask your technical contact.

### I want to start a completely new batch

Click **Upload new**. That clears the current results and returns you to **Ready** so you can pick new files and options.

### The Per-hierarchy switch never appears

The hierarchy list is loaded when the page first opens. If it cannot be loaded (for example, the service was unavailable for a moment), the toggle may not appear. Refresh the page or try again later; if the problem persists, contact your support contact.

---

## Summary

1. Open your institution’s **link**.
2. On **Ready**, add **images**, set **options**, then **Generate Keywords**.
3. On **Processing**, wait for the **progress** (and optional **description**).
4. On **Review**, **check** or **uncheck** keywords, use **Filter**, **Group**, or **Heatmap** if helpful.
5. **Export** with **Export all** / batch **CSV**, or **Copy** / **TXT** / **CSV** for one image.
6. Name files so the **accession column** matches your records.
7. For **EmbARK**, verify the CSV with your **registrar** and follow your museum’s import steps.

Thank you for using the MCAM Keyword Generator. When in doubt, treat every suggestion as a draft and curate before it goes into the collection catalog.
