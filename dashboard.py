import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import os

def _db_path() -> str:
    try:
        base = os.path.dirname(__file__)
    except Exception:
        base = os.getcwd()
    return os.path.join(base, "users.db")


def _load_user_logs(user_email: str) -> pd.DataFrame:
    try:
        conn = sqlite3.connect(_db_path())
        df = pd.read_sql_query(
            "SELECT user_email, exercise, reps, duration_seconds, created_at FROM workout_logs WHERE user_email = ? ORDER BY created_at DESC",
            conn,
            params=(user_email,),
            parse_dates=["created_at"],
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame(columns=["user_email", "exercise", "reps", "duration_seconds", "created_at"])


def _get_user_weight(user_email: str) -> float | None:
    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()
        cur.execute("SELECT weight FROM users WHERE email = ? LIMIT 1", (user_email,))
        row = cur.fetchone()
        conn.close()
        return float(row[0]) if row and row[0] is not None else None
    except Exception:
        return None


def show_dashboard():
    """Display the fitness dashboard with statistics and progress tracking."""
    st.title("📊 Fitness Dashboard")
    user_email = st.session_state.get("user_email", "guest@example.com")
    user_weight = _get_user_weight(user_email)
    df = _load_user_logs(user_email)
    
    # Create tabs for different dashboard sections
    tab1, tab2, tab3 = st.tabs(["Overview", "Progress", "Statistics"])
    
    with tab1:
        st.header("Today's Overview")
        col1, col2, col3, col4 = st.columns(4)

        today = pd.Timestamp(datetime.now().date())
        df_today = df[df["created_at"].dt.date == today.date()] if not df.empty else pd.DataFrame()
        total_reps = int(df_today["reps"].sum()) if not df_today.empty else 0
        total_duration = int(df_today["duration_seconds"].sum()) if not df_today.empty else 0
        exercises_done = df_today["exercise"].nunique() if not df_today.empty else 0
        minutes = total_duration / 60.0
        # Calorie estimate uses user weight when available (MET 6 strength training baseline)
        if user_weight:
            calories_from_time = (6 * 3.5 * user_weight / 200) * minutes
            calories_from_reps = (total_reps * 0.2) * (user_weight / 70)
            calories = int(calories_from_time + calories_from_reps)
        else:
            calories = int(total_reps * 0.5 + minutes * 3)

        with col1:
            st.metric("Total Reps", f"{total_reps}")
        with col2:
            st.metric("Calories Burned", f"{calories}")
        with col3:
            st.metric("Exercises Done", f"{exercises_done}")
        with col4:
            mins = total_duration // 60
            st.metric("Duration", f"{mins} min")
    
    with tab2:
        st.header("Weekly Progress")
        if df.empty:
            st.info("No data yet. Start exercising to build your progress!")
        else:
            last7 = pd.Timestamp(datetime.now().date()) - pd.Timedelta(days=6)
            d7 = df[df["created_at"].dt.date >= last7.date()].copy()
            d7["date"] = d7["created_at"].dt.date
            agg = d7.groupby("date").agg({"reps": "sum", "duration_seconds": "sum"}).reset_index()
            agg = agg.sort_values("date")
            agg["date"] = pd.to_datetime(agg["date"])
            chart_df = agg.set_index("date")["reps"]
            st.line_chart(chart_df)
            st.caption("Reps per day for the last 7 days")
    
    with tab3:
        st.header("Exercise Statistics")
        col1, col2 = st.columns(2)
        if df.empty:
            with col1:
                st.subheader("Exercise Breakdown")
                st.info("No data yet. Start exercising to see statistics!")
            with col2:
                st.subheader("Session Summary")
                st.info("No data yet.")
        else:
            with col1:
                st.subheader("Exercise Breakdown")
                breakdown = df.groupby("exercise").agg({"reps": "sum", "duration_seconds": "sum"}).sort_values("reps", ascending=False)
                st.bar_chart(breakdown["reps"])
            with col2:
                st.subheader("Session Summary")
                st.dataframe(df[["created_at", "exercise", "reps", "duration_seconds"]], width="stretch")