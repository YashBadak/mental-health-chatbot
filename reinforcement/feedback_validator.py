import nltk
from textblob import TextBlob
from collections import Counter
import re

# Function to validate the feedback
def validate_feedback(feedback: str) -> bool:
    """
    Validates the user feedback by ensuring it is meaningful, non-contradictory, and relevant.
    """
    if not feedback or len(feedback.strip()) == 0:
        return False  # Empty feedback is invalid
    
    # Sentiment validation (checking if the sentiment makes sense)
    sentiment = analyze_sentiment(feedback)
    if sentiment not in ['positive', 'negative', 'neutral']:
        return False  # Invalid sentiment detected
    
    # Language check (ensure feedback is well-formed)
    if not is_valid_language(feedback):
        return False  # Feedback contains invalid characters or language
    
    # Duplicate check (ensure no identical feedback in past)
    if check_duplicate_feedback(feedback):
        return False  # Duplicate feedback
    
    return True

# Sentiment analysis of the feedback
def analyze_sentiment(feedback: str) -> str:
    """
    Analyzes the sentiment of the feedback using TextBlob.
    Returns 'positive', 'negative', or 'neutral'.
    """
    analysis = TextBlob(feedback)
    polarity = analysis.sentiment.polarity
    
    if polarity > 0:
        return 'positive'
    elif polarity < 0:
        return 'negative'
    else:
        return 'neutral'

# Check if the feedback contains invalid or non-standard language (e.g., offensive words)
def is_valid_language(feedback: str) -> bool:
    """
    Ensures feedback does not contain invalid or offensive words.
    """
    # Simple example, can be extended with a list of inappropriate words
    offensive_words = ['offensive_word1', 'offensive_word2']
    feedback = feedback.lower()
    for word in offensive_words:
        if word in feedback:
            return False
    return True

# Check if the feedback is a duplicate (can be based on a hash or direct comparison)
def check_duplicate_feedback(feedback: str) -> bool:
    """
    Checks if the feedback is already present in the feedback database.
    """
    # This could be implemented using a hashing method or a database query.
    # Simple example: assuming feedback is stored in a list
    feedback_db = ["This is a sample feedback", "Great chatbot experience!"]
    if feedback in feedback_db:
        return True
    return False
