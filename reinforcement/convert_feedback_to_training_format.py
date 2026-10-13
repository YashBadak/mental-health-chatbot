# reinforcement/convert_feedback_to_training_format.py
import pandas as pd
import json
from reinforcement.reward_model import calculate_reward # Import the reward function

# Define file paths
INPUT_FILE = "data/processed_feedback.csv"
OUTPUT_FILE = "data/reward_training_data.jsonl" # New output file name

def convert_feedback():
    """
    Converts processed feedback into a JSONL file with (text, score) pairs
    suitable for training a scoring reward model.
    """
    try:
        processed_df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: Processed feedback file not found at {INPUT_FILE}.")
        return
    except pd.errors.EmptyDataError:
        print(f"Warning: The processed feedback file is empty.")
        return

    required_columns = ["input_text", "response_text", "rating"]
    if not all(col in processed_df.columns for col in required_columns):
        print(f"Error: The input CSV must contain columns: {required_columns}")
        return
        
    processed_df = processed_df.dropna(subset=required_columns)

    training_data = []
    for index, row in processed_df.iterrows():
        # Combine prompt and response into a single text input
        text = f"PROMPT: {row['input_text']}\n\nRESPONSE: {row['response_text']}"
        
        # Calculate score based on rating
        score = calculate_reward(row['rating'])
        
        training_data.append({"text": text, "score": score})

    if not training_data:
        print("Warning: No valid feedback data found to convert.")
        return

    # Write the new data format to a JSONL file
    with open(OUTPUT_FILE, 'w') as f:
        for entry in training_data:
            f.write(json.dumps(entry) + '\n')

    print(f"Successfully converted {len(training_data)} feedback entries to {OUTPUT_FILE}")

if __name__ == "__main__":
    convert_feedback()