import streamlit as st
import json
import os
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import umap
from typing import List, Dict, Tuple

def load_data(viz_params: Dict) -> pd.DataFrame:
    """Load and prepare data with configurable visualization parameters"""
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
    
    # Generate embeddings with configurable parameters
    
    # PCA
    pca = PCA(
        n_components=2,
        random_state=42
    )
    df[['PCA1', 'PCA2']] = pca.fit_transform(embeddings_array)
    
    # t-SNE
    tsne = TSNE(
        n_components=2,
        perplexity=viz_params['tsne_perplexity'],
        early_exaggeration=viz_params['tsne_early_exaggeration'],
        learning_rate=viz_params['tsne_learning_rate'],
        n_iter=viz_params['tsne_n_iter'],
        random_state=42
    )
    df[['TSNE1', 'TSNE2']] = tsne.fit_transform(embeddings_array)
    
    # UMAP
    umap_reducer = umap.UMAP(
        n_neighbors=viz_params['umap_n_neighbors'],
        min_dist=viz_params['umap_min_dist'],
        n_components=2,
        metric=viz_params['umap_metric'],
        random_state=42
    )
    df[['UMAP1', 'UMAP2']] = umap_reducer.fit_transform(embeddings_array)
    
    return df

def create_plot(df: pd.DataFrame, plot_type: str, selected_categories: List[str]) -> go.Figure:
    """Create plotly figure based on selected visualization type and categories"""
    
    if plot_type == 'PCA':
        x_col, y_col = 'PCA1', 'PCA2'
        title = 'PCA Visualization of Story Chunks'
    elif plot_type == 't-SNE':
        x_col, y_col = 'TSNE1', 'TSNE2'
        title = 't-SNE Visualization of Story Chunks'
    else:  # UMAP
        x_col, y_col = 'UMAP1', 'UMAP2'
        title = 'UMAP Visualization of Story Chunks'

    fig = go.Figure()
    
    # Base scatter plot
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='markers',
        marker=dict(color='lightgray', size=8),
        text=df['content'],
        hovertemplate='Content: %{text}<br><extra></extra>',
        name='All Points',
        showlegend=False
    ))
    
    # Color scheme
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
    
    for category in selected_categories:
        if category in ['beginning', 'middle', 'leaving', 'after']:
            mask = df['timing'] == category
            if mask.any():
                fig.add_trace(go.Scatter(
                    x=df[mask][x_col],
                    y=df[mask][y_col],
                    mode='markers',
                    marker=dict(color=colors[category], size=8),
                    text=df[mask]['content'],
                    hovertemplate=f'Content: %{{text}}<br>Time: {category}<br><extra></extra>',
                    name=category.title()
                ))
        else:
            column = f'has_{category}'
            if column in df.columns:
                mask = df[column]
                if mask.any():
                    fig.add_trace(go.Scatter(
                        x=df[mask][x_col],
                        y=df[mask][y_col],
                        mode='markers',
                        marker=dict(color=colors[category], size=8),
                        text=df[mask]['content'],
                        hovertemplate=f'Content: %{{text}}<br>Tactic: {category.replace("_", " ").title()}<br><extra></extra>',
                        name=category.replace('_', ' ').title()
                    ))
    
    fig.update_layout(
        title=title,
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
    
    # Sidebar controls for visualization parameters
    st.sidebar.header("Visualization Parameters")
    
    # t-SNE parameters
    st.sidebar.subheader("t-SNE Parameters")
    tsne_params = {
        'tsne_perplexity': st.sidebar.slider(
            "Perplexity (balance between local and global structure)",
            5, 100, 30,
            help="Higher values consider more neighbors (global structure), lower values focus on local structure"
        ),
        'tsne_early_exaggeration': st.sidebar.slider(
            "Early Exaggeration",
            1.0, 50.0, 12.0,
            help="Higher values create more space between clusters"
        ),
        'tsne_learning_rate': st.sidebar.slider(
            "Learning Rate",
            10.0, 1000.0, 200.0,
            help="Higher values make the visualization more spread out"
        ),
        'tsne_n_iter': st.sidebar.slider(
            "Number of Iterations",
            250, 2000, 1000,
            help="More iterations may improve quality but take longer"
        )
    }
    
    # UMAP parameters
    st.sidebar.subheader("UMAP Parameters")
    umap_params = {
        'umap_n_neighbors': st.sidebar.slider(
            "Number of Neighbors",
            2, 200, 15,
            help="Higher values preserve more global structure"
        ),
        'umap_min_dist': st.sidebar.slider(
            "Minimum Distance",
            0.0, 1.0, 0.1,
            help="Lower values create tighter clusters"
        ),
        'umap_metric': st.sidebar.selectbox(
            "Distance Metric",
            ['euclidean', 'manhattan', 'cosine'],
            help="Different ways to measure distance between points"
        )
    }
    
    # Combine all visualization parameters
    viz_params = {**tsne_params, **umap_params}
    
    # Load data with current parameters
    df = load_data(viz_params)
    
    # Visualization type selector
    viz_type = st.sidebar.radio(
        "Select Visualization Type",
        ["PCA", "t-SNE", "UMAP"]
    )
    
    # Category selectors
    st.sidebar.subheader("Categories")
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
    
    selected_categories = time_periods + tactics
    
    # Create and display plot
    fig = create_plot(df, viz_type, selected_categories)
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