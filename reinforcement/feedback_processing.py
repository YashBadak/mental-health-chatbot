import faiss
import numpy as np
import sqlite3
import pandas as pd
import os

# Paths
INPUT_FILE = "data/new_feedback.csv"
OUTPUT_FILE = "data/processed_feedback.csv"

# Function to process the feedback
def process_feedback():
    """
    Reads the raw feedback CSV, cleans the data, and saves it to a new file
    without changing the essential column names.
    """
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    try:
        raw_df = pd.read_csv(INPUT_FILE)
        
        if raw_df.empty:
            print("Feedback file is empty. No data to process.")
            # Still, we write an empty file with headers to ensure the next step runs
            pd.DataFrame(columns=['input_text', 'response_text', 'rating']).to_csv(OUTPUT_FILE, index=False)
            return

        # Ensure required columns exist before processing
        required_cols = ['input_text', 'response_text', 'rating']
        if not all(col in raw_df.columns for col in required_cols):
            print(f"Error: Input file must contain columns: {required_cols}")
            return

        # Clean the data by stripping whitespace from text fields
        processed_df = raw_df.copy()
        processed_df['input_text'] = processed_df['input_text'].str.strip()
        processed_df['response_text'] = processed_df['response_text'].str.strip()

        # --- FIX: We are no longer renaming the columns ---
        # Select the columns to ensure order and save to the output file
        final_df = processed_df[processed_df.columns.intersection(
            ['user_id', 'input_text', 'response_text', 'rating', 'reward']
        )]
        
        final_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Feedback processed and saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An error occurred during feedback processing: {e}")

if __name__ == "__main__":
    process_feedback()

# Store feedback in SQLite database (for simplicity)
def store_feedback_in_db(feedback: str, sentiment: str, user_id: str) -> None:
    """
    Stores valid feedback in the SQLite database.
    """
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            feedback_id INTEGER PRIMARY KEY,
            user_id TEXT,
            feedback TEXT,
            sentiment TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT INTO feedbacks (user_id, feedback, sentiment)
        VALUES (?, ?, ?)
    ''', (user_id, feedback, sentiment))
    
    conn.commit()
    conn.close()

# Update FAISS embeddings with new feedback
def update_faiss_embeddings(feedback: str, sentiment: str) -> None:
    """
    Updates the FAISS embeddings with the new feedback.
    """
    # This is a placeholder for FAISS update process
    # Example: assuming you have pre-existing embeddings in 'embedding_model'
    embedding_model = get_embedding_model()  # Fetch your model
    embedding = embedding_model.encode([feedback])
    
    # Add new feedback embedding to FAISS index
    index = load_faiss_index()  # Load your existing FAISS index
    index.add(np.array(embedding))  # Add new embedding
    
    save_faiss_index(index)  # Save the updated FAISS index

# Retrain the reward model based on the new feedback
def retrain_reward_model(feedback: str) -> None:
    """
    Retrains the reward model with the new feedback.
    """
    # Placeholder: Implement your reward model retraining logic here.
    print(f"Retraining reward model with feedback: {feedback}")
    # Assume feedback influences training for reinforcement learning

# Utility functions for FAISS (placeholder functions)
def load_faiss_index() -> faiss.Index:
    """
    Load the FAISS index.
    """
    # Example: load FAISS index from disk (customize based on your setup)
    index = faiss.read_index('faiss.index')
    return index

def save_faiss_index(index: faiss.Index) -> None:
    """
    Save the FAISS index to disk.
    """
    # Example: save FAISS index to disk (customize based on your setup)
    faiss.write_index(index, 'faiss.index')

# Placeholder function to get the embedding model
def get_embedding_model():
    """
    Retrieves or initializes the embedding model.
    """
    # Example: load pre-trained SentenceTransformer or any model
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model
