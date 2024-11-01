# backend/app.py

import os
import shutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import openai
import pandas as pd
import objaverse.xl as oxl
from typing import Optional, List
import logging
import traceback

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Configure CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI API (Not used in keyword search but kept for potential future use)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Directory to download Objaverse objects
DOWNLOAD_DIR = os.path.expanduser("~/.objaverse")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Mount the download directory to serve static files
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")

# Global variable to store annotations
annotations_df = pd.DataFrame()

# Load annotations on startup
@app.on_event("startup")
def setup():
    global annotations_df
    try:
        logger.info("Loading Objaverse annotations...")
        annotations_df = oxl.get_alignment_annotations(download_dir=DOWNLOAD_DIR)
        logger.info(f"Loaded {len(annotations_df)} annotations.")
    except Exception as e:
        logger.error(f"Error loading annotations: {e}")
        annotations_df = pd.DataFrame()  # Empty DataFrame in case of failure


def find_relevant_object_keyword(prompt: str) -> Optional[pd.Series]:
    """
    Perform a keyword-based search to find a relevant object.
    Filters objects to include only those with fileType 'obj'.
    Searches within 'fileIdentifier' first, then 'metadata' if no match is found.
    Returns a single object if found, else selects a random one.
    """
    if annotations_df.empty:
        logger.error("Annotations DataFrame is empty.")
        return None
    
    # Lowercase the prompt (assuming it's a single word)
    keyword = prompt.lower()
    
    # Search in 'fileIdentifier' first
    annotations_df['metadata_str'] = annotations_df['metadata'].astype(str).str.lower()
    mask_file_identifier = (
        (annotations_df['fileType'].str.lower() == 'obj') &  # Filter for 'obj' fileType
        annotations_df['metadata_str'].str.contains(keyword, na=False)
    )

    # Filter the DataFrame based on 'fileIdentifier'
    filtered = annotations_df[mask_file_identifier]

    # If no results found in 'fileIdentifier', search in 'metadata'
    if filtered.empty:
        print("no metadata found")
        # Assuming 'metadata' is a dictionary stored as a string
        mask_metadata = (
            (annotations_df['fileType'].str.lower() == 'obj') & 
            annotations_df['fileIdentifier'].str.contains(keyword, na=False)
        )
        filtered = annotations_df[mask_metadata]

    # If results found, return the first match
    if not filtered.empty:
        selected_obj = filtered.iloc[0]
        logger.info(f"Found object matching the keyword in 'fileIdentifier' or 'metadata': {selected_obj['fileIdentifier']}")
        return selected_obj
    else:
        # If no matches, select a random 'obj' object
        logger.warning(f"No relevant 'obj' objects found for keyword '{keyword}'. Selecting a random 'obj' object.")
        random_objs = annotations_df[annotations_df['fileType'].str.lower() == 'obj']
        if not random_objs.empty:
            selected_obj = random_objs.sample(n=1).iloc[0]
            logger.info(f"Selected random object: {selected_obj['fileIdentifier']}")
            return selected_obj
        else:
            logger.error("No 'obj' fileType objects available in the dataset.")
            return None
        

def download_object(obj: pd.Series) -> Optional[str]:
    """
    Download a single Objaverse object and return its local path.
    """
    try:
        objects_to_download = pd.DataFrame([obj])
        downloaded = oxl.download_objects(objects=objects_to_download, save_repo_format="files")
        # The returned 'downloaded' is a dict mapping fileIdentifier to local paths
        file_identifier = obj['fileIdentifier']
        local_path = downloaded.get(file_identifier)
        if local_path and os.path.exists(local_path):
            logger.info(f"Successfully downloaded object: {file_identifier} to {local_path}")
            return local_path
        else:
            logger.warning(f"Download failed or file does not exist for object: {file_identifier}")
            return None
    except Exception as e:
        logger.error(f"Error downloading object {obj['fileIdentifier']}: {e}")
        logger.error(traceback.format_exc())
        return None

@app.post("/generate_scene")
async def generate_scene(request: Request):
    """
    Endpoint to generate a 3D scene based on a user prompt.
    Expects a JSON payload with a 'prompt' field.
    """
    try:
        data = await request.json()
        prompt = data.get("prompt", "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required.")

        # Step 1: Perform keyword-based search
        selected_obj = find_relevant_object_keyword(prompt)
        print(selected_obj)
        if selected_obj is None:
            raise HTTPException(status_code=404, detail="No 'obj' type objects available to generate the scene.")

        # Step 2: Attempt to download the selected object
        downloaded_path = download_object(selected_obj)
        if not downloaded_path:
            raise HTTPException(status_code=500, detail="Failed to download the selected object.")

        # Step 3: Prepare data to send to frontend
        relative_path = os.path.relpath(downloaded_path, DOWNLOAD_DIR)
        file_url = f"/downloads/{relative_path.replace(os.sep, '/')}"  

        response = {
            "fileIdentifier": selected_obj['fileIdentifier'],
            "source": selected_obj['source'],
            "license": selected_obj['license'],
            "fileType": selected_obj['fileType'],
            "fileURL": file_url,
            "metadata": selected_obj['metadata']
        }

        return JSONResponse(content=response)

    except HTTPException as he:
        logger.error(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in generate_scene: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
