# chatbot/admin_tips_editor.py
import streamlit as st
import json
import os

TIPS_FILE = "data/tips_content.json"

def load_tips_content():
    """Loads the content for the tips page from a JSON file."""
    if os.path.exists(TIPS_FILE):
        with open(TIPS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"affirmations": [], "videos": [], "techniques": [], "links": []}

def save_tips_content(data):
    """Saves the provided data to the tips content JSON file."""
    with open(TIPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def render_admin_tips_editor():
    """Renders the UI for the admin to manage the Tips page content."""
    st.title("💡 Manage Tips Page Content")
    st.markdown("Use the sections below to add, update, or remove content from the user-facing Tips page.")
    st.markdown("---")

    content = load_tips_content()

    with st.expander("Manage Affirmations", expanded=True):
        affirmations_text = "\n".join(content['affirmations'])
        new_affirmations_text = st.text_area(
            "Affirmations (one per line)", value=affirmations_text, height=200
        )
        if st.button("Save Affirmations"):
            content['affirmations'] = [line.strip() for line in new_affirmations_text.split("\n") if line.strip()]
            save_tips_content(content)
            st.success("Affirmations updated!")
            st.rerun()

    with st.expander("Manage Videos"):
        st.subheader("Current Videos")
        for i, video in enumerate(content['videos']):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{video['title']}**: `{video['url']}`")
            with col2:
                if st.button("Delete", key=f"del_video_{i}", use_container_width=True):
                    content['videos'].pop(i)
                    save_tips_content(content)
                    st.rerun()
        
        st.subheader("Add New Video")
        with st.form("new_video_form", clear_on_submit=True):
            new_video_title = st.text_input("Video Title")
            new_video_url = st.text_input("YouTube Video URL")
            if st.form_submit_button("Add Video"):
                if new_video_title and new_video_url:
                    content['videos'].append({"title": new_video_title, "url": new_video_url})
                    save_tips_content(content)
                    st.success("Video added!")
                    st.rerun()

    with st.expander("Manage Reading & Techniques"):
        st.subheader("Current Techniques")
        for i, technique in enumerate(content['techniques']):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{technique['title']}**")
            with col2:
                if st.button("Delete", key=f"del_tech_{i}", use_container_width=True):
                    content['techniques'].pop(i)
                    save_tips_content(content)
                    st.rerun()
        
        st.subheader("Add New Technique")
        with st.form("new_tech_form", clear_on_submit=True):
            new_tech_title = st.text_input("Technique Title")
            new_tech_content = st.text_area("Content (Supports Markdown)")
            if st.form_submit_button("Add Technique"):
                if new_tech_title and new_tech_content:
                    content['techniques'].append({"title": new_tech_title, "content": new_tech_content})
                    save_tips_content(content)
                    st.success("Technique added!")
                    st.rerun()