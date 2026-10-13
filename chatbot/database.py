# chatbot/database.py
import sqlite3
import bcrypt
import pandas as pd
import json

DB_PATH = "data/chatbot_database.db"

# --- Database Initialization (existing code remains the same) ---
def init_db():
    """Initializes the main chat history table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            chat_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            messages TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_email_column_if_not_exists():
    """
    Safely adds an 'email' column to the 'users' table for backward compatibility.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'email' not in columns:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT NOT NULL DEFAULT 'placeholder@email.com'")
            conn.commit()
            print("INFO: 'email' column added to users table.")
        except sqlite3.OperationalError as e:
            print(f"Could not add email column: {e}")
    conn.close()

def init_user_table():
    """Initializes the users table for authentication."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    add_email_column_if_not_exists()

# --- User Management (add new functions here) ---
def add_user(username, password, email, role):
    """Adds a new user to the database with an email."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cursor.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            (username, hashed_password, email, role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticates a user and returns their role if successful."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
        return user[1]
    return None

def update_username(old_username, new_username):
    """Updates a user's username and their associated chat history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # First, update the users table. This will fail if new_username is taken.
        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
        # Next, update the chat_history table to maintain the link.
        cursor.execute("UPDATE chat_history SET username = ? WHERE username = ?", (new_username, old_username))
        conn.commit()
        return True
    except sqlite3.IntegrityError: # Catches if the new_username is already taken
        return False
    finally:
        conn.close()

def get_email_by_username(username):
    """Retrieves a user's email by their username."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def check_email_exists(email):
    """Checks if a user with the given email exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def update_password_by_email(email, new_password):
    """Updates a user's password based on their email address."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error updating password: {e}")
        return False
    finally:
        conn.close()

def delete_user_and_chats(username):
    """Deletes a user and all of their associated data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Delete from users table
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        # Delete from chat_history table
        cursor.execute("DELETE FROM chat_history WHERE username = ?", (username,))
        # You could add more deletes here if you store feedback or other user data
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user and chats: {e}")
        return False
    finally:
        conn.close()

def get_user_count():
    """Returns the total number of registered users."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    finally:
        conn.close()
    return count

def get_all_users():
    """Fetches all users for the admin dashboard."""
    conn = sqlite3.connect(DB_PATH)
    try:
        query = "SELECT id, username, role, email FROM users"
        df = pd.read_sql_query(query, conn)
    except pd.io.sql.DatabaseError:
        df = pd.DataFrame(columns=['id', 'username', 'role', 'email'])
    finally:
        conn.close()
    return df

# --- Chat History Management (existing code remains the same) ---
def save_chat(chat_id, username, messages):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_history WHERE chat_id = ?", (chat_id,))
    existing_record = cursor.fetchone()
    if existing_record:
        cursor.execute("UPDATE chat_history SET messages = ? WHERE chat_id = ?", (json.dumps(messages), chat_id))
    else:
        cursor.execute("INSERT INTO chat_history (chat_id, username, messages) VALUES (?, ?, ?)", (chat_id, username, json.dumps(messages)))
    conn.commit()
    conn.close()

def load_chat(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT messages FROM chat_history WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return json.loads(result[0]) if result else None

def get_user_chats(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM chat_history WHERE username = ?", (username,))
    chats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chats

def delete_chat(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def store_feedback(username, feedback_text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feedback (username, feedback_text) VALUES (?, ?)", (username, feedback_text))
    conn.commit()
    conn.close()