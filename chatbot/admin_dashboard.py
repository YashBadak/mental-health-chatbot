# admin_dashboard.py
import os
import streamlit as st
import pandas as pd
import json
from chatbot.database import get_all_users, get_user_count, DB_PATH

TIPS_FILE = "data/tips_content.json"

def load_tips_content():
    """Loads the content for the tips page from a JSON file."""
    if os.path.exists(TIPS_FILE):
        with open(TIPS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Default structure if file doesn't exist
    return {"affirmations": [], "videos": [], "techniques": [], "links": []}

def save_tips_content(data):
    """Saves the provided data to the tips content JSON file."""
    with open(TIPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def render_admin_dashboard():
    """
    Renders the admin dashboard with user and feedback information.
    """
    st.title("👑 Admin Dashboard")
    st.markdown("---")

    # --- Display Key Metrics ---
    user_total = get_user_count()

    feedback_file = "data/new_feedback.csv"
    feedback_total = 0
    if os.path.exists(feedback_file):
        try:
            feedback_df_for_count = pd.read_csv(feedback_file)
            feedback_total = len(feedback_df_for_count)
        except pd.errors.EmptyDataError:
            feedback_total = 0 # File exists but is empty

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Registered Users", value=user_total)
    with col2:
        st.metric(label="Total Feedbacks Received", value=feedback_total)

    st.markdown("---")

    # --- Display Detailed Tables ---
    st.header("👥 User Management")
    users_df = get_all_users()
    if not users_df.empty:
        st.dataframe(users_df, use_container_width=True)
    else:
        st.info("No users have registered yet.")