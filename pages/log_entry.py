import streamlit as st
from database.mysql_db import insert_log
from utils.helpers import today_date, show_success, show_error

def render():
    st.header("📝 Log Study Session")

    subject = st.selectbox("Subject", ["DSA", "Data Science"])
    topic = st.text_input("Topic")
    hours = st.number_input("Hours Studied", min_value=0.0, step=0.5)
    problems = st.number_input("Problems Solved", min_value=0, step=1)
    date = st.date_input("Date", today_date())

    if st.button("Save Log"):
        if not topic:
            show_error("Topic cannot be empty")
            return
        insert_log(subject, topic, hours, problems, date)
        show_success("Study log saved")
