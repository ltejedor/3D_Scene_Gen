import json
import os
import time
from typing import Dict, List
import google.generativeai as genai
from ratelimit import limits, sleep_and_retry

# Get the path to stories.json in parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stories_path = os.path.join(parent_dir, 'stories_smaller_chunks.json')

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Google API key not found in environment variables")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Rate limiting decorator: 15 calls per minute
@sleep_and_retry
@limits(calls=15, period=60)
def analyze_chunk(chunk_content: str, full_story: str) -> str:
    prompt = f"""Given the following section of text from a domestic abuse story, determine at what phase of the abusive relationship this chunk takes place. The possible phases are:
- "beginning": Early stages of the relationship
- "middle": During the ongoing abusive relationship
- "leaving": When the victim is in the process of leaving or deciding to leave
- "after": After leaving the relationship has ended and they've started to move on and heal

The goal is to categorize types of abusive tactics to help educate others on the tactics of abusers.
Analyze this specific section in the context of the full story.

Full story for context:
{full_story}

Specific section to analyze and label:
{chunk_content}

Reply with ONLY ONE WORD - either "beginning", "middle", "leaving", or "after"."""

    response = model.generate_content(prompt)
    return response.text.strip().lower()

def save_progress(data: Dict) -> None:
    """Save the current state to the JSON file"""
    with open(stories_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)

def main():
    # Load the stories
    with open(stories_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Process each story
    for story_index, story in enumerate(data['stories']):
        if 'content' not in story or 'chunks' not in story:
            continue

        print(f"\nProcessing story {story_index + 1}/{len(data['stories'])}")
        
        # Process each chunk
        for chunk_index, chunk in enumerate(story['chunks']):
            # Skip if already analyzed
            if 'timing' in chunk:
                print(f"Chunk {chunk_index + 1} already analyzed, skipping...")
                continue

            try:
                print(f"Analyzing chunk {chunk_index + 1}/{len(story['chunks'])}...")
                chunk['timing'] = analyze_chunk(chunk['content'], story['content'])
                
                # Save progress after each chunk
                save_progress(data)
                print(f"Chunk {chunk_index + 1} timing: {chunk['timing']}")
                
            except Exception as e:
                print(f"Error processing chunk {chunk_index + 1}: {str(e)}")
                # Save progress even if there's an error
                save_progress(data)
                continue

if __name__ == "__main__":
    main()