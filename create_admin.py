# create_admin.py
import sys
import os
import getpass

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.database import init_user_table, add_user

def main():
    """
    A command-line script to create a new admin user.
    """
    init_user_table()
    print("--- Create Admin User ---")
    username = input("Enter admin username: ")
    password = getpass.getpass("Enter admin password: ")
    email = input("Enter admin email: ")  # Prompt for admin's email

    if not username or not password or not email:
        print("Username, password, and email cannot be empty.")
        return

    # Pass the email to the add_user function
    if add_user(username, password, email, "admin"):
        print(f"Admin user '{username}' created successfully.")
    else:
        print(f"Failed to create admin user '{username}'. It may already exist.")

if __name__ == "__main__":
    main()