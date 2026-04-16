"""
Upload the local ChromaDB vector store to Hugging Face as a dataset repo.

Usage:
    python scripts/hf_upload_scripts/vdb_to_hf.py

Requires: pip install huggingface_hub
Must be logged in: huggingface-cli login
"""

from huggingface_hub import HfApi

REPO_ID = "KeeganC/mcam-vdb"
VDB_DIR = "src/data/VDB"

api = HfApi()

# Create the dataset repo (no-op if it already exists)
api.create_repo(repo_id=REPO_ID, repo_type="dataset", exist_ok=True)

# Upload the entire VDB directory
api.upload_folder(
    folder_path=VDB_DIR,
    repo_id=REPO_ID,
    repo_type="dataset",
)

print(f"VDB uploaded to https://huggingface.co/datasets/{REPO_ID}")
