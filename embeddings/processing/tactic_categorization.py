import json
import os
import google.generativeai as genai
from typing import Dict, List
from ratelimit import limits, sleep_and_retry

# Get the path to stories.json in parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stories_path = os.path.join(parent_dir, 'stories_smaller_chunks.json')

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Google API key not found in environment variables")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-pro", system_instruction="You are an expert in relationships, psychology and manipulation techniques. You're putting together educational materials to help people identify these techniques in their own lives.")

TACTICS = {
    "gaslighting": {
        "examples": [
            "Telling a partner 'You're just being paranoid'",
            "Insisting events didn't happen",
            "Denying discussions or agreements made previously",
            "Telling an employee 'I never said that' when they remember differently"
        ]
    },
    "silent_treatment": {
        "examples": [
            "Ignoring a partner for days",
            "Leaving a room each time they speak",
            "Ignoring emails or messages for days",
            "Avoiding interaction as a form of punishment"
        ]
    },
    "love_bombing": {
        "examples": [
            "Constantly giving compliments to win trust",
            "Showering with gifts",
            "Constantly praising an employee to build dependency",
            "Offering excessive praise to manipulate trust"
        ]
    },
    "projection": {
        "examples": [
            "Accusing partner of cheating",
            "Telling them they are secretive",
            "Accusing someone of bad work habits they themselves have",
            "Projecting personal frustrations by accusing others"
        ]
    },
    "triangulation": {
        "examples": [
            "Saying 'Even my friend agrees' to sway opinions",
            "Inviting a third person to side with them in arguments",
            "Discussing another employee's performance to create rivalries",
            "Creating triangles by discussing issues with third parties"
        ]
    }
}

# Rate limiting decorator: 15 calls per minute
# @sleep_and_retry
# @limits(calls=15, period=60)
def analyze_single_tactic(chunk_content: str, tactic: str, examples: List[str]) -> int:
    examples_text = "\n".join(f"- {example}" for example in examples)
    
    prompt = f"""Analyze this story of an abusive relationship for signs of {tactic}. 

Define {tactic} based on the following examples:
{examples_text}
    
Rate from 0-3 how strongly this manipulation tactic appears (0 = not present, 1 = slightly present, 2 = moderately present, 3 = strongly present). This is for educational purposes.

Assume most snippets will not have this tactic present, since these are only parts of a larger story. Only rate 2 or 3 if there is strong evidence of this particular tactic in the text that would help another person identify it in the future.

Story to analyze:
{chunk_content}

Respond with ONLY a single number (0, 1, 2, or 3)."""

    response = model.generate_content(prompt)
    return int(response.text.strip())

def save_progress(data: Dict) -> None:
    """Save the current state to the JSON file"""
    with open(stories_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)

def analyze_tactic_for_all_chunks(tactic_name: str, data: Dict) -> Dict:
    print(f"\nAnalyzing {tactic_name}...")
    
    tactic_data = TACTICS[tactic_name]
    
    # Process each story
    for story_index, story in enumerate(data['stories']):
        if 'content' not in story or 'chunks' not in story:
            continue

        print(f"\nProcessing story {story_index + 1}/{len(data['stories'])}")
        
        # Process each chunk
        for chunk_index, chunk in enumerate(story['chunks']):
            # Initialize manipulation_tactics if it doesn't exist
            if 'manipulation_tactics' not in chunk:
                chunk['manipulation_tactics'] = {}
                
            # Skip if this tactic has already been analyzed for this chunk
            if tactic_name in chunk['manipulation_tactics']:
                print(f"Chunk {chunk_index + 1} already analyzed for {tactic_name}, skipping...")
                continue

            try:
                print(f"Analyzing chunk {chunk_index + 1}/{len(story['chunks'])} for {tactic_name}...")
                rating = analyze_single_tactic(
                    chunk['content'], 
                    tactic_name, 
                    tactic_data['examples']
                )
                
                # Save the rating
                chunk['manipulation_tactics'][tactic_name] = rating
                
                # Save progress after each chunk
                save_progress(data)
                print(f"Chunk {chunk_index + 1} {tactic_name} rating: {rating}")
                
            except Exception as e:
                print(f"Error processing chunk {chunk_index + 1}: {str(e)}")
                # Save progress even if there's an error
                save_progress(data)
                continue
    
    return data

def main():
    # Load the stories
    with open(stories_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Process each tactic sequentially
    for tactic_name in TACTICS.keys():
        print(f"\nStarting analysis for {tactic_name}...")
        data = analyze_tactic_for_all_chunks(tactic_name, data)
        print(f"Completed analysis for {tactic_name}")
    
    print("\nAnalysis complete for all tactics!")

if __name__ == "__main__":
    main()