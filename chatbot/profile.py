# chatbot/profile.py
import streamlit as st
import random
import string
from chatbot.database import (
    get_email_by_username,
    update_password_by_email,
    update_username,
    delete_user_and_chats,
    authenticate_user
)
from chatbot.email_utils import send_otp_email

def render_profile_page():
    """Renders the user profile page for account management."""
    st.title(f"👤 Profile: {st.session_state.username}")

    # --- 1. Change Password ---
    with st.expander("🔑 Change Password", expanded=False):
        st.write(
            "For your security, we will send a One-Time Password (OTP) "
            "to your registered email to begin the password change process."
        )
        change_step = st.session_state.get('change_password_step', 'start')

        if change_step == 'start':
            if st.button("Send OTP to Change Password"):
                email = get_email_by_username(st.session_state.username)
                if email:
                    otp = ''.join(random.choices(string.digits, k=6))
                    if send_otp_email(email, otp):
                        st.session_state['otp_change'] = otp
                        st.session_state['change_password_step'] = 'verify_otp'
                        st.success(f"An OTP has been sent to {email}.")
                        st.rerun()
                    else:
                        st.error("Failed to send OTP. Please try again later.")
                else:
                    st.error("Could not find your registered email.")

        elif change_step == 'verify_otp':
            with st.form("otp_form_change"):
                otp_input = st.text_input("Enter the OTP from your email")
                submit_otp = st.form_submit_button("Verify OTP")
                if submit_otp:
                    if otp_input == st.session_state.get('otp_change'):
                        st.session_state['change_password_step'] = 'reset_password'
                        del st.session_state['otp_change']
                        st.rerun()
                    else:
                        st.error("Invalid OTP.")

        elif change_step == 'reset_password':
            with st.form("new_password_form"):
                new_pass = st.text_input("New Password", type="password")
                confirm_pass = st.text_input("Re-enter New Password", type="password")
                submit_new_pass = st.form_submit_button("Set New Password")

                if submit_new_pass:
                    if not new_pass or new_pass != confirm_pass:
                        st.error("Passwords do not match or are empty.")
                    else:
                        email = get_email_by_username(st.session_state.username)
                        if update_password_by_email(email, new_pass):
                            st.success("✅ Password updated successfully!")
                            del st.session_state['change_password_step']
                        else:
                            st.error("Failed to update password.")

    # --- 2. Change Username ---
    with st.expander("✏️ Change Username", expanded=False):
        st.write(f"Your current username is: **{st.session_state.username}**")
        st.info("Changing your username will log you out. You will need to log back in with your new username.")

        with st.form("change_username_form"):
            new_username = st.text_input("Enter new username")
            submit_username = st.form_submit_button("Change Username")

            if submit_username:
                if not new_username or new_username == st.session_state.username:
                    st.warning("Please enter a new, different username.")
                elif update_username(st.session_state.username, new_username):
                    # Set the message for the login screen
                    st.session_state['logout_message'] = "✅ Username changed successfully! Please log in with your new credentials."
                    # Log user out by clearing all other keys
                    for key in list(st.session_state.keys()):
                        if key != 'logout_message':
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error("That username is already taken. Please choose another.")

    # --- 3. Delete Account ---
    with st.expander("🗑️ Delete Account", expanded=False):
        st.error("**DANGER ZONE**: This action is permanent and cannot be undone. "
                 "All your data, including chat history, will be permanently erased.")

        password = st.text_input("To confirm, please enter your current password", type="password", key="delete_password_check")
        confirm_check = st.checkbox("I understand that my account and all associated data will be deleted forever.")

        if st.button("Permanently Delete My Account", disabled=(not confirm_check or not password)):
            if authenticate_user(st.session_state.username, password):
                if delete_user_and_chats(st.session_state.username):
                    # Set the message for the login screen
                    st.session_state['logout_message'] = "🗑️ Your account has been permanently deleted."
                    # Log user out by clearing all other keys
                    for key in list(st.session_state.keys()):
                        if key != 'logout_message':
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error("An error occurred during account deletion.")
            else:
                st.error("Incorrect password. Account not deleted.")