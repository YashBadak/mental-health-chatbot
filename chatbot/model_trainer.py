# chatbot/model_trainer_page.py
import streamlit as st
import pandas as pd
import os
import subprocess
import sys

def run_training_pipeline():
    """
    Executes the reinforcement learning training scripts in order.
    Returns the captured output from the scripts.
    """
    st.info("Starting model training pipeline... This may take several minutes.")
    log_output = ""
    
    # Define the sequence of scripts to run
    # You can add more scripts to this list if your pipeline grows
    scripts_to_run = [
        "reinforcement.feedback_processing",
        "reinforcement.convert_feedback_to_training_format",
        "reinforcement.train_reward_model"
    ]

    try:
        for script_module in scripts_to_run:
            log_output += f"--- Running {script_module} ---\n"
            
            # --- FIX: Use the '-m' flag to run as a module ---
            process = subprocess.run(
                [sys.executable, "-m", script_module],
                capture_output=True,
                text=True,
                check=True  # This will raise an exception if the script fails
            )
            log_output += process.stdout
            log_output += f"--- Finished {script_module} ---\n\n"
        
        st.success("Training pipeline completed successfully!")
        return log_output
    except FileNotFoundError as e:
        # This error is less likely with -m, but good to keep
        error_message = f"Error: A script was not found. Please check the file paths. Details: {e}"
        st.error(error_message)
        return log_output + error_message
    except subprocess.CalledProcessError as e:
        error_message = f"An error occurred while executing {e.cmd}:\n\n{e.stderr}"
        st.error(error_message)
        return log_output + error_message

def render_model_trainer_page():
    """Renders the UI for training the reward model."""
    st.title("🧠 Train Reward Model")
    st.markdown(
        "Use this section to improve the chatbot's performance by training it on the feedback "
        "provided by users."
    )
    st.markdown("---")

    # Display Feedback Data (moved from dashboard)
    st.header("📝 Review Feedback Data")
    feedback_file = "data/new_feedback.csv"
    if os.path.exists(feedback_file):
        try:
            feedback_df = pd.read_csv(feedback_file)
            if not feedback_df.empty:
                st.dataframe(feedback_df, use_container_width=True)
                if 'rating' in feedback_df.columns:
                    st.subheader("Feedback Ratings Distribution")
                    rating_counts = feedback_df['rating'].value_counts()
                    st.bar_chart(rating_counts)
            else:
                st.info("The feedback file is empty. No data to display or train on yet.")
        except pd.errors.EmptyDataError:
            st.info("The feedback file is empty. No data to display or train on yet.")
    else:
        st.warning("Feedback file (`data/new_feedback.csv`) not found.")

    st.markdown("---")

    # Training Section
    st.header("🚀 Start Training")
    st.warning("This process can be resource-intensive and may interrupt the chatbot service if run on the same machine. It's recommended to run this during off-peak hours.")
    
    if st.button("Start Training with Feedback Data"):
        with st.spinner("Training in progress... Please wait. You can view the log below."):
            output = run_training_pipeline()
            st.subheader("Training Log")
            st.code(output, language="log")