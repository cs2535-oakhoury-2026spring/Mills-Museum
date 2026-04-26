"""
Filter AAT SQLite database to a museum-labeling subset and push to HuggingFace.

Starts from the same 12 target hierarchies as `aat_categories_to_hf.py` (English,
no changes to hierarchy selection), then applies additional quality filters to cut
the ~44k baseline down to a ~20k subset suitable for museum image labeling.

Filters applied (in order) on top of the baseline:
  1. Require an English scope note          (quality signal)
  2. Drop parenthetical / inverted forms    (e.g. "Conté crayon (TM)", "knives, gauge")
  3. Drop non-Latin scripts + IAST translit (scholarly Sanskrit/Devanagari forms)
  4. Drop Latin scientific names in Living Organisms (genera, binomials, families)
  5. Drop very deep sub-styles in Styles and Periods (depth >= 6)
  6. In big hierarchies (Furnishings, Components, Materials, Built Env, People):
       - drop multi-word leaves at depth >= 6
       - drop multi-word leaves in sibling groups >= 20
       - drop 3+ word leaves outright
     Single-word leaves are preserved at any depth (e.g. "chairs", "cotton",
     "arches", "roofs", "watercolor") because AAT often buries common concepts
     under "X and X components" pseudo-parents that inflate depth.

Usage:
    pip install pandas datasets huggingface_hub
    huggingface-cli login
    python aat_museum_filtered_to_hf.py

Note: the DB columns are named after their documented AAT names. Convenience
views (v_subject, v_term, v_rels, v_notes) select commonly-used columns.
"""

import os
import re
import sqlite3
import unicodedata

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv

load_dotenv()

DB_PATH   = "AAT_terms/aat_database.db"
HF_REPO   = "KeeganC/aat-selectively-filtered"
HF_TOKEN  = os.environ["HF_TOKEN"]
EN_LANG   = 70051

TARGET_HIERARCHIES = [
    # Physical Attributes Facet
    "Design Elements", "Color",
    # Styles and Periods Facet
    "Styles and Periods",
    # Agents Facet
    "People", "Living Organisms",
    # Activities Facet
    "Events", "Physical and Mental Activities", "Processes and Techniques",
    # Materials Facet
    "Materials",
    # Objects Facet
    "Built Environment", "Components", "Furnishings and Equipment",
]

BIG_HIERS = {
    "Furnishings and Equipment", "Components", "Materials",
    "Built Environment", "People",
}

# --------------------------------------------------------------------------- #
# helpers for text-based filters                                              #
# --------------------------------------------------------------------------- #

LATIN_SUFFIXES = (
    "aceae", "idae", "oidea", "iformes", "formes", "inae",
    "virales", "mycota", "mycetes", "phyta", "opsida", "acea", "ineae", "ales",
)
TRANSLIT_CHARS = set("ṭḍṇśṣṛṝḷṃḥṅñēōīūĀĪŪṂṢṬḌṆŚṄḤṀ")

def is_latin_binomial(t: str) -> bool:
    if not isinstance(t, str):
        return False
    if re.match(r"^[A-Z][a-z]+ [a-z]+( [a-z]+)?$", t):
        return True
    return bool(re.match(r"^[A-Z][a-z]+ (sect\.|subsp\.|var\.|ssp)", t))

def is_latin_rank(t: str) -> bool:
    if not isinstance(t, str) or " " in t or len(t) < 4 or not t[0].isupper():
        return False
    if t[1:].islower():          # "Abies", "Panthera" — single capitalized genus
        return True
    return any(t.lower().endswith(s) for s in LATIN_SUFFIXES)

def has_nonlatin_script(t: str) -> bool:
    if not isinstance(t, str):
        return False
    for ch in t:
        if ord(ch) < 128:
            continue
        try:
            name = unicodedata.name(ch, "")
        except ValueError:
            continue
        if "LATIN" in name:
            continue
        return True
    return False

def has_translit(t: str) -> bool:
    if not isinstance(t, str):
        return False
    return any(ch in TRANSLIT_CHARS for ch in t)

# --------------------------------------------------------------------------- #

def setup_views(conn: sqlite3.Connection) -> None:
    """Ensure convenience views exist over the properly-named AAT columns."""
    conn.executescript("""
    DROP VIEW IF EXISTS v_subject;
    DROP VIEW IF EXISTS v_term;
    DROP VIEW IF EXISTS v_rels;
    DROP VIEW IF EXISTS v_notes;

    CREATE VIEW v_subject AS
      SELECT SUBJECT_ID, FACET_CODE, PARENT_KEY, RECORD_TYPE, SORT_ORDER
      FROM SUBJECT;

    CREATE VIEW v_term AS
      SELECT SUBJECT_ID, TERM, TERM_ID, PREFERRED
      FROM TERM;

    CREATE VIEW v_rels AS
      SELECT SUBJECTA_ID, SUBJECTB_ID, REL_TYPE, PREFERRED
      FROM SUBJECT_RELS;

    CREATE VIEW v_notes AS
      SELECT SUBJECT_ID, LANGUAGE_CODE, NOTE_TEXT
      FROM SCOPE_NOTES;
    """)


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    setup_views(conn)

    # ── 1. locate hierarchy roots ───────────────────────────────────────── #
    ph = ",".join("?" for _ in TARGET_HIERARCHIES)
    roots = pd.read_sql_query(f"""
        SELECT s.SUBJECT_ID AS root_id,
               t.TERM       AS hierarchy_name,
               s.FACET_CODE
        FROM   v_subject s
        JOIN   v_term    t ON t.SUBJECT_ID = s.SUBJECT_ID AND t.PREFERRED = 'P'
        WHERE  s.RECORD_TYPE = 'H' AND t.TERM IN ({ph})
    """, conn, params=TARGET_HIERARCHIES)

    missing = set(TARGET_HIERARCHIES) - set(roots["hierarchy_name"])
    if missing:
        print(f"WARNING — hierarchy roots missing from DB: {missing}")
    print(f"Hierarchy roots matched: {len(roots)}/{len(TARGET_HIERARCHIES)}")

    # ── 2. recursive descent through preferred parent→child ────────────── #
    root_csv = ",".join(str(int(r)) for r in roots["root_id"])
    desc = pd.read_sql_query(f"""
        WITH RECURSIVE tree AS (
            SELECT SUBJECT_ID, SUBJECT_ID AS root_id, 0 AS depth
            FROM   v_subject
            WHERE  SUBJECT_ID IN ({root_csv})

            UNION ALL

            SELECT r.SUBJECTB_ID, t.root_id, t.depth + 1
            FROM   v_rels r
            JOIN   tree   t ON r.SUBJECTA_ID = t.SUBJECT_ID
            WHERE  r.PREFERRED = 'P' AND r.REL_TYPE = 'P'
        )
        SELECT SUBJECT_ID, root_id, MIN(depth) AS depth
        FROM   tree
        GROUP  BY SUBJECT_ID
    """, conn)

    rmeta = roots.set_index("root_id").to_dict("index")
    desc["hierarchy"] = desc["root_id"].map(lambda r: rmeta[r]["hierarchy_name"])
    desc["facet"]     = desc["root_id"].map(lambda r: rmeta[r]["FACET_CODE"])

    # ── 3. merge in subject + preferred term + scope notes + variants ───── #
    subj_meta = pd.read_sql_query("""
        SELECT SUBJECT_ID, RECORD_TYPE, PARENT_KEY, SORT_ORDER FROM v_subject
    """, conn)
    pref = pd.read_sql_query("""
        SELECT SUBJECT_ID, TERM AS preferred_term, TERM_ID
        FROM   v_term WHERE PREFERRED = 'P'
    """, conn)
    vari = pd.read_sql_query("""
        SELECT SUBJECT_ID, TERM FROM v_term WHERE PREFERRED != 'P'
    """, conn)
    var_agg = (
        vari.groupby("SUBJECT_ID")["TERM"].apply(list).reset_index()
            .rename(columns={"TERM": "variant_terms"})
    )
    notes = pd.read_sql_query("""
        SELECT SUBJECT_ID, NOTE_TEXT, LANGUAGE_CODE FROM v_notes
    """, conn)
    notes["_en"] = pd.to_numeric(notes["LANGUAGE_CODE"], errors="coerce") == EN_LANG
    notes_any = (notes.sort_values("_en", ascending=False)
                      .drop_duplicates("SUBJECT_ID", keep="first")
                      [["SUBJECT_ID", "NOTE_TEXT"]]
                      .rename(columns={"NOTE_TEXT": "scope_note"}))
    notes_en = set(notes.loc[notes["_en"], "SUBJECT_ID"].astype(int))

    df = desc.merge(subj_meta, on="SUBJECT_ID", how="left")
    df = df.merge(pref, on="SUBJECT_ID", how="left")
    df = df.merge(var_agg, on="SUBJECT_ID", how="left")
    df = df.merge(notes_any, on="SUBJECT_ID", how="left")

    # parent's preferred term (for breadcrumb)
    parent_term = pd.read_sql_query("""
        SELECT t.SUBJECT_ID AS PARENT_KEY, t.TERM AS parent_term
        FROM   v_term t WHERE t.PREFERRED = 'P'
    """, conn)
    df = df.merge(parent_term, on="PARENT_KEY", how="left")

    df["variant_terms"] = df["variant_terms"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    # ── 4. baseline prune (same as original script) ─────────────────────── #
    df = df.dropna(subset=["preferred_term"])
    df = df[df["RECORD_TYPE"] == "C"]                         # concepts only
    root_ids = set(roots["root_id"].astype(int))
    df = df[~df["PARENT_KEY"].isin(root_ids)]                 # drop root children
    print(f"Baseline (before museum filter): {len(df):,}")

    # ── 5. compute structural signals ────────────────────────────────────── #
    # children = subjects whose PARENT_KEY = this SUBJECT_ID (within descent)
    child_count = (
        desc.groupby("PARENT_KEY" if False else "SUBJECT_ID").size()
        * 0  # placeholder so names collide; we compute below properly
    )
    parent_counts = df.groupby("PARENT_KEY").size().rename("sib_count")
    df = df.merge(parent_counts, left_on="PARENT_KEY", right_index=True, how="left")

    child_counts = (
        desc.merge(subj_meta[["SUBJECT_ID", "PARENT_KEY"]],
                   on="SUBJECT_ID", how="left")
            .groupby("PARENT_KEY").size().rename("child_count")
    )
    df = df.merge(child_counts, left_on="SUBJECT_ID", right_index=True, how="left")
    df["child_count"] = df["child_count"].fillna(0).astype(int)
    df["is_leaf"] = df["child_count"] == 0
    df["n_words"] = df["preferred_term"].str.split().str.len()

    df["has_en_note"] = df["SUBJECT_ID"].astype(int).isin(notes_en)
    df["_paren"] = df["preferred_term"].str.contains(r"[\(\)]", regex=True, na=False)
    df["_comma"] = df["preferred_term"].str.contains(",", na=False)
    df["_nonlatin"] = df["preferred_term"].apply(has_nonlatin_script)
    df["_translit"] = df["preferred_term"].apply(has_translit)
    df["_latin_bi"] = df["preferred_term"].apply(is_latin_binomial)
    df["_latin_rk"] = df["preferred_term"].apply(is_latin_rank)

    # ── 6. apply filters ─────────────────────────────────────────────────── #
    before = len(df)
    df = df[df["has_en_note"]]
    print(f"  after require English scope note : {len(df):,}  (-{before-len(df):,})")

    before = len(df)
    df = df[~df["_paren"] & ~df["_comma"]]
    print(f"  after drop paren/comma forms     : {len(df):,}  (-{before-len(df):,})")

    before = len(df)
    df = df[~df["_nonlatin"] & ~df["_translit"]]
    print(f"  after drop non-Latin/translit    : {len(df):,}  (-{before-len(df):,})")

    before = len(df)
    df = df[~((df["hierarchy"] == "Living Organisms") &
              (df["_latin_bi"] | df["_latin_rk"]))]
    print(f"  after drop LO Latin sci names    : {len(df):,}  (-{before-len(df):,})")

    before = len(df)
    df = df[~((df["hierarchy"] == "Styles and Periods") & (df["depth"] >= 6))]
    print(f"  after Styles/Periods depth<6     : {len(df):,}  (-{before-len(df):,})")

    in_big = df["hierarchy"].isin(BIG_HIERS)
    before = len(df)
    drop = in_big & df["is_leaf"] & (df["depth"] >= 6) & (df["n_words"] >= 2)
    df = df[~drop]
    print(f"  after drop deep multi-word leaves: {len(df):,}  (-{before-len(df):,})")

    in_big = df["hierarchy"].isin(BIG_HIERS)
    before = len(df)
    drop = in_big & df["is_leaf"] & (df["sib_count"] >= 20) & (df["n_words"] >= 2)
    df = df[~drop]
    print(f"  after drop leaves in big sib-grps: {len(df):,}  (-{before-len(df):,})")

    in_big = df["hierarchy"].isin(BIG_HIERS)
    before = len(df)
    drop = in_big & df["is_leaf"] & (df["n_words"] >= 3)
    df = df[~drop]
    print(f"  after drop 3+ word leaves in big : {len(df):,}  (-{before-len(df):,})")

    # ── 7. clean up + assemble ───────────────────────────────────────────── #
    df = df.rename(columns={
        "SUBJECT_ID":  "subject_id",
        "RECORD_TYPE": "record_type",
        "PARENT_KEY":  "parent_id",
        "SORT_ORDER":  "sort_order",
        "TERM_ID":     "term_id",
    })
    col_order = [
        "subject_id", "preferred_term", "variant_terms", "scope_note",
        "hierarchy", "facet", "record_type",
        "parent_id", "parent_term", "sort_order", "term_id", "root_id",
        "depth", "child_count", "is_leaf",
    ]
    df = df[[c for c in col_order if c in df.columns]]

    print(f"\nFinal dataset: {len(df):,} rows × {len(df.columns)} cols")
    print(df["hierarchy"].value_counts().to_string(header=False))

    # ── 8. push to HuggingFace ───────────────────────────────────────────── #
    ds = Dataset.from_pandas(df, preserve_index=False)
    ds.push_to_hub(HF_REPO, private=False, token=HF_TOKEN)
    print(f"\nPushed to https://huggingface.co/datasets/{HF_REPO}")

    conn.close()


if __name__ == "__main__":
    main()
