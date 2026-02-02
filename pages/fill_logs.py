import streamlit as st
from database.mysql_db import fetch_logs

def render():
    st.header("📋 View Logs")

    subject = st.selectbox("Select Subject", ["DSA", "Data Science"])
    df = fetch_logs(subject)

    if df.empty:
        st.info("No logs found")
    else:
        st.dataframe(df, use_container_width=True)
