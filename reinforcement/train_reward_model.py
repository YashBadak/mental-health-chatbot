# reinforcement/train_reward_model.py
import json
from reinforcement.reward_model import retrain_on_new_feedback

TRAINING_DATA_FILE = "data/reward_training_data.jsonl"

def train_model():
    """
    Loads the scored training data and initiates the retraining process.
    The actual training logic is now in reward_model.py.
    """
    try:
        with open(TRAINING_DATA_FILE, 'r') as f:
            new_feedback_data = [json.loads(line) for line in f]
        
        if not new_feedback_data:
            print("Training data file is empty. Skipping training.")
            return
            
        # Call the retraining function which now also handles saving the model
        retrain_on_new_feedback(new_feedback_data)
        
        print("Model training process finished.")
        
    except FileNotFoundError:
        print(f"Error: Training data file not found at {TRAINING_DATA_FILE}.")
    except Exception as e:
        print(f"An unexpected error occurred during training: {e}")

if __name__ == "__main__":
    train_model()