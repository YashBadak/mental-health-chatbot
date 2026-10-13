import os
import csv
import pandas as pd
from datetime import datetime
import os

# Define constants for the file path and headers to ensure consistency
CSV_FILE = "data/new_feedback.csv"
HEADERS = ['user_id', 'timestamp', 'input_text', 'response_text', 'rating', 'reward']

def save_feedback(user_id: str, input_text: str, response_text: str, rating: str, reward: float):
    """
    Saves user feedback to a CSV file, creating the file and writing headers
    if it doesn't already exist.
    """
    try:
        # Ensure the 'data' directory exists
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

        # Check if the file already exists to determine if we need to write headers
        # This is the crucial check to prevent missing headers
        file_exists = os.path.isfile(CSV_FILE)

        # Create a DataFrame for the new feedback
        new_feedback_df = pd.DataFrame([{
            "user_id": user_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_text": input_text,
            "response_text": response_text,
            "rating": rating,
            "reward": reward
        }])

        # --- THE CRUCIAL FIX ---
        # Use the 'header' parameter to write headers only when the file is new.
        new_feedback_df.to_csv(CSV_FILE, mode='a', header=not file_exists, index=False)

        print(f"Feedback from {user_id} saved successfully to {CSV_FILE}")

    except Exception as e:
        print(f"Error saving feedback: {e}")
