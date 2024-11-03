# backend/app.py

import os
import shutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import openai
import objaverse
from typing import Optional, List, Dict
import logging
import traceback
import random

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

# Global variable to store UIDs and annotations
uids = []
annotations = {}
lvis_annotations = {}

# Load UIDs and annotations on startup
@app.on_event("startup")
def setup():
    global uids, annotations, lvis_annotations
    try:
        logger.info("Loading Objaverse UIDs...")
        uids = objaverse.load_uids()
        logger.info(f"Loaded {len(uids)} UIDs.")
        
        logger.info("Loading Objaverse annotations...")
        annotations = objaverse.load_annotations()
        logger.info(f"Loaded annotations for {len(annotations)} objects.")
        
        logger.info("Loading LVIS annotations...")
        lvis_annotations = objaverse.load_lvis_annotations()
        logger.info(f"Loaded LVIS annotations for {len(lvis_annotations)} categories.")
        
    except Exception as e:
        logger.error(f"Error loading Objaverse data: {e}")


def find_relevant_object_keyword(prompt: str) -> Optional[str]:
    """
    Perform a keyword-based search to find a relevant object.
    Returns a single object UID if found, else selects a random one.
    """
    if not uids:
        logger.error("No objects found.")
        return None
    
    # Lowercase the prompt
    keyword = prompt.lower()
    
    # Search in object names and tags
    relevant_uids = []
    for uid, annotation in annotations.items():
        name = annotation.get('name', '').lower()
        tags = [tag['name'].lower() for tag in annotation.get('tags', [])]
        categories = [cat['name'].lower() for cat in annotation.get('categories', [])]
        
        if (keyword in name or 
            any(keyword in tag for tag in tags) or 
            any(keyword in category for category in categories)):
            relevant_uids.append(uid)
    
    # If results found, return a random one from the relevant set
    if relevant_uids:
        selected_uid = random.choice(relevant_uids)
        logger.info(f"Found object matching the keyword: {selected_uid}")
        return selected_uid
    else:
        # If no matches, select a random object
        logger.warning(f"No relevant objects found for keyword '{keyword}'. Selecting a random object.")
        return random.choice(uids)

def download_object(uid: str) -> Optional[str]:
    """
    Download a single Objaverse object and return its local path.
    """
    try:
        objects_to_download = {uid: annotations[uid]}
        downloaded = objaverse.load_objects(uids=[uid])
        local_path = downloaded.get(uid)
        if local_path and os.path.exists(local_path):
            logger.info(f"Successfully downloaded object: {uid} to {local_path}")
            return local_path
        else:
            logger.warning(f"Download failed or file does not exist for object: {uid}")
            return None
    except Exception as e:
        logger.error(f"Error downloading object {uid}: {e}")
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
        selected_uid = find_relevant_object_keyword(prompt)
        if selected_uid is None:
            raise HTTPException(status_code=404, detail="No objects available to generate the scene.")

        # Step 2: Attempt to download the selected object
        downloaded_path = download_object(selected_uid)
        if not downloaded_path:
            raise HTTPException(status_code=500, detail="Failed to download the selected object.")

        # Step 3: Prepare data to send to frontend
        relative_path = os.path.relpath(downloaded_path, DOWNLOAD_DIR)
        file_url = f"/downloads/{relative_path.replace(os.sep, '/')}"
        
        object_annotation = annotations.get(selected_uid, {})
        print(object_annotation)
        response = {
            "uid": selected_uid,
            "name": object_annotation.get('name', ''),
            "license": object_annotation.get('license', ''),
            "fileURL": file_url,
            "tags": [tag['name'] for tag in object_annotation.get('tags', [])],
            "categories": [cat['name'] for cat in object_annotation.get('categories', [])]
        }

        return JSONResponse(content=response)

    except HTTPException as he:
        logger.error(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in generate_scene: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")