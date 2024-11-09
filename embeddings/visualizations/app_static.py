import streamlit as st
import json
import os
import numpy as np
from sklearn.manifold import TSNE
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict

def load_data() -> pd.DataFrame:
    """Load and prepare data with optimized t-SNE parameters"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stories_path = os.path.join(parent_dir, 'stories_smaller_chunks.json')
    
    with open(stories_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    rows = []
    embeddings = []
    
    for story_idx, story in enumerate(data['stories']):
        for chunk_idx, chunk in enumerate(story['chunks']):
            if 'embedding' not in chunk:
                continue
                
            row = {
                'story_index': story_idx,
                'chunk_index': chunk_idx,
                'content': chunk['content'],
                'timing': chunk.get('timing', 'unknown'),
            }
            
            if 'manipulation_tactics' in chunk:
                for tactic, score in chunk['manipulation_tactics'].items():
                    row[f'has_{tactic}'] = bool(score >= 2)
            
            rows.append(row)
            embeddings.append(chunk['embedding'])
    
    df = pd.DataFrame(rows)
    embeddings_array = np.array(embeddings)
    
    # t-SNE with optimized parameters
    tsne = TSNE(
        n_components=2,
        perplexity=46,
        early_exaggeration=12,
        learning_rate=200,
        n_iter=1200,
        random_state=42
    )
    df[['TSNE1', 'TSNE2']] = tsne.fit_transform(embeddings_array)
    
    return df

def create_plot(df: pd.DataFrame, selected_categories: List[str]) -> go.Figure:
    """Create plotly figure with t-SNE visualization"""
    fig = go.Figure()
    
    # Base scatter plot with all points in gray
    fig.add_trace(go.Scatter(
        x=df['TSNE1'],
        y=df['TSNE2'],
        mode='markers',
        marker=dict(color='lightgray', size=8),
        text=df['content'],
        hovertemplate='Content: %{text}<br><extra></extra>',
        name='All Points',
        showlegend=False
    ))
    
    # Color scheme for different categories
    colors = {
        'beginning': '#ff7f0e',
        'middle': '#2ca02c',
        'leaving': '#d62728',
        'after': '#9467bd',
        'gaslighting': '#e377c2',
        'silent_treatment': '#7f7f7f',
        'love_bombing': '#bcbd22',
        'projection': '#17becf',
        'triangulation': '#1f77b4'
    }
    
    # Add selected categories
    for category in selected_categories:
        if category in ['beginning', 'middle', 'leaving', 'after']:
            # Time period categories
            mask = df['timing'] == category
            if mask.any():
                fig.add_trace(go.Scatter(
                    x=df[mask]['TSNE1'],
                    y=df[mask]['TSNE2'],
                    mode='markers',
                    marker=dict(color=colors[category], size=8),
                    text=df[mask]['content'],
                    hovertemplate=f'Content: %{{text}}<br>Time: {category}<br><extra></extra>',
                    name=category.title()
                ))
        else:
            # Manipulation tactics
            column = f'has_{category}'
            if column in df.columns:
                mask = df[column]
                if mask.any():
                    fig.add_trace(go.Scatter(
                        x=df[mask]['TSNE1'],
                        y=df[mask]['TSNE2'],
                        mode='markers',
                        marker=dict(color=colors[category], size=8),
                        text=df[mask]['content'],
                        hovertemplate=f'Content: %{{text}}<br>Tactic: {category.replace("_", " ").title()}<br><extra></extra>',
                        name=category.replace('_', ' ').title()
                    ))
    
    # Update layout
    fig.update_layout(
        title='t-SNE Visualization of Story Chunks',
        template='plotly_white',
        height=700,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        hovermode='closest'
    )
    
    return fig

def main():
    st.set_page_config(layout="wide")
    st.title("Story Chunk Visualization")
    
    # Load data with optimized parameters
    df = load_data()
    
    # Sidebar controls
    st.sidebar.header("Categories")
    
    # Category selectors
    time_periods = st.sidebar.multiselect(
        "Select Time Periods",
        ["beginning", "middle", "leaving", "after"],
        default=[]
    )
    
    tactics = st.sidebar.multiselect(
        "Select Manipulation Tactics",
        ["gaslighting", "silent_treatment", "love_bombing", "projection", "triangulation"],
        default=[]
    )
    
    # Combine selected categories
    selected_categories = time_periods + tactics
    
    # Create and display plot
    fig = create_plot(df, selected_categories)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display statistics
    st.sidebar.subheader("Statistics")
    if selected_categories:
        for category in selected_categories:
            if category in ['beginning', 'middle', 'leaving', 'after']:
                count = (df['timing'] == category).sum()
                st.sidebar.text(f"{category.title()}: {count} chunks")
            else:
                column = f'has_{category}'
                if column in df.columns:
                    count = df[column].sum()
                    st.sidebar.text(f"{category.replace('_', ' ').title()}: {count} chunks")

if __name__ == "__main__":
    main()