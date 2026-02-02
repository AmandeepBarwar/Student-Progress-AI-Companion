import streamlit as st
import datetime
import pandas as pd

# -------------------------------
# Date & Time Helpers
# -------------------------------

def today_date():
    """Return today's date"""
    return datetime.date.today()

def current_week_range():
    """Return start and end date of current week"""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    return start, end


# -------------------------------
# Validation Helpers
# -------------------------------

def is_positive_number(value):
    """Check if value is positive number"""
    try:
        return float(value) > 0
    except Exception:
        return False


# -------------------------------
# Streamlit UI Helpers
# -------------------------------

def show_success(message):
    st.success(f"{message}")

def show_error(message):
    st.error(f"{message}")

def show_info(message):
    st.info(f"{message}")


# -------------------------------
# Data Helpers
# -------------------------------

def weekly_summary(df):
    """
    Generate weekly study summary from dataframe
    Expected columns: hours, problems, date
    """
    if df.empty:
        return None

    start, end = current_week_range()
    week_df = df[(df["date"] >= start) & (df["date"] <= end)]

    return {
        "total_hours": week_df["hours"].sum(),
        "total_problems": week_df["problems"].sum(),
        "days_studied": week_df["date"].nunique()
    }


def topics_not_covered(df, all_topics):
    """Return topics not studied in the current week"""
    if df.empty:
        return all_topics

    start, end = current_week_range()
    studied = df[(df["date"] >= start) & (df["date"] <= end)]["topic"].unique()
    return list(set(all_topics) - set(studied))


# -------------------------------
# File Helpers
# -------------------------------

def save_uploaded_file(uploaded_file, save_dir="assets/saved_solutions"):
    """Save uploaded file locally"""
    file_path = f"{save_dir}/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path
