import streamlit as st
import sqlite3
import uuid
import json
from dotenv import load_dotenv
load_dotenv()
import chatbot.auth as auth
from chatbot.core import generate_response
from chatbot.database import DB_PATH, init_db, load_chat, delete_chat, init_user_table, store_feedback
from chatbot.admin_dashboard import render_admin_dashboard
from chatbot.profile import render_profile_page
from chatbot.tips import render_tips_page
from chatbot.model_trainer import render_model_trainer_page
from chatbot.admin_tips import render_admin_tips_editor
from datetime import datetime
import chatbot.core as core # Import core to access the LLM

# --- Helper Functions for Chat Titles ---

def add_title_column_if_not_exists():
    """
    Ensures the 'chat_history' table has a 'title' column.
    This makes the change backward compatible with your existing database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN title TEXT")
        print("INFO: 'title' column added to chat_history table.")
    except sqlite3.OperationalError:
        pass  # Column already exists, so we can ignore the error.
    finally:
        conn.close()

def save_chat(chat_id, messages, title=None):
    """
    Saves chat messages and a title to the database.
    This function replaces the original save_chat to handle the new 'title' field.
    """
    try:
        formatted_messages = json.dumps(messages, ensure_ascii=False)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if title is None:
            cursor.execute("SELECT title FROM chat_history WHERE chat_id = ?", (chat_id,))
            result = cursor.fetchone()
            if result:
                title = result[0]

        cursor.execute("""
            REPLACE INTO chat_history (chat_id, username, messages, title)
            VALUES (?, ?, ?, ?)
        """, (chat_id, st.session_state.username, formatted_messages, title))
        conn.commit()
    except Exception as e:
        print(f"Error saving chat: {e}")
    finally:
        conn.close()

def update_chat_title(chat_id, new_title):
    """Updates the title of a specific chat in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE chat_history SET title = ? WHERE chat_id = ?", (new_title, chat_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating chat title: {e}")
    finally:
        conn.close()


def generate_chat_title(user_input: str) -> str:
    """Generates a short, descriptive title for the chat using the LLM."""
    try:
        prompt = f"""
        Based on the user's first message, create a very short and concise title for the chat session (under 5 words).
        Do not use quotes in the title. Just return the title itself.

        User's first message: "{user_input}"
        
        Title:
        """
        response = core.llm.generate_content(prompt)
        title = response.text.strip().replace('"', '')
        return title if title else "Chat"
    except Exception as e:
        print(f"Error generating title: {e}")
        return user_input[:40] + "..." if len(user_input) > 40 else user_input

def render_chat_interface():
    """
    This function contains all the UI and logic for the chat page.
    """
    st.sidebar.header("📂 Chat History")

    # --- Chat Initialization and Loading ---
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, title FROM chat_history WHERE username = ? ORDER BY rowid DESC", (st.session_state.username,))
    user_chats = {row[0]: row[1] if row[1] else row[0] for row in cursor.fetchall()}
    conn.close()
    user_chat_ids = list(user_chats.keys())

    if "chat_id" not in st.session_state or st.session_state.chat_id not in user_chat_ids:
        if user_chat_ids:
            st.session_state.chat_id = user_chat_ids[0]
            st.session_state.messages = load_chat(st.session_state.chat_id)
        else:
            new_id = f"chat_{uuid.uuid4()}"
            st.session_state.chat_id = new_id
            st.session_state.messages = []
            save_chat(new_id, [], title="New Chat")
            user_chats[new_id] = "New Chat"
            user_chat_ids.insert(0, new_id)

    # --- Sidebar for Chat Management ---
    selected_chat_id = st.sidebar.selectbox(
        "🗂️ Select a Chat", options=user_chat_ids,
        format_func=lambda chat_id: user_chats.get(chat_id, "Chat"),
        index=user_chat_ids.index(st.session_state.chat_id) if st.session_state.chat_id in user_chat_ids else 0
    )

    if selected_chat_id != st.session_state.chat_id:
        st.session_state.chat_id = selected_chat_id
        st.session_state.messages = load_chat(selected_chat_id) or []
        st.session_state.renaming_chat = False
        st.rerun()

    col1, col2, col3 = st.sidebar.columns(3)
    if col1.button("🆕 New"):
        new_id = f"chat_{uuid.uuid4()}"
        st.session_state.chat_id = new_id
        st.session_state.messages = []
        save_chat(new_id, [], title="New Chat")
        st.session_state.renaming_chat = False
        st.rerun()
    if col2.button("✏️ Rename"):
        st.session_state.renaming_chat = not st.session_state.get("renaming_chat", False)
        st.rerun()
    if col3.button("🗑️ Delete"):
        delete_chat(st.session_state.chat_id)
        st.session_state.pop("chat_id", None)
        st.session_state.renaming_chat = False
        st.rerun()

    if st.session_state.get("renaming_chat"):
        current_title = user_chats.get(st.session_state.chat_id, "")
        new_title_input = st.sidebar.text_input("New chat name", value=current_title, key="rename_input")
        if st.sidebar.button("Save Name"):
            if new_title_input:
                update_chat_title(st.session_state.chat_id, new_title_input)
                st.session_state.renaming_chat = False
                st.rerun()

    # --- Display Chat Messages ---
    for i, message in enumerate(st.session_state.get("messages", [])):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show feedback buttons only for the last message from the assistant
            if i == len(st.session_state.messages) - 1 and message["role"] == "assistant":
                col_thumb_up, col_spacer, col_thumb_down = st.columns([1, 2, 1]) # Adjust column ratios

                with col_thumb_up:
                    if st.button("👍", key=f"thumbs_up_{i}"):
                        from reinforcement.save_feedback import save_feedback
                        user_message = st.session_state.messages[-2]["content"] if len(st.session_state.messages) >= 2 else ""
                        bot_response = st.session_state.messages[-1]["content"]
                        save_feedback(
                            user_id=st.session_state.username,
                            input_text=user_message,
                            response_text=bot_response,
                            rating="positive",
                            reward=1
                        )
                        st.success("Thanks for your feedback!")

                with col_thumb_down:
                    if st.button("👎", key=f"thumbs_down_{i}"):
                        from reinforcement.save_feedback import save_feedback
                        user_message = st.session_state.messages[-2]["content"] if len(st.session_state.messages) >= 2 else ""
                        bot_response = st.session_state.messages[-1]["content"]
                        save_feedback(
                            user_id=st.session_state.username,
                            input_text=user_message,
                            response_text=bot_response,
                            rating="negative",
                            reward=0
                        )
                        st.warning("Thanks for your feedback!")

    # --- Handle User Input & Title Generation ---
    if user_input := st.chat_input("💬 Ask anything"):
        is_first_message = len(st.session_state.messages) == 0
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("⏳ Thinking...")
            bot_response = generate_response(user_input)
            message_placeholder.markdown(bot_response)

        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        new_title = generate_chat_title(user_input) if is_first_message else None
        save_chat(st.session_state.chat_id, st.session_state.messages, title=new_title)
        st.rerun()

# --- Main App Setup ---
st.title("🧠 Mental Health Chatbot 🤖")

init_db()
init_user_table()
add_title_column_if_not_exists()

# --- Authentication ---
if not st.session_state.get("authenticated"):
    if 'logout_message' in st.session_state:
        st.success(st.session_state.logout_message)
        del st.session_state.logout_message
    if st.session_state.get('forgot_password_flow'):
        auth.forgot_password_ui()
    else:
        login_tab, signup_tab, about_tab, contact_tab = st.tabs(
            ["Login", "Sign Up", "About", "Contact Us"]
        )
        with login_tab: auth.login_ui()
        with signup_tab: auth.signup_ui()
        with about_tab: auth.about_ui()
        with contact_tab: auth.contact_us_ui()
    st.stop()

# --- Sidebar Navigation for Logged-in Users ---
st.sidebar.title(f"Welcome, {st.session_state.username}")
st.sidebar.markdown("---")

if st.session_state.get("role") == "admin":
    # --- ADMIN SIDEBAR ---
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'

    if st.sidebar.button("👑 Dashboard", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()

    if st.sidebar.button("💡 Manage Tips", use_container_width=True):
        st.session_state.page = 'tips_admin' # New page state for the tips editor
        st.rerun()

    if st.sidebar.button("🧠 Train Model", use_container_width=True):
        st.session_state.page = 'train_model'
        st.rerun()

else:
    # --- REGULAR USER SIDEBAR ---
    if 'page' not in st.session_state:
        st.session_state.page = 'chat'
    if st.sidebar.button("💬 Chat", use_container_width=True):
        st.session_state.page = 'chat'
        st.rerun()
    if st.sidebar.button("💡 Tips", use_container_width=True):
        st.session_state.page = 'tips'
        st.rerun()
    if st.sidebar.button("👤 Profile", use_container_width=True):
        st.session_state.page = 'profile'
        st.rerun()
    

# Logout button is visible to all logged-in users
if st.sidebar.button("🚪 Logout", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- Main Content Display ---
if st.session_state.get("role") == "admin":
    # --- ADMIN PAGE ROUTING ---
    admin_page = st.session_state.get('page', 'dashboard')
    if admin_page == 'tips_admin':
        render_admin_tips_editor()
    elif admin_page == 'train_model':
        render_model_trainer_page()
    else: # Default to dashboard
        render_admin_dashboard()
else:
    # --- REGULAR USER PAGE ROUTING ---
    user_page = st.session_state.get('page', 'chat')
    if user_page == 'tips':
        render_tips_page()
    elif user_page == 'profile':
        render_profile_page()
    else:
        render_chat_interface()