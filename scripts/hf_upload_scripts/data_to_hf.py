"""
Build a Hugging Face dataset from museum metadata plus local image files.

This script matches object records to image files using accession numbers,
adds the resolved image path as a dataset column, then publishes the combined
table to the Hugging Face Hub.
"""
import pandas as pd
from datasets import Dataset, Image
import os
import glob

# Load the museum spreadsheet that contains object and artist metadata.
df = pd.read_excel('data/metadata/MCAM Object and Artist Records.xlsx', sheet_name='MCAM Object and Artist Records')


located_images = 0
failed_images = 0
failed_images_list = []

# Look for an image whose filename begins with the accession number.
# Some artworks have multiple related image files, so the script prefers a
# file with an underscore suffix over one that ends immediately in `.png`.
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
        # Keep the row even when the image is missing so the upload still
        # reflects the metadata coverage honestly.
        images.append(None)
        failed_images += 1
        failed_images_list.append(accesion_number)

    print(f"\rLocated: {located_images} | Failed: {failed_images} | Total: {len(df)} | Percent: {located_images / len(df) * 100:.2f}%", end="")
print()  # for newline after the loop
print("Failed to locate images for the following Accession Numbers:")
print(failed_images_list)
print()

# Insert the resolved image paths near the front of the table for readability.
df.insert(loc=1, column='Image', value=images)

# Display Columns to verify
print(df.columns)
# Display the first 5 rows to verify
print(df.head())

for column in df.columns:
    if column != "Image":
        # Convert spreadsheet-style empty values into proper nulls before upload.
        df[column] = df[column].astype(str)
        df[column] = df[column].replace(['None', 'nan', 'NaN', ''], None)



# Convert the pandas table to a Hugging Face dataset, then tell the hub that
# the `Image` column should be treated as actual image data.
hf_dataset = Dataset.from_pandas(df)

hf_dataset = hf_dataset.cast_column("Image", Image())
hf_dataset.push_to_hub("KeeganC/mcam-object-artist-records", private=False)
