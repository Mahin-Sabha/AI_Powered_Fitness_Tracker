import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
import sqlite3
import datetime
import time
import os
from exercises import DumbbellHighCurl, LateralRaise, HammerCurl, FrontRaise, StandingSideLegRaise
from dashboard import show_dashboard
from chatbot import show_chatbot

# Streamlit page configuration
st.set_page_config(
    page_title="AI Fitness Trainer",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Helper function to load user profile
def _load_user_profile(email, name):
    """Load user profile and generate avatar details"""
    avatar_letter = name[0].upper() if name else "G"
    # Generate a color based on email hash
    colors = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#ec4899"]
    avatar_color = colors[hash(email) % len(colors)]
    return name, avatar_letter, avatar_color

# Get query parameters
qp = st.query_params

# Read user from query params, then session, with guest defaults
user_email = qp.get("email", [None])[0] if isinstance(qp.get("email"), list) else qp.get("email")
user_name_q = qp.get("username", [None])[0] if isinstance(qp.get("username"), list) else qp.get("username")

# Check environment variables only for email, not username
if not user_email:
    user_email = os.environ.get("USER_EMAIL") if "os" in globals() else None
    if not user_email:
        try:
            import os as _os
            user_email = _os.environ.get("USER_EMAIL")
        except Exception:
            user_email = None

# Fallback to session_state
if not user_email:
    user_email = st.session_state.get("user_email")
if not user_name_q:
    user_name_q = st.session_state.get("user_name")

# If still missing, use guest defaults
if not user_email:
    user_email = "guest@example.com"
if not user_name_q:
    user_name_q = "Guest"

# Persist to session_state
st.session_state["user_email"] = user_email
st.session_state["user_name"] = user_name_q

user_name, avatar_letter, avatar_color = _load_user_profile(user_email, user_name_q)

# Custom CSS for modern dashboard UI
custom_css = """
<style>
    .main {
        background-color: #121212 !important;
        color: #E0E0E0 !important;
    }

    body {
        color: #E0E0E0 !important;
    }

    .title-container {
        text-align: center;
        margin-bottom: 20px;
    }

    .title-text {
        font-size: 36px;
        font-weight: 700;
        color: #36D7E8;
        text-shadow: 0 0 10px rgba(54,215,232,0.5);
    }

    .sidebar .sidebar-content {
        background-color: #1E1E2F !important;
        border-radius: 10px;
        padding: 20px;
    }

    .stSelectbox > div > div {
        background-color: #1E1E2F !important;
        border: 2px solid #36D7E8 !important;
        border-radius: 8px !important;
        color: #E0E0E0 !important;
    }

    .stButton > button {
        background: linear-gradient(90deg, #36D7E8, #00FFF7) !important;
        border: none !important;
        border-radius: 20px !important;
        color: black !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        cursor: pointer !important;
        box-shadow: 0 0 12px rgba(54,215,232,0.6) !important;
    }

    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(0,255,247,0.78) !important;
    }

    .metric-container {
        background-color: #1E1E2F;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(54,215,232,0.3);
        margin-bottom: 20px;
    }

    .feedback-text {
        background-color: #1E1E2F;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(54,215,232,0.3);
        font-size: 18px;
        font-weight: 500;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Centered title
st.markdown('<div class="title-container"><h1 class="title-text">💪 AI Fitness Trainer</h1></div>', unsafe_allow_html=True)

# Profile card for sidebar
profile_card = f'''
<div style="width:100%;background:#222530;border:1px solid #2f3240;border-radius:12px;padding:0.9rem 1rem;margin-bottom:0.75rem;">
    <div style="display:flex;align-items:center;gap:0.85rem;">
        <div style="min-width:36px;height:36px;border-radius:50%;background:{avatar_color};color:#ffffff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:18px;">{avatar_letter}</div>
        <div style="display:flex;flex-direction:column;gap:2px;">
            <div style="font-weight:700;font-size:15px;color:#e8eaf2;line-height:1.2;">{user_name}</div>
            <div style="font-size:12px;color:#c3c6d4;line-height:1.2;">{user_email}</div>
        </div>
    </div>
</div>
'''

st.sidebar.markdown(profile_card, unsafe_allow_html=True)

# Divider beneath the profile box
st.sidebar.markdown('<div style="height:1px;background:#343740;margin:0 0 0.75rem 0;"></div>', unsafe_allow_html=True)

st.sidebar.markdown(
        """
        <style>
    /* Sidebar layout to push logout to bottom */
    div[data-testid="stSidebar"] > div:first-child {
        height: 100%;
    }
    div[data-testid="stSidebarContent"] {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .sidebar-spacer {
        flex: 1 1 auto;
        min-height: 256px;
    }
        div[data-testid="stSidebar"] .stButton>button {
                width: 100%;
                margin-bottom: 0.35rem;
                padding: 0.6rem 0.9rem;
                border-radius: 10px;
                border: 1px solid #2d2f36;
                background: #1f2330;
                color: #e2e8f0;
                font-weight: 600;
                transition: all 0.2s ease;
                text-align: left;
        }
        div[data-testid="stSidebar"] .stButton>button:hover {
                border-color: #8b5cf6;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.35);
        }
        div[data-testid="stSidebar"] .stButton>button:focus:not(:active) {
                border-color: #8b5cf6;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.35);
        }
        </style>
        """,
        unsafe_allow_html=True,
)

if "page" not in st.session_state:
        st.session_state.page = "Exercises"

if st.sidebar.button("Exercises", key="nav_exercises"):
        st.session_state.page = "Exercises"
if st.sidebar.button("Dashboard", key="nav_dashboard"):
        st.session_state.page = "Dashboard"
if st.sidebar.button("Chatbot", key="nav_chatbot"):
        st.session_state.page = "Chatbot"

# Spacer to push logout button to bottom
st.sidebar.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

# Logout button at the bottom of the sidebar
if st.sidebar.button("Logout", key="nav_logout", type="secondary"):
    # Clear local session state
    for key in ["user_email", "user_name", "avatar_email", "avatar_color", "running", "workout_start", "exercise_start", "current_exercise"]:
        if key in st.session_state:
            st.session_state.pop(key)
    # Set logout flag
    st.session_state["logging_out"] = True
    st.rerun()

# Handle logout redirect
if st.session_state.get("logging_out", False):
    st.markdown(
        """
        <meta http-equiv="refresh" content="0; url=http://localhost:5000/" />
        <script>
        window.location.href = "http://localhost:5000/";
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# Page handling
if "page" not in st.session_state:
    st.session_state.page = "Exercises"

page = st.session_state.page

# Initialize workout session states
if 'workout_started' not in st.session_state:
    st.session_state.workout_started = False
if 'workout_paused' not in st.session_state:
    st.session_state.workout_paused = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'pause_start' not in st.session_state:
    st.session_state.pause_start = None
if 'total_pause_time' not in st.session_state:
    st.session_state.total_pause_time = 0
if 'exercise_start_time' not in st.session_state:
    st.session_state.exercise_start_time = None
if 'current_exercise' not in st.session_state:
    st.session_state.current_exercise = None
if 'exercise_durations' not in st.session_state:
    st.session_state.exercise_durations = {}
if 'total_reps_per_exercise' not in st.session_state:
    st.session_state.total_reps_per_exercise = {}

def log_workout_to_db(user_email, exercise, reps, duration_seconds):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO workout_logs (user_email, exercise, reps, duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_email, exercise, reps, duration_seconds, datetime.datetime.now()))
        conn.commit()
        conn.close()
        st.write(f"Debug: Successfully logged to DB - {exercise}: {reps} reps")
    except Exception as e:
        st.write(f"Debug: Error logging to DB: {e}")

if page == "Exercises":
    # Controls in main area
    st.header("Controls")

    exercise_options = {
        "Dumbbell High Curl": DumbbellHighCurl(),
        "Lateral Raise": LateralRaise(),
        "Hammer Curl": HammerCurl(),
        "Front Raise": FrontRaise(),
        "Standing Side Leg Raise": StandingSideLegRaise()
    }

    selected_exercise = st.selectbox("Select an exercise:", list(exercise_options.keys()))

    # Workout control buttons
    col_start, col_stop, col_end = st.columns(3)
    with col_start:
        if st.button("Start Workout", disabled=st.session_state.workout_started and not st.session_state.workout_paused):
            if not st.session_state.workout_started:
                st.session_state.workout_started = True
                st.session_state.workout_paused = False
                st.session_state.start_time = time.time()
                st.session_state.exercise_start_time = time.time()
                st.session_state.current_exercise = selected_exercise
                st.session_state.current_exercise_instance = exercise_options[selected_exercise]
                st.session_state.exercise_durations = {}
                st.session_state.total_reps_per_exercise = {}
                st.session_state.total_pause_time = 0
                st.rerun()
            elif st.session_state.workout_paused:
                # Accumulate pause time
                if st.session_state.pause_start:
                    pause_duration = time.time() - st.session_state.pause_start
                    st.session_state.total_pause_time += pause_duration
                st.session_state.workout_paused = False
                st.session_state.pause_start = None
                st.session_state.exercise_start_time = time.time()
                st.rerun()

    with col_stop:
        if st.button("Stop Workout", disabled=not st.session_state.workout_started or st.session_state.workout_paused):
            st.session_state.workout_paused = True
            st.session_state.pause_start = time.time()
            st.rerun()

    with col_end:
        if st.button("End Workout", disabled=not st.session_state.workout_started):
            # Calculate final durations
            current_time = time.time()
            if st.session_state.current_exercise:
                duration = current_time - st.session_state.exercise_start_time - st.session_state.total_pause_time
                st.session_state.exercise_durations[st.session_state.current_exercise] = st.session_state.exercise_durations.get(st.session_state.current_exercise, 0) + duration

            # Log to DB
            user_email = st.session_state.get("user_email", "guest@example.com")
            for ex, dur in st.session_state.exercise_durations.items():
                reps = st.session_state.total_reps_per_exercise.get(ex, 0)
                st.write(f"Debug: Logging {ex} - reps: {reps}, duration: {int(dur)}")  # Debug line
                log_workout_to_db(user_email, ex, reps, int(dur))

            # Reset states
            st.session_state.workout_started = False
            st.session_state.workout_paused = False
            st.session_state.start_time = None
            st.session_state.pause_start = None
            st.session_state.total_pause_time = 0
            st.session_state.exercise_start_time = None
            st.session_state.current_exercise = None
            st.session_state.current_exercise_instance = None
            st.session_state.exercise_durations = {}
            st.session_state.total_reps_per_exercise = {}
            st.rerun()

    run = st.session_state.workout_started and not st.session_state.workout_paused

    # Main dashboard area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Live Camera Feed")
        FRAME_WINDOW = st.empty()

    with col2:
        st.subheader("Metrics")
        if st.session_state.workout_started:
            total_time = int(time.time() - st.session_state.start_time - st.session_state.total_pause_time)
            exercise_time = int(time.time() - st.session_state.exercise_start_time - st.session_state.total_pause_time)
            st.metric("Total Workout Time", f"{total_time // 60}:{total_time % 60:02d}")
            st.metric("Current Exercise Time", f"{exercise_time // 60}:{exercise_time % 60:02d}")
        reps_metric = st.empty()
        feedback_text = st.empty()

    # Camera and pose logic
    if run:
        cap = cv2.VideoCapture(0)
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        pose = mp_pose.Pose()

        # Use persistent exercise instance from session state
        if 'current_exercise_instance' not in st.session_state or st.session_state.current_exercise != selected_exercise:
            st.session_state.current_exercise_instance = exercise_options[selected_exercise]
            st.session_state.current_exercise = selected_exercise

        exercise = st.session_state.current_exercise_instance

        while run:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                landmarks = results.pose_landmarks.landmark

                form_correct = exercise.detect_form(landmarks)
                exercise.count_reps(landmarks, form_correct)

                feedback_msg = exercise.give_feedback()

                cv2.putText(frame, f"Reps: {exercise.count}", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            else:
                feedback_msg = "Incorrect Form"

            FRAME_WINDOW.image(frame, channels="BGR")
            reps_metric.metric("Reps", exercise.count)
            feedback_text.markdown(f'<div class="feedback-text">Feedback: {feedback_msg}</div>', unsafe_allow_html=True)

            # Update reps in session state
            st.session_state.total_reps_per_exercise[selected_exercise] = exercise.count

        cap.release()
    else:
        FRAME_WINDOW.image("https://via.placeholder.com/640x480/1E1E2F/FFFFFF?text=Camera+Off", width='stretch')
        reps_metric.metric("Reps", 0)
        feedback_text.markdown('<div class="feedback-text">Feedback: Camera is off</div>', unsafe_allow_html=True)

elif page == "Dashboard":
    show_dashboard()
elif page == "Chatbot":
    show_chatbot()