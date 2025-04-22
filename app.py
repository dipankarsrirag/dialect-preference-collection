import streamlit as st
import pandas as pd
import json
import os
import csv
import hashlib
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Preference Data Collector",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# File paths and directories
DATA_DIR = "user_data"
USERS_FILE = "users.json"
QUESTIONS_FILE = "questions.csv"

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)


# Authentication functions
def load_users():
    """Load users from JSON file or create empty users dict"""
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def hash_password(password):
    """Create a hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    """Register a new user"""
    users = load_users()

    if username in users:
        return False, "Username already exists"

    # Create new user
    hashed_password = hash_password(password)
    users[username] = {
        "password": hashed_password,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_users(users)
    return True, "Registration successful"


def authenticate(username, password):
    """Authenticate a user"""
    users = load_users()

    if username not in users:
        return False, "User not found"

    # Check password
    hashed_password = hash_password(password)
    if users[username]["password"] != hashed_password:
        return False, "Incorrect password"

    return True, "Authentication successful"


# Question handling functions
def load_questions():
    """Load questions from the CSV file"""
    try:
        questions = []
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                question = {
                    "sentence": row["translated"],
                    "option1": row["text"],
                    "option2": row["multi"],
                }
                questions.append(question)

            if not questions:
                raise FileNotFoundError("CSV file was empty or improperly formatted")
        return questions
    except FileNotFoundError:
        # Sample questions if file doesn't exist
        questions = [
            {
                "sentence": "The movie was really enjoyable and entertaining.",
                "option1": "I found the film to be quite delightful.",
                "option2": "The cinematic experience gave me great pleasure.",
            },
            {
                "sentence": "The company announced record profits this quarter.",
                "option1": "The firm reported unprecedented earnings for this period.",
                "option2": "The business revealed they had their most successful quarter yet.",
            },
            {
                "sentence": "The researchers discovered a new species of frog.",
                "option1": "Scientists identified a previously unknown amphibian of the frog family.",
                "option2": "The research team found a type of frog that was not known before.",
            },
        ]
        # Create a sample CSV file
        with open(QUESTIONS_FILE, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["text", "multi", "translated"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for q in questions:
                writer.writerow(
                    {
                        "text": q["option1"],
                        "multi": q["option2"],
                        "translated": q["sentence"],
                    }
                )
        return questions


def load_responses(username):
    """Load previous responses for a user"""
    data_file = os.path.join(DATA_DIR, f"{username}_data.json")
    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_response(username, response):
    """Save a response for a user"""
    data_file = os.path.join(DATA_DIR, f"{username}_data.json")
    responses = load_responses(username)

    # Check if this question has already been answered
    existing_index = None
    for i, r in enumerate(responses):
        if r["question_id"] == response["question_id"]:
            existing_index = i
            break

    if existing_index is not None:
        # Update existing response
        responses[existing_index] = response
    else:
        # Add new response
        responses.append(response)
        # Sort responses by question_id
        responses.sort(key=lambda x: x["question_id"])

    # Save responses to file
    with open(data_file, "w") as f:
        json.dump(responses, f, indent=4)

    return responses


def export_results(username, questions, responses):
    """Export results to a CSV file"""
    export_file = os.path.join(DATA_DIR, f"{username}_results.csv")
    try:
        with open(export_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "question_id",
                "user",
                "sentence",
                "option1",
                "option2",
                "selected_option",
                "selected_text",
                "confidence",
                "timestamp",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for response in responses:
                question = questions[response["question_id"]]
                row = {
                    "question_id": response["question_id"],
                    "user": username,
                    "sentence": question["sentence"],
                    "option1": question["option1"],
                    "option2": question["option2"],
                    "selected_option": response["selected_option"],
                    "selected_text": response["selected_text"],
                    "confidence": response["confidence"],
                    "timestamp": response["timestamp"],
                }
                writer.writerow(row)

        return True, export_file
    except Exception as e:
        return False, str(e)


def export_all_data():
    """Export all user data to a single CSV file"""
    export_file = "all_preference_data.csv"
    try:
        users = load_users()
        questions = load_questions()
        all_data = []

        # Get data from each user
        for username in users:
            try:
                responses = load_responses(username)

                for response in responses:
                    question_id = response["question_id"]
                    if question_id < len(questions):
                        question = questions[question_id]
                        entry = {
                            "question_id": question_id,
                            "user": username,
                            "sentence": question["sentence"],
                            "option1": question["option1"],
                            "option2": question["option2"],
                            "selected_option": response["selected_option"],
                            "selected_text": response["selected_text"],
                            "confidence": response["confidence"],
                            "timestamp": response["timestamp"],
                        }
                        all_data.append(entry)
            except Exception as e:
                print(f"Error processing {username}: {e}")

        # Write to CSV
        with open(export_file, "w", newline="", encoding="utf-8") as f:
            if all_data:
                fieldnames = all_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in all_data:
                    writer.writerow(row)
            else:
                writer = csv.writer(f)
                writer.writerow(["No data available"])

        return True, export_file
    except Exception as e:
        return False, str(e)


def delete_user(username):
    """Delete a user and their data"""
    users = load_users()

    try:
        data_file = os.path.join(DATA_DIR, f"{username}_data.json")
        if os.path.exists(data_file):
            os.remove(data_file)

        # Remove from users dict
        if username in users:
            del users[username]
            save_users(users)

        return True, f"User '{username}' deleted successfully"
    except Exception as e:
        return False, f"Failed to delete user: {e}"


def get_statistics():
    """Get statistics for all users and responses"""
    users = load_users()
    total_users = len(users)

    # Count responses
    total_responses = 0
    completed_users = 0

    # Get questions count
    question_count = 0
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(f)
            # Count rows, subtract header
            question_count = sum(1 for _ in csv_reader) - 1
    except FileNotFoundError:
        question_count = 0

    # Count responses across all users
    user_progress = {}
    for username in users:
        try:
            responses = load_responses(username)
            total_responses += len(responses)

            if question_count > 0:
                progress_percentage = (len(responses) / question_count) * 100
            else:
                progress_percentage = 0

            user_progress[username] = {
                "responses": len(responses),
                "progress": progress_percentage,
                "created_at": users[username].get("created_at", "Unknown"),
            }

            if len(responses) >= question_count:
                completed_users += 1
        except Exception:
            user_progress[username] = {
                "responses": 0,
                "progress": 0,
                "created_at": users[username].get("created_at", "Unknown"),
            }

    # Calculate completion rate
    completion_rate = 0
    if total_users > 0 and question_count > 0:
        completion_rate = (completed_users / total_users) * 100

    return {
        "total_users": total_users,
        "total_responses": total_responses,
        "question_count": question_count,
        "completion_rate": completion_rate,
        "user_progress": user_progress,
    }


# Main Streamlit UI functions
def login_page():
    st.title("Preference Data Collector")
    st.write("Please log in or register to continue.")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.header("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                success, message = authenticate(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.is_admin = username == "admin"
                    st.success(message)
                    # Replace experimental_rerun with rerun
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        st.header("Register")
        username = st.text_input("Username", key="register_username")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if not username or not password:
                st.error("Please enter both username and password")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = register_user(username, password)
                if success:
                    st.success(message)
                    st.info("You can now log in with your credentials")
                else:
                    st.error(message)


def question_page():
    username = st.session_state.username
    questions = load_questions()
    responses = load_responses(username)

    # Initialize question index if not set
    if "question_index" not in st.session_state:
        if len(responses) < len(questions):
            st.session_state.question_index = len(responses)
        else:
            st.session_state.question_index = 0

    # Create a sidebar with navigation options
    with st.sidebar:
        st.title("Navigation")

        # Calculate progress
        answered_count = len(responses)
        total_count = len(questions)
        progress_percentage = (
            (answered_count / total_count) * 100 if total_count > 0 else 0
        )

        st.progress(progress_percentage / 100)
        st.write(
            f"Progress: {answered_count}/{total_count} questions answered ({progress_percentage:.1f}%)"
        )

        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏪ First"):
                st.session_state.question_index = 0
                # Replace experimental_rerun with rerun
                st.rerun()

            if st.button("◀ Previous"):
                if st.session_state.question_index > 0:
                    st.session_state.question_index -= 1
                    # Replace experimental_rerun with rerun
                    st.rerun()

        with col2:
            if st.button("Next ▶"):
                if st.session_state.question_index < len(questions) - 1:
                    st.session_state.question_index += 1
                    # Replace experimental_rerun with rerun
                    st.rerun()

            if st.button("Last ⏩"):
                st.session_state.question_index = len(questions) - 1
                # Replace experimental_rerun with rerun
                st.rerun()

        # Jump to question
        st.write("Jump to question:")
        jump_to = st.number_input("", min_value=1, max_value=len(questions), step=1)
        if st.button("Go"):
            st.session_state.question_index = jump_to - 1
            # Replace experimental_rerun with rerun
            st.rerun()

        # Show progress summary button
        if st.button("View Progress Summary"):
            st.session_state.show_summary = True
            # Replace experimental_rerun with rerun
            st.rerun()

        # Logout button
        st.write("---")
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Replace experimental_rerun with rerun
            st.rerun()

    # Show summary page if needed
    if st.session_state.get("show_summary", False):
        summary_page()
        return

    # Display question
    current_index = st.session_state.question_index
    if current_index < len(questions):
        question = questions[current_index]

        # Check if this question has a previous response
        previous_response = None
        for response in responses:
            if response["question_id"] == current_index:
                previous_response = response
                break

        # Page header
        st.title("Preference Data Collector")
        st.subheader(f"Question {current_index + 1} of {len(questions)}")

        # Question status
        if previous_response:
            st.success("Question Status: Answered")
        else:
            st.warning("Question Status: Not Answered")

        # Display the question
        st.markdown("### Original Sentence")
        st.markdown(f"**{question['sentence']}**")

        st.markdown("### Which alternative do you prefer?")

        # Default value from previous response if it exists
        default_option = 0
        default_confidence = 3
        if previous_response:
            default_option = previous_response["selected_option"]
            default_confidence = previous_response["confidence"]

        # Create a form for input
        with st.form(key=f"question_form_{current_index}"):
            selected_option = st.radio(
                "Select one option:",
                options=[question["option1"], question["option2"]],
                index=default_option - 1 if default_option > 0 else None,
            )

            confidence = st.slider(
                "How confident are you in your choice?",
                min_value=1,
                max_value=5,
                value=default_confidence,
                step=1,
                help="1 = Low confidence, 5 = High confidence",
            )

            submit_button = st.form_submit_button("Save Answer")

            if submit_button:
                # Create response object
                option_value = 1 if selected_option == question["option1"] else 2
                response = {
                    "question_id": current_index,
                    "user": username,
                    "sentence": question["sentence"],
                    "selected_option": option_value,
                    "selected_text": selected_option,
                    "confidence": confidence,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Save response
                updated_responses = save_response(username, response)

                st.success("Response saved successfully!")

                # Auto-navigate to next question if not the last one
                if current_index < len(questions) - 1:
                    st.session_state.question_index += 1
                    # Replace experimental_rerun with rerun
                    st.rerun()
                else:
                    st.info("You've reached the last question!")
    else:
        st.error("Question index out of range")


def summary_page():
    username = st.session_state.username
    questions = load_questions()
    responses = load_responses(username)

    st.title("Progress Summary")

    # Progress stats
    total_questions = len(questions)
    answered_questions = len(responses)
    completion_percentage = (
        (answered_questions / total_questions) * 100 if total_questions > 0 else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Questions", total_questions)
    col2.metric("Answered Questions", answered_questions)
    col3.metric("Completion Rate", f"{completion_percentage:.1f}%")

    # List of questions with answered status
    st.subheader("Question Status")

    # Create a DataFrame for display
    answered_ids = [r["question_id"] for r in responses]
    status_data = []

    for i, question in enumerate(questions):
        # Truncate question text
        truncated_text = (
            question["sentence"][:50] + "..."
            if len(question["sentence"]) > 50
            else question["sentence"]
        )
        status = "✅ Answered" if i in answered_ids else "❌ Not Answered"

        status_data.append(
            {"Question #": i + 1, "Question": truncated_text, "Status": status}
        )

    status_df = pd.DataFrame(status_data)

    # Display with styling
    st.dataframe(
        status_df,
        column_config={
            "Question #": st.column_config.Column(
                "Question #",
                width="small",
            ),
            "Status": st.column_config.Column(
                "Status",
                width="small",
            ),
        },
        hide_index=True,
    )

    # Add buttons to jump to questions
    st.subheader("Go to specific question")

    # Create rows of 5 buttons each
    num_buttons_per_row = 5
    num_questions = len(questions)
    num_rows = (
        num_questions + num_buttons_per_row - 1
    ) // num_buttons_per_row  # Ceiling division

    for row in range(num_rows):
        cols = st.columns(num_buttons_per_row)
        for col_idx in range(num_buttons_per_row):
            q_idx = row * num_buttons_per_row + col_idx
            if q_idx < num_questions:
                q_num = q_idx + 1
                status = "✅" if q_idx in answered_ids else "❌"
                if cols[col_idx].button(f"{status} Q{q_num}", key=f"goto_{q_idx}"):
                    st.session_state.question_index = q_idx
                    st.session_state.show_summary = False
                    # Replace experimental_rerun with rerun
                    st.rerun()

    # Export button
    if st.button("Export My Results"):
        success, result = export_results(username, questions, responses)
        if success:
            st.success(f"Results exported to {result}")

            # Provide download button
            with open(result, "r") as f:
                st.download_button(
                    label="Download CSV",
                    data=f,
                    file_name=f"{username}_results.csv",
                    mime="text/csv",
                )
        else:
            st.error(f"Failed to export results: {result}")

    # Back button
    if st.button("Back to Questions"):
        st.session_state.show_summary = False
        # Replace experimental_rerun with rerun
        st.rerun()


def admin_page():
    st.title("Admin Panel - Preference Data Collector")

    tab1, tab2, tab3 = st.tabs(["Users", "Export Data", "Statistics"])

    # Users tab
    with tab1:
        st.header("Registered Users")

        # Get user statistics
        stats = get_statistics()
        user_progress = stats["user_progress"]

        # Create a DataFrame for display
        user_data = []
        for username, data in user_progress.items():
            user_data.append(
                {
                    "Username": username,
                    "Registration Date": data["created_at"],
                    "Responses": data["responses"],
                    "Progress": f"{data['progress']:.1f}%",
                    "Actions": username,
                }
            )

        user_df = pd.DataFrame(user_data)

        # Display user table
        if not user_df.empty:
            st.dataframe(user_df, hide_index=True)

            # User deletion
            st.subheader("Delete User")
            delete_username = st.selectbox(
                "Select user to delete",
                options=[user for user in user_progress.keys() if user != "admin"],
            )

            if delete_username and st.button("Delete Selected User"):
                success, message = delete_user(delete_username)
                if success:
                    st.success(message)
                    # Replace experimental_rerun with rerun
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.info("No users registered yet.")

    # Export Data tab
    with tab2:
        st.header("Export All User Data")
        st.write("Export all user data to a single CSV file for analysis")

        if st.button("Export All Data"):
            success, result = export_all_data()
            if success:
                st.success(f"Data exported successfully to {result}")

                # Provide download button
                with open(result, "r") as f:
                    st.download_button(
                        label="Download CSV",
                        data=f,
                        file_name="all_preference_data.csv",
                        mime="text/csv",
                    )
            else:
                st.error(f"Failed to export data: {result}")

    # Statistics tab
    with tab3:
        st.header("Collection Statistics")

        # Get statistics
        stats = get_statistics()

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Users", stats["total_users"])
        col2.metric("Total Questions", stats["question_count"])
        col3.metric("Total Responses", stats["total_responses"])
        col4.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")

        # Display user progress chart
        if stats["user_progress"]:
            st.subheader("User Progress")

            chart_data = pd.DataFrame(
                {
                    "Username": list(stats["user_progress"].keys()),
                    "Progress (%)": [
                        data["progress"] for data in stats["user_progress"].values()
                    ],
                }
            )

            st.bar_chart(chart_data.set_index("Username"))

        # Refresh button
        if st.button("Refresh Statistics"):
            # Replace experimental_rerun with rerun
            st.rerun()


# Main app logic
def main():
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Display appropriate page based on login state
    if not st.session_state.logged_in:
        login_page()
    else:
        # Check if admin
        if st.session_state.get("is_admin", False):
            admin_page()
        else:
            question_page()


if __name__ == "__main__":
    main()
