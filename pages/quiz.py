import streamlit as st

QUESTIONS = {
    "DSA": {
        "What is the time complexity of binary search?": "O(log n)"
    },
    "Data Science": {
        "What does overfitting mean?": "Poor generalization"
    }
}

def render():
    st.header("🧠 Quick Quiz")

    subject = st.selectbox("Subject", QUESTIONS.keys())
    question = st.selectbox("Question", QUESTIONS[subject].keys())
    answer = st.text_input("Your Answer")

    if st.button("Check Answer"):
        correct = QUESTIONS[subject][question]
        if answer.strip().lower() in correct.lower():
            st.success("Correct 🎉")
        else:
            st.error(f"Incorrect. Correct answer: {correct}")
