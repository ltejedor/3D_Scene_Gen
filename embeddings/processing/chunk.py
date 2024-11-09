# Recursive Chunking
# First process step
import json
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Get the path to stories.json in parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stories_path = os.path.join(parent_dir, 'stories_smaller_chunks.json')

# Initialize text splitter with smarter separators
text_splitter = RecursiveCharacterTextSplitter(
    # Define separators in order of priority
    separators=["\n\n", "\n", ".", "!", "?", ";"],  # Split first on paragraphs, then sentences
    chunk_size=400, 
    chunk_overlap=35,  # Smaller overlap since we're splitting on natural boundaries
    length_function=len,
    is_separator_regex=False,
    keep_separator=True  # Keep the separator at the end of each chunk
)

# Read the stories file
with open(stories_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Process each story in the stories array
for story in data['stories']:
    if 'content' in story:
        # Split the content into chunks
        chunks = text_splitter.create_documents([story['content']])
        
        # Convert chunks to the desired format
        story['chunks'] = [
            {'content': chunk.page_content.strip()}  # Strip any extra whitespace
            for chunk in chunks
        ]

# Save the updated stories back to the file
with open(stories_path, 'w', encoding='utf-8') as file:
    json.dump(data, file, indent=2)

# Optional: Print first few chunks of first story to check the splitting
if len(data['stories']) > 0 and 'chunks' in data['stories'][0]:
    print("\nExample chunks from first story:")
    for i, chunk in enumerate(data['stories'][0]['chunks'][:3]):
        print(f"\nChunk {i + 1}:")
        print(chunk['content'])
        print("-" * 80)