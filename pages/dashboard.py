import streamlit as st
from database.mysql_db import fetch_logs
from utils.helpers import weekly_summary

def render():
    st.header("📊 Weekly Dashboard")

    subject = st.selectbox("Subject", ["DSA", "Data Science"])
    df = fetch_logs(subject)

    summary = weekly_summary(df)

    if not summary:
        st.info("No study activity this week")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Hours Studied", summary["total_hours"])
    col2.metric("Problems Solved", summary["total_problems"])
    col3.metric("Days Studied", summary["days_studied"])
