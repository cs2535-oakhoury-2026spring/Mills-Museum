"""
Filter AAT SQLite database to museum-relevant hierarchies and push to HuggingFace.

    pip install pandas datasets huggingface_hub
    huggingface-cli login
"""

import os
import sqlite3
import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "AAT_terms/aat_database.db"
HF_REPO = "KeeganC/aat-museum-subset"
HF_TOKEN = os.environ["HF_TOKEN"]

# ── hierarchies to keep ──────────────────────────────────────────────
TARGET_HIERARCHIES = [
    # Physical Attributes Facet
    "Design Elements",
    "Color",
    # Styles and Periods Facet
    "Styles and Periods",
    # Agents Facet
    "People",
    "Living Organisms",
    # Activities Facet
    "Events",
    "Physical and Mental Activities",
    "Processes and Techniques",
    # Materials Facet
    "Materials",
    # Objects Facet
    "Built Environment",
    "Components",
    "Furnishings and Equipment",
]

# AAT language code for English scope notes
EN_LANG_CODE = "70051"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")

    # ── 1. locate hierarchy roots ────────────────────────────────────
    ph = ",".join("?" for _ in TARGET_HIERARCHIES)
    roots = pd.read_sql_query(f"""
        SELECT s.SUBJECT_ID AS root_id,
               t.TERM        AS hierarchy_name,
               s.FACET_CODE
        FROM   SUBJECT s
        JOIN   TERM t ON t.SUBJECT_ID = s.SUBJECT_ID
                     AND t.PREFERRED  = 'P'
        WHERE  s.RECORD_TYPE = 'H'
          AND  t.TERM IN ({ph})
    """, conn, params=TARGET_HIERARCHIES)

    found = set(roots["hierarchy_name"])
    missing = set(TARGET_HIERARCHIES) - found
    if missing:
        print(f"⚠  Not found in DB: {missing}")
    print(f"✓  {len(roots)} hierarchy roots matched")
    for _, r in roots.iterrows():
        print(f"   {r['hierarchy_name']:30s}  id={r['root_id']}  facet={r['FACET_CODE']}")

    # ── 2. recursive descent (preferred parent→child) ────────────────
    root_csv = ",".join(str(int(r)) for r in roots["root_id"])
    desc = pd.read_sql_query(f"""
        WITH RECURSIVE tree AS (
            SELECT SUBJECT_ID, SUBJECT_ID AS root_id
            FROM   SUBJECT
            WHERE  SUBJECT_ID IN ({root_csv})

            UNION ALL

            SELECT sr.SUBJECTB_ID, t.root_id
            FROM   SUBJECT_RELS sr
            JOIN   tree t ON sr.SUBJECTA_ID = t.SUBJECT_ID
            WHERE  sr.PREFERRED = 'P'
              AND  sr.REL_TYPE  = 'P'
        )
        SELECT DISTINCT SUBJECT_ID, root_id FROM tree
    """, conn)
    print(f"✓  {len(desc)} subjects across selected hierarchies")

    # map each subject → its hierarchy name + facet code
    rmeta = roots.set_index("root_id").to_dict("index")
    subj = desc.drop_duplicates(subset="SUBJECT_ID", keep="first").copy()
    subj["hierarchy"] = subj["root_id"].map(lambda r: rmeta[r]["hierarchy_name"])
    subj["facet"]     = subj["root_id"].map(lambda r: rmeta[r]["FACET_CODE"])

    # ── 3. temp table for fast joins ─────────────────────────────────
    conn.execute("CREATE TEMP TABLE _keep (SUBJECT_ID INTEGER PRIMARY KEY)")
    conn.executemany(
        "INSERT OR IGNORE INTO _keep VALUES (?)",
        [(int(i),) for i in subj["SUBJECT_ID"]],
    )

    # ── 4. gather metadata ───────────────────────────────────────────
    # preferred term
    pref = pd.read_sql_query("""
        SELECT t.SUBJECT_ID, t.TERM AS preferred_term, t.TERM_ID
        FROM   TERM t JOIN _keep k ON t.SUBJECT_ID = k.SUBJECT_ID
        WHERE  t.PREFERRED = 'P'
    """, conn)

    # variant terms  →  list per subject
    vari = pd.read_sql_query("""
        SELECT t.SUBJECT_ID, t.TERM
        FROM   TERM t JOIN _keep k ON t.SUBJECT_ID = k.SUBJECT_ID
        WHERE  t.PREFERRED != 'P'
    """, conn)
    var_agg = (
        vari.groupby("SUBJECT_ID")["TERM"]
        .apply(list).reset_index()
        .rename(columns={"TERM": "variant_terms"})
    )

    # subject-level fields
    subj_meta = pd.read_sql_query("""
        SELECT s.SUBJECT_ID, s.RECORD_TYPE, s.PARENT_KEY, s.SORT_ORDER
        FROM   SUBJECT s JOIN _keep k ON s.SUBJECT_ID = k.SUBJECT_ID
    """, conn)

    # scope notes (prefer English, fall back to first available)
    notes = pd.read_sql_query("""
        SELECT sn.SUBJECT_ID, sn.NOTE_TEXT, sn.LANGUAGE_CODE
        FROM   SCOPE_NOTES sn JOIN _keep k ON sn.SUBJECT_ID = k.SUBJECT_ID
    """, conn)
    if not notes.empty:
        notes["_en"] = notes["LANGUAGE_CODE"].astype(str).str.strip() == EN_LANG_CODE
        notes = (notes.sort_values("_en", ascending=False)
                      .drop_duplicates("SUBJECT_ID", keep="first")
                      [["SUBJECT_ID", "NOTE_TEXT"]]
                      .rename(columns={"NOTE_TEXT": "scope_note"}))

    # parent's preferred term (gives breadcrumb context)
    parent_term = pd.read_sql_query("""
        SELECT t.SUBJECT_ID AS PARENT_KEY, t.TERM AS parent_term
        FROM   TERM t
        WHERE  t.PREFERRED = 'P'
          AND  t.SUBJECT_ID IN (
               SELECT DISTINCT s.PARENT_KEY
               FROM SUBJECT s JOIN _keep k ON s.SUBJECT_ID = k.SUBJECT_ID
          )
    """, conn)

    # ── 5. assemble ──────────────────────────────────────────────────
    df = subj[["SUBJECT_ID", "hierarchy", "facet", "root_id"]]
    df = df.merge(subj_meta, on="SUBJECT_ID", how="left")
    df = df.merge(pref,      on="SUBJECT_ID", how="left")
    df = df.merge(var_agg,   on="SUBJECT_ID", how="left")
    if not notes.empty:
        df = df.merge(notes, on="SUBJECT_ID", how="left")
    else:
        df["scope_note"] = None
    df = df.merge(parent_term, on="PARENT_KEY", how="left")

    df["variant_terms"] = df["variant_terms"].apply(
        lambda x: x if isinstance(x, list) else []
    )
    df = df.rename(columns={
        "SUBJECT_ID":  "subject_id",
        "RECORD_TYPE": "record_type",
        "PARENT_KEY":  "parent_id",
        "SORT_ORDER":  "sort_order",
        "TERM_ID":     "term_id",
    })
    df = df.dropna(subset=["preferred_term"])
    df = df[df["record_type"] == "C"]  # keep only concepts, drop H/G/F records


    # drop direct children of hierarchy roots (broad category labels, not real terms)
    root_ids = set(roots["root_id"].astype(int))
    df = df[~df["parent_id"].isin(root_ids)]

    
    col_order = [
        "subject_id", "preferred_term", "variant_terms", "scope_note",
        "hierarchy", "facet", "record_type",
        "parent_id", "parent_term", "sort_order", "term_id", "root_id",
    ]
    df = df[[c for c in col_order if c in df.columns]]

    print(f"\n✓  Final dataset: {len(df):,} rows × {len(df.columns)} cols")
    print(df["hierarchy"].value_counts().to_string(header=False))

    # ── 6. push to HuggingFace ───────────────────────────────────────
    ds = Dataset.from_pandas(df, preserve_index=False)
    ds.push_to_hub(HF_REPO, private=False, token=HF_TOKEN)
    print(f"\n✓  Pushed → https://huggingface.co/datasets/{HF_REPO}")

    conn.close()


if __name__ == "__main__":
    main()