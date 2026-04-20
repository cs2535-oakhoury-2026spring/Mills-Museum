"""
Pipeline-local copy of the museum metadata + image upload script.

This file mirrors `scripts/hf_upload_scripts/data_to_hf.py` so the pipeline
folder keeps its publishing helpers close to the rest of the data workflow.
"""
import pandas as pd
from datasets import Dataset, Image
import os
import glob

# Load the spreadsheet that describes museum objects and artists.
df = pd.read_excel('data/metadata/MCAM Object and Artist Records.xlsx', sheet_name='MCAM Object and Artist Records')


located_images = 0
failed_images = 0
failed_images_list = []

# Attempt to resolve one image file for each accession number.
images = []
for accesion_number in df['Accession Number']:

    path = f"data/images/{accesion_number}*.png"
    # some pieces have multiple images, so we use glob to find all matches
    matches = glob.glob(path)

    image_path = ""
    for match in matches:
        following_char = match[len(f"data/images/{accesion_number}")]
        if following_char == '_': # if it is followed by _ we have found the correct image
            image_path = match
            break # prioritize _ images over . images
        if following_char == '.': # if it is followed by . we may have found the correct image
            image_path = match
    
    if os.path.exists(image_path):
        if image_path in [images]:
            print(f"Duplicate image found for Accession Number {accesion_number} : {image_path}")

        images.append(image_path)
        located_images += 1
    else:
        # Preserve the metadata row even if its image could not be found.
        images.append(None)
        failed_images += 1
        failed_images_list.append(accesion_number)

    print(f"\rLocated: {located_images} | Failed: {failed_images} | Total: {len(df)} | Percent: {located_images / len(df) * 100:.2f}%", end="")
print()  # for newline after the loop
print("Failed to locate images for the following Accession Numbers:")
print(failed_images_list)
print()

# Add the resolved image path column near the front for easier inspection.
df.insert(loc=1, column='Image', value=images)

# Display Columns to verify
print(df.columns)
# Display the first 5 rows to verify
print(df.head())

for column in df.columns:
    if column != "Image":
        # Normalize blank-like spreadsheet values into proper nulls.
        df[column] = df[column].astype(str)
        df[column] = df[column].replace(['None', 'nan', 'NaN', ''], None)



# Upload the table as a hub dataset and mark the image column accordingly.
hf_dataset = Dataset.from_pandas(df)

hf_dataset = hf_dataset.cast_column("Image", Image())
hf_dataset.push_to_hub("KeeganC/mcam-object-artist-records", private=False)
