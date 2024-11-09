import json
import os
import google.generativeai as genai
from typing import Dict, List

# Get the path to stories.json in parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stories_path = os.path.join(parent_dir, 'stories_smaller_chunks.json')

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Google API key not found in environment variables")

genai.configure(api_key=api_key)

def get_embedding(content: str, title: str = "Embedding") -> List[float]:
    """Get embedding for a piece of content"""
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=content,
        task_type="retrieval_document",
        title=title
    )
    return result['embedding']

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
        print(f"\nProcessing story {story_index + 1}/{len(data['stories'])}")
        
        # # Generate embedding for main content if not already done
        # if 'content' in story and 'embedding' not in story:
        #     try:
        #         print("Generating embedding for main content...")
        #         story['embedding'] = get_embedding(
        #             story['content'],
        #             f"Story {story_index + 1} Main Content"
        #         )
        #         save_progress(data)
        #         print("Main content embedding generated and saved")
        #     except Exception as e:
        #         print(f"Error generating main content embedding: {str(e)}")
        #         continue

        # Process each chunk
        if 'chunks' in story:
            for chunk_index, chunk in enumerate(story['chunks']):
                if 'embedding' not in chunk:
                    try:
                        print(f"Generating embedding for chunk {chunk_index + 1}/{len(story['chunks'])}...")
                        chunk['embedding'] = get_embedding(
                            chunk['content'],
                            f"Story {story_index + 1} Chunk {chunk_index + 1}"
                        )
                        save_progress(data)
                        print(f"Chunk {chunk_index + 1} embedding generated and saved")
                    except Exception as e:
                        print(f"Error processing chunk {chunk_index + 1}: {str(e)}")
                        continue
                else:
                    print(f"Chunk {chunk_index + 1} already has embedding, skipping...")

    print("\nAll embeddings generated!")

if __name__ == "__main__":
    main()