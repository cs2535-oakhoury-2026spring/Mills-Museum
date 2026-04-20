"""
Build a simple Hugging Face dataset from raw AAT export files.

This script:
- reads raw term rows from `TERM.out`
- reads note rows from `SCOPE_NOTES.out`
- keeps only preferred English terms
- attaches English notes to those terms
- uploads the result to the Hugging Face Hub

It is a direct operational script with hard-coded paths, not a reusable library.
"""
import pandas as pd
from datasets import Dataset


# Load the raw term export. The chosen columns are:
# - preferred/non-preferred flag
# - term ID
# - visible label text
df = pd.read_csv('AAT_terms\\aat_rel_0125\\TERM.out',
                sep='\t',
                on_bad_lines='skip',
                usecols=[7, 9, 10],
                names=['term_preference','term_id', 'term_label'],
                dtype={'term_id': str, 'term_preference': str, 'term_label': str})

print("\nTERMS DATAFRAME")
print(df.head())

notes = pd.read_csv('AAT_terms\\aat_rel_0125\\SCOPE_NOTES.out',
                engine="python",
                sep='\t',
                on_bad_lines='skip',
                usecols=[1, 2, 3],
                names=['term_id', 'language_id', 'term_note'],
                dtype={'term_id': str, 'language_id': str, 'term_note': str}
                )

print("\nNOTES DATAFRAME")
print(notes.head())

# Getty language code `70051` stands for English. This keeps the upload small
# and aligned with the current English-label workflow.
notes_filtered = notes[notes['language_id'] == '70051']
print("\nENGLISH FILTERED NOTES DATAFRAME")
print(notes_filtered.head())


# `P` marks preferred terms, which are treated as the canonical label.
df_filtered = df[df['term_preference'] == 'P']
print("\nPREFERRED TERMS FILTERED DATAFRAME")
print(df_filtered.head())
df_filtered = df_filtered.drop(columns=['term_preference'])


# Join preferred terms with their English notes using the shared term ID.
aat_dataset = pd.merge(df_filtered, notes_filtered, on='term_id', how='left')
print("\nMERGED DATAFRAME")
print(aat_dataset.head())

print(len(aat_dataset))
# Convert the pandas DataFrame to a Hugging Face Dataset
hf_dataset = Dataset.from_pandas(aat_dataset)
print("\nHUGGING FACE DATASET")
# Publish the finished table as a public dataset.
hf_dataset.push_to_hub("aat-preferred-terms", private=False)
