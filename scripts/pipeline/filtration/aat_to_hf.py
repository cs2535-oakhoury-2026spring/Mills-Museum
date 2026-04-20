"""
Pipeline-local copy of the simple AAT-to-Hugging-Face upload script.

This version mirrors `scripts/hf_upload_scripts/aat_to_hf.py` and exists for
historical convenience inside the pipeline folder.
"""
import pandas as pd
from datasets import Dataset


# Load the raw term export and keep the columns needed for a lightweight dataset.
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

# Restrict notes to English using Getty's language code.
notes_filtered = notes[notes['language_id'] == '70051']
print("\nENGLISH FILTERED NOTES DATAFRAME")
print(notes_filtered.head())


# Keep only preferred terms so one canonical label represents each concept.
df_filtered = df[df['term_preference'] == 'P']
print("\nPREFERRED TERMS FILTERED DATAFRAME")
print(df_filtered.head())
df_filtered = df_filtered.drop(columns=['term_preference'])


# Merge term text with matching English notes.
aat_dataset = pd.merge(df_filtered, notes_filtered, on='term_id', how='left')
print("\nMERGED DATAFRAME")
print(aat_dataset.head())

print(len(aat_dataset))
# Convert the pandas DataFrame to a Hugging Face Dataset
hf_dataset = Dataset.from_pandas(aat_dataset)
print("\nHUGGING FACE DATASET")

# Publish the dataset to the configured public Hugging Face repository.
hf_dataset.push_to_hub("aat-preferred-terms", private=False)
