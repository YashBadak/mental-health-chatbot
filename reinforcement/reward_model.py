# reinforcement/reward_model.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# Define paths
BASE_MODEL_NAME = "distilbert-base-uncased"
FINETUNED_REWARD_MODEL_PATH = "models/reward_model_finetuned"

# --- FIX: Load the base model with num_labels=1 for scoring ---
base_model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL_NAME, num_labels=1)
base_tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)

def retrain_on_new_feedback(new_feedback_data):
    """
    Trains the reward model on new feedback and saves the updated model to disk.
    """
    print("Retraining reward model on new scored feedback...")
    
    # Use the base model for retraining
    optimizer = torch.optim.AdamW(base_model.parameters(), lr=5e-5)
    loss_function = torch.nn.MSELoss()

    base_model.train()
    for item in new_feedback_data:
        inputs = base_tokenizer(item['text'], return_tensors="pt", truncation=True, padding=True)
        scores = torch.tensor([item['score']], dtype=torch.float32)

        optimizer.zero_grad()
        outputs = base_model(**inputs)
        
        loss = loss_function(outputs.logits.squeeze(), scores)
        loss.backward()
        optimizer.step()

    # --- FIX: Save the fine-tuned model ---
    print(f"Saving fine-tuned model to {FINETUNED_REWARD_MODEL_PATH}")
    base_model.save_pretrained(FINETUNED_REWARD_MODEL_PATH)
    base_tokenizer.save_pretrained(FINETUNED_REWARD_MODEL_PATH)
    print("Retraining and saving complete.")

# --- NEW: Function to load our fine-tuned model for inference ---
def load_finetuned_reward_model():
    """
    Loads the fine-tuned reward model. If it doesn't exist,
    falls back to the base model.
    """
    if os.path.exists(FINETUNED_REWARD_MODEL_PATH):
        print("Loading fine-tuned reward model.")
        model = AutoModelForSequenceClassification.from_pretrained(FINETUNED_REWARD_MODEL_PATH)
        tokenizer = AutoTokenizer.from_pretrained(FINETUNED_REWARD_MODEL_PATH)
    else:
        print("Fine-tuned model not found. Loading base model.")
        model = base_model
        tokenizer = base_tokenizer
    
    model.eval() # Set model to evaluation mode
    return model, tokenizer

# --- NEW: Function to score a response ---
@torch.no_grad() # Disable gradient calculations for faster inference
def score_response(model, tokenizer, prompt, response):
    """
    Uses the loaded reward model to score a single prompt-response pair.
    """
    text_to_score = f"PROMPT: {prompt}\n\nRESPONSE: {response}"
    inputs = tokenizer(text_to_score, return_tensors='pt', truncation=True, padding=True)
    output = model(**inputs)
    return output.logits.squeeze().item()

def calculate_reward(rating: str) -> float:
    # (This function remains the same)
    if rating == "positive": return 1.0
    elif rating == "negative": return 0.0
    return 0.5