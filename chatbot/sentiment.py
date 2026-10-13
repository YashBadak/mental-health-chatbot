# chatbot/sentiment.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax

# --- FIX: Use a pre-trained public model from Hugging Face ---
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# The labels correspond to what this specific model outputs
LABELS = ['negative', 'neutral', 'positive']

def analyze_sentiment(text: str) -> str:
    """
    Analyzes the sentiment of a given text and returns 'positive', 'negative', or 'neutral'.
    """
    try:
        # Tokenize the text
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        
        # Get model output
        output = model(**inputs)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)
        
        # Get the label with the highest score
        ranking = reversed(scores.argsort())
        top_label = LABELS[next(ranking)]
        return top_label
        
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return "neutral" # Default to neutral in case of an error