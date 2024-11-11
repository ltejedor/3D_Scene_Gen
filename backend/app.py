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
import PIL.Image
import requests
from io import BytesIO
from typing import Tuple

import google.generativeai as genai

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

def get_image_from_url(url: str):
    """Downloads and returns an image as a PIL Image."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return PIL.Image.open(BytesIO(response.content))
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {e}")
        return None

async def rate_object_fit(url: str, object_type: str, theme: str) -> Tuple[float, str]:
    """Rate how well an object fits the theme and its functionality."""
    try:
        image = get_image_from_url(url)
        if not image:
            return (0, "Failed to load image")

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise Exception("Google API key not found")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        prompt = f"""
        Rate this {object_type} for a {theme} room on a scale of 1-5:
        1. How well does it fit the {theme} theme? (0-5)
        2. How well does it function as a {object_type}? (0-5)

        Format your response exactly like this:
        3.5
        Good match for theme, proper functionality as a {object_type}
        """

        response = model.generate_content([prompt, image])
        lines = response.text.strip().split('\n', 1)
        rating = float(lines[0])
        explanation = lines[1] if len(lines) > 1 else ""
        
        return (rating, explanation)
        
    except Exception as e:
        logger.error(f"Error rating object: {e}")
        return (0, f"Error: {str(e)}")

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
    

@app.post("/gemini_call")
async def gemini_call(request: Request) -> Dict:
    """
    Endpoint to prompt Gemini API.
    Expects a JSON body with a "prompt" field.
    Returns the Gemini response.
    """
    try:
        # Get the request body
        body = await request.json()
        prompt = body.get("prompt")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Configure Gemini with API key from environment variables
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="Google API key not found in environment variables"
            )

        genai.configure(api_key=api_key)
        
        # Initialize the model and generate response
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="You are a cat. Your name is Neko.")
        response = model.generate_content(prompt)
        
        # Return the response
        return {
            "status": "success",
            "response": response.text
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )
    
@app.get("/initialize_scene")
async def initialize_scene():
    """Initialize the scene with theme-appropriate objects."""
    try:
        # Select random theme
        themes = ["modern minimalist", "cozy cottage", "vintage aesthetic", 
                 "industrial chic", "bohemian retreat"]
        theme = random.choice(themes)
        logger.info(f"Selected theme: {theme}")
        # Define all objects and their positions
        objects = [
            # Original furniture
            {
                "keyword": "bookshelf",
                "position": {"x": 3, "y": 0, "z": -1},
                "rotation": {"y": 0}
            },
            {
                "keyword": "window",
                "position": {"x": 0, "y": 1.5, "z": -3},
                "rotation": {"y": 0}
            },
            {
                "keyword": "mirror",
                "position": {"x": -3, "y": 1.5, "z": -1},
                "rotation": {"y": 90}
            },
            {
                "keyword": "couch",
                "position": {"x": -3, "y": 0, "z": -1},
                "rotation": {"y": 90}
            },
            {
                "keyword": "coffee table",
                "position": {"x": -2, "y": 0, "z": 0},
                "rotation": {"y": 0}
            },
            # New furniture and objects
            {
                "keyword": "gift",
                "position": {"x": -2, "y": 0.5, "z": 0},  # On coffee table
                "rotation": {"y": 0}
            },
            {
                "keyword": "side table",
                "position": {"x": 3, "y": 0, "z": -2.5},  # Back right
                "rotation": {"y": 0}
            },
            {
                "keyword": "lamp",
                "position": {"x": 3, "y": 0.8, "z": -2.5},  # On the side table
                "rotation": {"y": 0}
            },
            # Objects near bookshelf
            {
                "keyword": "cards",
                "position": {"x": 2.7, "y": 0, "z": -0.5},
                "rotation": {"y": 45}
            },
            {
                "keyword": "radio",
                "position": {"x": 3.3, "y": 0, "z": -0.5},
                "rotation": {"y": -20}
            },
            {
                "keyword": "notebook",
                "position": {"x": 2.5, "y": 0, "z": -0.7},
                "rotation": {"y": 15}
            },
            {
                "keyword": "telephone",
                "position": {"x": 3.1, "y": 0, "z": -0.7},
                "rotation": {"y": -10}
            }
        ]

        scene_objects = []
        
        # Process each object
        for item in objects:
            # Get 5 random matching objects
            relevant_uids = []
            for uid, annotation in annotations.items():
                name = annotation.get('name', '').lower()
                tags = [tag['name'].lower() for tag in annotation.get('tags', [])]
                categories = [cat['name'].lower() for cat in annotation.get('categories', [])]
                
                if (item["keyword"] in name or 
                    any(item["keyword"] in tag for tag in tags) or 
                    any(item["keyword"] in category for category in categories)):
                    relevant_uids.append(uid)

            if not relevant_uids:
                logger.warning(f"No objects found for {item['keyword']}")
                continue

            # Take up to 5 random objects
            sample_uids = random.sample(relevant_uids, min(5, len(relevant_uids)))
            
            # Rate each object
            best_rating = 0
            best_uid = None
            best_explanation = ""
            
            for uid in sample_uids:
                # Get first thumbnail URL
                thumbnails = annotations[uid].get('thumbnails', {}).get('images', [])
                if not thumbnails:
                    continue
                    
                image_url = thumbnails[0].get('url')
                if not image_url:
                    continue
                
                rating, explanation = await rate_object_fit(
                    image_url, 
                    item["keyword"],
                    theme
                )
                
                if rating > best_rating:
                    best_rating = rating
                    best_uid = uid
                    best_explanation = explanation

            # If we found a good object, add it to the scene
            if best_uid:
                downloaded_path = download_object(best_uid)
                if not downloaded_path:
                    continue

                relative_path = os.path.relpath(downloaded_path, DOWNLOAD_DIR)
                file_url = f"/downloads/{relative_path.replace(os.sep, '/')}"
                
                object_annotation = annotations.get(best_uid, {})
                scene_objects.append({
                    "uid": best_uid,
                    "name": object_annotation.get('name', ''),
                    "fileURL": file_url,
                    "position": item["position"],
                    "rotation": item["rotation"],
                    "type": item["keyword"],
                    "rating": best_rating,
                    "explanation": best_explanation
                })

        return JSONResponse(content={
            "theme": theme,
            "objects": scene_objects
        })

    except Exception as e:
        logger.error(f"Error initializing scene: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to initialize scene")