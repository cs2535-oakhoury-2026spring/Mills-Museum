import pandas as pd
from datasets import Dataset, Image
import os
import glob

# Load the Excel file
df = pd.read_excel('data/metadata/MCAM Object and Artist Records.xlsx', sheet_name='MCAM Object and Artist Records')


located_images = 0
failed_images = 0
failed_images_list = []

# finds images based on Accesion number and adds it to a new column
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
        images.append(None)  # or handle missing images as needed
        failed_images += 1
        failed_images_list.append(accesion_number)

    print(f"\rLocated: {located_images} | Failed: {failed_images} | Total: {len(df)} | Percent: {located_images / len(df) * 100:.2f}%", end="")
print()  # for newline after the loop
print("Failed to locate images for the following Accession Numbers:")
print(failed_images_list)
print()

# Inserts images colunm as the second column
df.insert(loc=1, column='Image', value=images)

# Display Columns to verify
print(df.columns)
# Display the first 5 rows to verify
print(df.head())

for column in df.columns:
    if column != "Image":
        # ensure empty values are stored as None
        df[column] = df[column].astype(str)
        df[column] = df[column].replace(['None', 'nan', 'NaN', ''], None)



# convert to Hugging Face Dataset and push to hub
hf_dataset = Dataset.from_pandas(df)

hf_dataset = hf_dataset.cast_column("Image", Image())
hf_dataset.push_to_hub("KeeganC/mcam-object-artist-records", private=False)