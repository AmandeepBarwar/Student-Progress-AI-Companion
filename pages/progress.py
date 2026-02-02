import streamlit as st
import altair as alt
from database.mysql_db import fetch_logs

def render():
    st.header("📈 Progress Analysis")

    subject = st.selectbox("Subject", ["DSA", "Data Science"])
    df = fetch_logs(subject)

    if df.empty:
        st.info("No data available")
        return

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="date:T",
            y="hours:Q",
            tooltip=["topic", "hours"]
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)
