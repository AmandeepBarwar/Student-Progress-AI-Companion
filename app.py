import streamlit as st
from pages import home, log_entry, fill_logs, progress, dashboard, quiz
from utils.styles import load_css
from database.mysql_db import ensure_table

st.set_page_config(page_title="Student Progress AI Companion", layout="wide")

ensure_table()
load_css()

if "page" not in st.session_state:
    st.session_state.page = "Home"

PAGES = {
    "Home": home.render,
    "Log Entry": log_entry.render,
    "Fill Logs": fill_logs.render,
    "Progress": progress.render,
    "Dashboard": dashboard.render,
    "Quiz": quiz.render
}

with st.sidebar:
    st.title("Navigation")
    choice = st.radio("Go to", PAGES.keys())
    st.session_state.page = choice

PAGES[st.session_state.page]()
