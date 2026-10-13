# chatbot/core.py

import os
import numpy as np
import sqlite3
import hashlib
import streamlit as st
from typing import List, Dict

from groq import Groq
from chatbot.embeddings import load_resources
from chatbot.database import DB_PATH
from chatbot.sentiment import analyze_sentiment as detect_emotion

# ------------------ Load Resources ------------------
index, df, embedding_model = load_resources()

from dotenv import load_dotenv
load_dotenv()

# ------------------ LLM Configuration ------------------
GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile"
]

def get_groq_client():
    """Load fresh GROQ client with current environment variables."""
    load_dotenv(override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if api_key and api_key.strip():
        return Groq(api_key=api_key.strip())
    return None

def call_gemini_fallback(prompt: str) -> str:
    """Optional fallback to Gemini if GEMINI_API_KEY is configured."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or not gemini_key.strip():
        return None
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key.strip())
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        if res and res.text:
            return res.text.strip()
    except Exception as e:
        print(f"[Gemini Fallback Error]: {e}")
    return None

# Helper to emulate GenAI structure for chat title generation in main.py
class GroqLLM:
    def generate_content(self, prompt: str):
        class ResponseHolder:
            def __init__(self, text):
                self.text = text
        try:
            client = get_groq_client()
            if client:
                for model in GROQ_MODELS:
                    try:
                        res = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model=model,
                            max_tokens=256,
                            temperature=0.2,
                        )
                        if res.choices and res.choices[0].message.content:
                            val = res.choices[0].message.content.strip()
                            return ResponseHolder(val)
                    except Exception as model_err:
                        if "model_not_found" in str(model_err) or "does not exist" in str(model_err):
                            continue
                        raise model_err
        except Exception as e:
            print(f"[Title Generation Error]: {e}")
        
        # Try Gemini fallback if available
        gemini_res = call_gemini_fallback(prompt)
        if gemini_res:
            return ResponseHolder(gemini_res)
        return ResponseHolder("")

llm = GroqLLM()

# ------------------ FAISS Search ------------------
def retrieve_from_faiss(query: str, top_k: int = 5, return_full: bool = False):
    query_embedding = np.array([embedding_model.encode(query)]).astype("float32")
    distances, indices = index.search(query_embedding, top_k)
    result_df = df.iloc[indices[0]]
    return result_df.to_dict(orient="records") if return_full else result_df["Response"].dropna().tolist()

# ------------------ Emotion-Aware Filtering ------------------
def get_emotionally_aligned_response(rows: List[Dict], detected_emotion: str) -> str:
    if not rows:
        return "I'm here for you. How can I help you today?"

    # Map RoBERTa sentiment ('negative', 'neutral', 'positive') to dataset emotions
    emotion_map = {
        "negative": ["depressed", "sad", "anxious", "stressed"],
        "positive": ["happy"],
        "neutral": ["neutral"]
    }
    targets = emotion_map.get(detected_emotion.lower(), [detected_emotion.lower()])

    # Find rows matching target emotions
    matching_rows = [row for row in rows if str(row.get("Emotion", "")).lower() in targets]
    selected_row = matching_rows[0] if matching_rows else rows[0]

    resp = selected_row.get("Response", "")
    action = selected_row.get("Suggested_Action", "")
    followup = selected_row.get("Followup_Question", "")

    if action and followup and resp:
        return f"{resp}\n\nTip: {action}\n\n{followup}"
    return resp if resp else "I'm here to listen. Tell me more about what's on your mind."

# ------------------ Cache ------------------
def get_cached_response(user_input: str) -> str:
    return None

# ------------------ Response Generation ------------------
def generate_response(user_input: str) -> str:
    cached = get_cached_response(user_input)
    if cached:
        return cached

    detected_emotion = detect_emotion(user_input)
    retrieved_rows = retrieve_from_faiss(user_input, top_k=5, return_full=True)
    best_response = get_emotionally_aligned_response(retrieved_rows, detected_emotion)

    # 1. Try Groq LLM
    try:
        client = get_groq_client()
        if not client:
            raise ValueError("GROQ_API_KEY is not set or empty in .env.")

        retrieved_text = "\n".join([f"- {row.get('Response', '')}" for row in retrieved_rows if row.get('Response')])
        prompt = f"""
You are a compassionate, emotionally-aware AI mental health companion.
The user says:
"{user_input}"

Their detected emotional tone is: {detected_emotion}

Reference context / suggestions from mental health database:
{retrieved_text}

Instructions:
- Respond directly, warmly, and naturally to what the user said.
- Do NOT repeat rigid templates like "As a ... expert, I understand that ...".
- Speak in a supportive, conversational, and empathetic tone.
"""

        for model in GROQ_MODELS:
            try:
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    max_tokens=2048,
                    temperature=0.6,
                )
                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
            except Exception as model_err:
                if "model_not_found" in str(model_err) or "does not exist" in str(model_err):
                    continue
                raise model_err

    except Exception as e:
        print(f"[LLM Error]: {e}")
        error_msg = str(e)

        # Notify via Streamlit if running inside a Streamlit web session
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            if get_script_run_ctx():
                if "expired_api_key" in error_msg or "Invalid API Key" in error_msg or "invalid_api_key" in error_msg:
                    st.warning("⚠️ **GROQ_API_KEY is invalid or expired.** Please update your `GROQ_API_KEY` in `.env` to enable dynamic AI responses.")
                elif "GROQ_API_KEY is not set" in error_msg:
                    st.warning("⚠️ **GROQ_API_KEY is not configured.** Please set your `GROQ_API_KEY` in `.env`.")
        except Exception:
            pass

        # 2. Try Gemini fallback if configured
        gemini_res = call_gemini_fallback(prompt)
        if gemini_res:
            return gemini_res

        # 3. Fallback to retrieved response
        return best_response