# chatbot/auth.py
import streamlit as st
from streamlit_lottie import st_lottie
import requests
import random
import string
from chatbot.database import add_user, authenticate_user, check_email_exists, update_password_by_email
from chatbot.email_utils import send_welcome_email, send_otp_email

def load_lottie_url(url: str):
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def render_footer():
    """Renders the footer content for the auth pages."""
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("#### About This Application")
    st.markdown(
        "Welcome to your Mental Health Chatbot. Our mission is to provide a safe, anonymous, and "
        "supportive space where you can freely express your thoughts and feelings. Our AI assistant "
        "is designed to listen, offer comfort, and provide information to help you on your journey "
        "towards mental well-being."
    )

    st.warning(
        """
        **Disclaimer:** This chatbot is an AI-based listening service and not a substitute for
        professional medical advice, diagnosis, or treatment. It is not designed to provide crisis support.
        Always seek the advice of your physician or other qualified health providers with any
        questions you may have regarding a medical condition.
        """
    )

    st.info(
        """
        **In Crisis?** If you are in emotional distress or thinking about harming yourself, please
        reach out for help immediately. Confidential support is available from trained professionals.
        - **Tele MANAS (Govt. of India):** Call `14416` (24/7)
        - **Vandrevala Foundation:** Call or WhatsApp `9999666555` (24/7)
        """
    )


# Common animation
lottie_animation = load_lottie_url("https://assets1.lottiefiles.com/packages/lf20_w51pcehl.json")

def login_ui():
    # ... (styling) ...
    st.title("🔐 Login to Mental Health Chatbot")
    col1, col2 = st.columns([1, 2])
    with col1:
        st_lottie(lottie_animation, height=200, key="login_anim")
    with col2:
        with st.form(key='login_form'):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            login_button = st.form_submit_button(label="Login")
            if login_button:
                role = authenticate_user(username, password)
                if role:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = role
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

    # --- Add Forgot Password Button ---
    if st.button("Forgot Password?"):
        st.session_state['forgot_password_flow'] = 'enter_email'
        st.rerun()
    render_footer()

def signup_ui():
    # This function remains the same as before
    st.title("📝 Sign Up")
    col1, col2 = st.columns([1, 2])
    with col1:
        st_lottie(lottie_animation, height=200, key="signup_anim")
    with col2:
        with st.form(key='signup_form'):
            username = st.text_input("📛 New Username")
            email = st.text_input("✉️ Email")
            password = st.text_input("🔐 New Password", type="password")
            signup_button = st.form_submit_button(label="Sign Up")
            if signup_button:
                if not username or not password or not email or "@" not in email:
                    st.error("❌ Please fill in all fields with a valid email.")
                else:
                    if add_user(username, password, email, "user"):
                        send_welcome_email(recipient_email=email, username=username)
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = "user"
                        st.rerun()
                    else:
                        st.error("❌ Username or email already exists.")
    render_footer()
def forgot_password_ui():
    """Handles the entire multi-step forgot password process."""
    flow_step = st.session_state.get('forgot_password_flow', 'enter_email')

    if st.button("← Back to Login"):
        # Clear session state related to the flow and rerun
        for key in ['forgot_password_flow', 'reset_email', 'otp']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # --- Step 1: Ask for user's email ---
    if flow_step == 'enter_email':
        st.subheader("✉️ Enter Your Email Address")
        with st.form(key="email_form"):
            email = st.text_input("Registered Email")
            submit_email = st.form_submit_button("Send OTP")

            if submit_email:
                if check_email_exists(email):
                    otp = ''.join(random.choices(string.digits, k=6))
                    if send_otp_email(email, otp):
                        st.session_state['otp'] = otp
                        st.session_state['reset_email'] = email
                        st.session_state['forgot_password_flow'] = 'enter_otp'
                        st.success("An OTP has been sent to your email.")
                        st.rerun()
                    else:
                        st.error("Failed to send OTP. Please check server logs.")
                else:
                    st.error("This email is not registered with us.")

    # --- Step 2: Ask for OTP ---
    elif flow_step == 'enter_otp':
        st.subheader("🔐 Enter the OTP")
        st.info(f"An OTP was sent to {st.session_state.get('reset_email')}. Please enter it below.")
        with st.form(key="otp_form"):
            otp_input = st.text_input("One-Time Password (OTP)")
            submit_otp = st.form_submit_button("Verify OTP")

            if submit_otp:
                if otp_input == st.session_state.get('otp'):
                    st.session_state['forgot_password_flow'] = 'reset_password'
                    del st.session_state['otp'] # OTP is used, delete it
                    st.success("OTP verified!")
                    st.rerun()
                else:
                    st.error("Invalid OTP. Please try again.")

    # --- Step 3: Ask for new password ---
    elif flow_step == 'reset_password':
        st.subheader("🔑 Set Your New Password")
        with st.form(key="reset_password_form"):
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Re-enter New Password", type="password")
            submit_password = st.form_submit_button("Reset Password")

            if submit_password:
                if not new_password or not confirm_password:
                    st.error("Please fill in both password fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    email_to_update = st.session_state.get('reset_email')
                    if update_password_by_email(email_to_update, new_password):
                        st.success("Password updated successfully! You can now log in.")
                        # Clean up session state and end the flow
                        del st.session_state['forgot_password_flow']
                        del st.session_state['reset_email']
                        st.rerun()
                    else:
                        st.error("Failed to update password. Please try again.")

def about_ui():
    """Displays the 'About' page content."""
    st.title("💡 About the Mental Health Chatbot")
    st.markdown("---")
    st.subheader("Our Mission")
    st.write(
        "Our mission is to provide an accessible, anonymous, and supportive first point of contact "
        "for individuals seeking to understand and improve their mental well-being. We aim to break "
        "down the barriers of stigma and hesitation, offering a safe space where users can freely "
        "express their thoughts and feelings."
    )

    st.subheader("How It Works")
    st.write(
        "This chatbot is powered by Google's advanced Generative AI. When you interact with our bot, "
        "it processes your input to understand the context and sentiment, providing a thoughtful and "
        "empathetic response. It's designed to be a supportive listener, helping you navigate your "
        "feelings and providing information."
    )

    st.subheader("Key Features")
    st.markdown(
        """
        - **Secure Authentication:** Your conversations are private. With our secure login system, only you can access your chat history.
        - **Persistent Chat History:** Pick up right where you left off. Your past conversations are saved for your reference.
        - **Admin Dashboard:** An administrative view to monitor application usage and user feedback, ensuring continuous improvement.
        - **Feedback System:** Your feedback is crucial. We use a reinforcement learning approach to improve the chatbot's responses based on your ratings.
        """
    )
    st.info(
        "**Disclaimer:** This chatbot is not a substitute for professional medical advice, diagnosis, or treatment. "
        "It is a supportive tool, not a healthcare provider."
    )
    render_footer()

def contact_us_ui():
    """Displays the 'Contact Us' page content."""
    st.title("📨 Contact Us")
    st.markdown("---")
    st.write("We value your feedback and inquiries. Please feel free to reach out to us.")

    st.subheader("General & Technical Inquiries")
    st.write("For any questions, technical issues, or suggestions, please email us at:")
    st.markdown("📧 **zenchat.aibot@gmail.com** (placeholder)")

    st.subheader("Collaborations & Partnerships")
    st.write("Interested in collaborating? We'd love to hear from you. Reach out at:")
    st.markdown("🤝 **zenchat.aibot@gmail.com** (placeholder)")

    st.markdown("---")
    st.error(
        """
        **CRISIS SUPPORT - PLEASE READ**
        
        This contact information is **NOT** for emergencies. If you are in emotional distress or thinking about harming yourself, please reach out for help immediately.
        
        - **Tele MANAS (Govt. of India):** Call `14416` (24/7)
        - **Vandrevala Foundation:** Call or WhatsApp `9999666555` (24/7)
        """
    )
    render_footer()