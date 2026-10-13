# chatbot/tips_page.py
import streamlit as st
import json
import random
import os

TIPS_FILE = "data/tips_content.json"

def load_tips_content():
    """Loads the content for the tips page from a JSON file."""
    if os.path.exists(TIPS_FILE):
        with open(TIPS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "affirmations": ["Welcome! The content for this page is being set up."],
        "videos": [], "techniques": [], "links": []
    }

def get_random_affirmation(affirmations):
    """Returns a random positive affirmation from the provided list."""
    if not affirmations:
        return "Stay positive!"
    return random.choice(affirmations)

def render_tips_page():
    """Renders the UI and content for the Wellness Tips page."""
    content = load_tips_content()
    st.title("💡 Wellness Tips & Resources")
    st.markdown("A collection of resources to help you find balance, peace, and clarity.")
    st.markdown("---")

    st.subheader("✨ A Thought for Today")
    st.info(f"**Affirmation:** \"{get_random_affirmation(content['affirmations'])}\"")
    if st.button("Show me another one"):
        st.rerun()

    st.markdown("---")

    tab_videos, tab_techniques, tab_links = st.tabs([
        "🎬 Watch & Relax", "📖 Read & Reflect", "🔗 Helpful Links"
    ])

    with tab_videos:
        st.header("Guided Videos for Peace and Clarity")
        if content['videos']:
            for video in content['videos']:
                st.subheader(video['title'])
                st.video(video['url'])
        else:
            st.info("Video content is not available at the moment.")

    with tab_techniques:
        st.header("Techniques for a Healthier Mind")
        if content['techniques']:
            for technique in content['techniques']:
                st.subheader(technique['title'])
                st.markdown(technique['content'])
        else:
            st.info("Reading content is not available at the moment.")

    with tab_links:
        st.header("Explore More Resources")
        if content['links']:
            for link in content['links']:
                st.markdown(f"- **[{link['title']}]({link['url']})**")
        else:
            st.info("Links are not available at the moment.")

        st.error(
            """
            **CRISIS SUPPORT**
            Remember, if you are in immediate distress, these helplines are available 24/7:
            - **Tele MANAS (Govt. of India):** Call `14416`
            - **Vandrevala Foundation:** Call or WhatsApp `9999666555`
            """
        )