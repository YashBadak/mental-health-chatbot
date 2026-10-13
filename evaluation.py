# evaluation/evaluate_model.py
import pandas as pd
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import os
import sys

# Add the project root to the Python path to allow for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.core import generate_response

# Define the path to your dataset
# This should be the same file used for your FAISS index and embeddings
DATA_FILE = "data/mental_health_embeddings.csv"
# The number of samples from your dataset to test on.
# Start with a small number (e.g., 20-50) for faster testing.
NUM_SAMPLES = 20 

def calculate_scores(reference, candidate):
    """Calculates BLEU and ROUGE scores for a single reference-candidate pair."""
    
    # --- BLEU Score ---
    # The reference needs to be a list of lists of words
    # The candidate needs to be a list of words
    reference_tokens = [reference.split()]
    candidate_tokens = candidate.split()
    # Using SmoothingFunction to avoid zero scores for short sentences
    chencherry = SmoothingFunction()
    bleu_score = sentence_bleu(reference_tokens, candidate_tokens, smoothing_function=chencherry.method1)
    
    # --- ROUGE Score ---
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    rouge_scores = scorer.score(reference, candidate)
    
    return bleu_score, rouge_scores

def evaluate_model():
    """
    Loads a sample of the dataset, generates responses with the chatbot,
    and calculates the average BLEU and ROUGE scores.
    """
    print(f"Loading test data from {DATA_FILE}...")
    try:
        df = pd.read_csv(DATA_FILE)
        # Ensure we don't try to sample more rows than exist
        sample_size = min(NUM_SAMPLES, len(df))
        if sample_size == 0:
            print("Error: Data file is empty.")
            return
        test_samples = df.sample(n=sample_size, random_state=42)
    except FileNotFoundError:
        print(f"Error: Data file not found at {DATA_FILE}. Please check the path.")
        return
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    total_bleu = 0
    total_rouge1 = 0
    total_rouge2 = 0
    total_rougeL = 0
    
    results = []

    print(f"\nGenerating and scoring responses for {len(test_samples)} samples...\n")
    for index, row in test_samples.iterrows():
        prompt = row['Prompt']
        reference_response = row['Response']
        
        # 1. Generate a response from your chatbot
        candidate_response = generate_response(prompt)
        
        # 2. Calculate scores
        bleu, rouge = calculate_scores(reference_response, candidate_response)
        
        # 3. Accumulate scores
        total_bleu += bleu
        total_rouge1 += rouge['rouge1'].fmeasure
        total_rouge2 += rouge['rouge2'].fmeasure
        total_rougeL += rouge['rougeL'].fmeasure
        
        results.append({
            "Prompt": prompt,
            "Reference Response": reference_response,
            "Generated Response": candidate_response,
            "BLEU": bleu,
            "ROUGE-L": rouge['rougeL'].fmeasure
        })
        
        print(f"Processed sample {index+1}/{len(test_samples)}")

    # Calculate averages
    avg_bleu = total_bleu / len(test_samples)
    avg_rouge1 = total_rouge1 / len(test_samples)
    avg_rouge2 = total_rouge2 / len(test_samples)
    avg_rougeL = total_rougeL / len(test_samples)

    # Display results
    print("\n--- Evaluation Results ---")
    print(f"Average BLEU Score: {avg_bleu:.4f}")
    print(f"Average ROUGE-1 Score: {avg_rouge1:.4f}")
    print(f"Average ROUGE-2 Score: {avg_rouge2:.4f}")
    print(f"Average ROUGE-L Score: {avg_rougeL:.4f}")
    print("------------------------\n")
    
    # Optionally, display a table with a few examples
    print("--- Example Generations and Scores ---")
    results_df = pd.DataFrame(results).head()
    print(results_df.to_string())


if __name__ == "__main__":
    # Download the 'punkt' tokenizer models if not already present
    # This is required by NLTK for tokenization
    try:
        nltk.data.find('tokenizers/punkt')
    except nltk.downloader.DownloadError:
        print("Downloading NLTK 'punkt' model...")
        nltk.download('punkt')
        print("Download complete.")
        
    evaluate_model()