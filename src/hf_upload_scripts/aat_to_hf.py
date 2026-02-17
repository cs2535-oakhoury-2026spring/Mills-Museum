import pandas as pd
from datasets import Dataset


# Load the TSV file
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

# 70051 means English language note, we only want those
notes_filtered = notes[notes['language_id'] == '70051']
print("\nENGLISH FILTERED NOTES DATAFRAME")
print(notes_filtered.head())


# P means preferred term note, we only want those
df_filtered = df[df['term_preference'] == 'P']
print("\nPREFERRED TERMS FILTERED DATAFRAME")
print(df_filtered.head())
df_filtered = df_filtered.drop(columns=['term_preference'])


# Merge the notes into the main dataframe based on term_id
aat_dataset = pd.merge(df_filtered, notes_filtered, on='term_id', how='left')
print("\nMERGED DATAFRAME")
print(aat_dataset.head())

print(len(aat_dataset))
# Convert the pandas DataFrame to a Hugging Face Dataset
hf_dataset = Dataset.from_pandas(aat_dataset)
print("\nHUGGING FACE DATASET")
# upload to Hugging Face Hub
hf_dataset.push_to_hub("aat-preferred-terms", private=False)