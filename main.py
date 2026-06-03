import streamlit as st
import pandas as pd
import datetime
import os
import altair as alt
import cv2
import numpy as np
from sqlalchemy import create_engine
import av  # Required for packaging video processor frames in newer streamlit-webrtc versions
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

# --------------------------------
# 🗄️ POSTGRESQL DATABASE CONNECTION (Updated with SQLAlchemy Contexts)
# --------------------------------
DB_URL = os.getenv("DATABASE_URL")

def get_sqla_engine():
    """Creates a clean SQLAlchemy connection engine for database operations."""
    if DB_URL:
        uri = DB_URL.replace("postgres://", "postgresql://") if DB_URL.startswith("postgres://") else DB_URL
        return create_engine(uri)
    else:
        return create_engine("postgresql://postgres:npg_FlwQbk3izPg0@localhost:5432/student_progress")

def ensure_table():
    """Creates the study_logs table automatically if it doesn't exist."""
    sql = """
    CREATE TABLE IF NOT EXISTS study_logs (
        id SERIAL PRIMARY KEY,
        subject VARCHAR(255) NOT NULL,
        topic VARCHAR(255) NOT NULL,
        hours_studied FLOAT NOT NULL,
        problems_solved INT NOT NULL,
        date DATE NOT NULL
    );
    """
    try:
        engine = get_sqla_engine()
        with engine.begin() as conn:
            conn.exec_driver_sql(sql)
    except Exception as e:
        st.error(f"❌ Database initialization failed: {e}")

def insert_log(subject, topic, hours, problems, date_value):
    """Inserts a new study log using safe execution contexts."""
    sql = """
    INSERT INTO study_logs (subject, topic, hours_studied, problems_solved, date)
    VALUES (%s, %s, %s, %s, %s);
    """
    try:
        engine = get_sqla_engine()
        with engine.begin() as conn:
            conn.exec_driver_sql(sql, (subject, topic, float(hours), int(problems), date_value))
    except Exception as e:
        st.error(f"❌ Failed to save record: {e}")

def fetch_subject_df(subject):
    """Fetches study records via SQLAlchemy connection to cleanly return a pandas DataFrame without warnings."""
    sql = """
    SELECT subject AS "Subject", topic AS "Topic", 
           hours_studied AS "Hours Studied", problems_solved AS "Problems Solved", date AS "Date" 
    FROM study_logs WHERE subject = %s;
    """
    df = pd.DataFrame(columns=["Subject", "Topic", "Hours Studied", "Problems Solved", "Date"])
    try:
        engine = get_sqla_engine()
        with engine.connect() as conn:
            df = pd.read_sql_query(sql, conn, params=(subject,))
    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")
    return df

# Initialize database schemas cleanly before page configurations boot
ensure_table()

# --------------------------------
# 🎓 PAGE CONFIG
# --------------------------------
st.set_page_config(
    page_title="Student Progress AI Companion",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------
# 🎨 CSS STYLING
# --------------------------------
st.markdown("""
<style>
    .stButton > button {
        background: #5564F5;
        min-width: 350px !important;
        max-width: 100%;
        min-height: 3rem !important;
        height: 3rem !important;
        padding: 1.5rem !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        font-weight: 700 !important;
        transition: transform 0.3s ease;
        color: white;
    }
    .stButton > button:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    .main-header-wrapper {
        display: block;
        margin: 0 auto;
        padding: 0 1.5rem;
        max-width: 1500px;
        width: 100%;
        box-sizing: border-box;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
    .main-header {
        text-align: left;
        padding: 0.75rem 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------
# 🧭 SESSION STATE
# --------------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "subject" not in st.session_state:
    st.session_state.subject = None
if "quiz_subject" not in st.session_state:
    st.session_state.quiz_subject = None

# --------------------------------
# 🏠 HOME PAGE
# --------------------------------
def home_page():
    st.markdown("""
    <div class="main-header-wrapper">
        <div class="main-header">
            <h1>🎓 Student Progress AI Companion</h1>
            <h3>You're on your way to mastery!</h3>
            <p>Log your daily study activities for better analysis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🚀 Quick Navigation")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Get Your Weekly Insights")
        if st.button("📘 DSA", key="dsa_btn"):
            st.session_state.subject = "DSA"
            st.session_state.page = "progress"
            st.rerun()
    with col2:
        st.markdown("### ")
        if st.button("📊 Data Science", key="ds_btn"):
            st.session_state.subject = "Data Science"
            st.session_state.page = "progress"
            st.rerun()

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### Engage With Activities")
        if st.button("🧾 Fill Out Your Learning Logs"):
            st.session_state.page = "log_entry"
            st.rerun()
    with col4:
        st.markdown("### ")
        if st.button("🧠 Knowledge Quiz"):
            st.session_state.page = "quiz_subject"
            st.rerun()

    st.markdown("---")
    st.subheader("🔔 Weekly Study Notifications")

    subjects = {
        "DSA": [
            "Arrays", "Strings", "Linked List", "Stack", "Queue",
            "Trees", "Graphs", "Dynamic Programming", "Sorting", "Searching"
        ],
        "Data Science": [
            "Python", "Pandas", "NumPy", "Statistics", "Machine Learning",
            "Deep Learning", "Data Preprocessing", "Visualization", "SQL", "EDA"
        ]
    }

    current_week = datetime.date.today().isocalendar().week
    current_year = datetime.date.today().year
    notifications = []

    for subject, topics in subjects.items():
        try:
            df = fetch_subject_df(subject)
        except Exception:
            df = pd.DataFrame()

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"])
            df["Week"] = df["Date"].dt.isocalendar().week
            df["Year"] = df["Date"].dt.year
            week_df = df[(df["Week"] == current_week) & (df["Year"] == current_year)]
            studied_topics = set(week_df["Topic"].unique())
            not_studied = [t for t in topics if t not in studied_topics]
            if not_studied:
                notifications.append(
                    f"📘 {subject} Reminder: You haven’t studied these topics this week → " +
                    ", ".join(not_studied)
                )
            else:
                notifications.append(f"✅ Great job! You’ve studied all {subject} topics this week!")
        else:
            notifications.append(f"ℹ No study data for {subject} yet. Start logging your progress!")

    for note in notifications:
        st.info(note)

# --------------------------------
# ✏ LOG ENTRY PAGE
# --------------------------------
def log_entry_page():
    st.markdown("## 🧾 Fill Out Your Learning Logs")
    st.markdown("Choose a subject to add your daily progress:")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧩 Log for DSA"):
            st.session_state.subject = "DSA"
            st.session_state.page = "fill_logs"
            st.rerun()
    with col2:
        if st.button("📊 Log for Data Science"):
            st.session_state.subject = "Data Science"
            st.session_state.page = "fill_logs"
            st.rerun()

    if st.button("⬅ Back to Home"):
        st.session_state.page = "home"
        st.rerun()

# --------------------------------
# 📷 WEB CAMERA STREAM PROCESSOR
# --------------------------------
class FaceExpressionTransformer(VideoProcessorBase):
    """Processes real-time camera frames securely sent over WebRTC from the user's browser."""
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(40, 40))
        face_detected = len(faces) > 0
        frame_color = (0, 255, 0) if face_detected else (100, 100, 100)
        status = "✅ Person Detected — Studying" if face_detected else "⏸ Waiting for Person"

        for (x, y, w_face, h_face) in faces:
            cv2.rectangle(img, (x, y), (x + w_face, y + h_face), frame_color, 2)
            
        h, w = img.shape[:2]
        cv2.rectangle(img, (0, 0), (w, h), frame_color, 3)
        cv2.putText(img, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, frame_color, 2)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# --------------------------------
# 📋 FILL LOGS PAGE
# --------------------------------
def fill_logs_page(subject):
    st.markdown(f"## ✏ Add {subject} Learning Logs")
    st.markdown("**📷 Browser WebRTC Camera: Secure tracking optimized for Cloud Deployments.**")

    dsa_topics = [
        "Arrays", "Strings", "Linked List", "Stack", "Queue",
        "Trees", "Graphs", "Dynamic Programming", "Sorting", "Searching"
    ]
    ds_topics = [
        "Python", "Pandas", "NumPy", "Statistics", "Machine Learning",
        "Deep Learning", "Data Preprocessing", "Visualization", "SQL", "EDA"
    ]
    topics = dsa_topics if subject == "DSA" else ds_topics

    st.markdown("### Step 1 — Select Topic")
    topic = st.selectbox(f"Select {subject} Topic", topics, key="monitor_topic")

    try:
        df = fetch_subject_df(subject)
    except Exception:
        df = pd.DataFrame(columns=["Date", "Topic", "Hours Studied", "Problems Solved"])

    st.markdown("### Step 2 — Real-Time Study Monitoring")
    cam_col, form_col = st.columns([1, 1])

    with cam_col:
        st.info("📌 Press 'Start' below to track your focus. Allow browser camera permissions if prompted.")
        
        try:
            webrtc_ctx = webrtc_streamer(
                key="student-companion-video",
                video_processor_factory=FaceExpressionTransformer,
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                media_stream_constraints={"video": True, "audio": False}
            )
        except Exception:
            webrtc_ctx = None
            st.error("🎥 WebRTC streaming initialization encountered an issue.")

        # Protected state mutation checks to prevent mid-thread runtime loop disruptions
        if webrtc_ctx and getattr(webrtc_ctx.state, "playing", False):
            if "session_start_time" not in st.session_state:
                st.session_state.session_start_time = datetime.datetime.now()
        else:
            if "session_start_time" in st.session_state and "session_end_time" not in st.session_state:
                st.session_state.session_end_time = datetime.datetime.now()

    with form_col:
        st.markdown("### Step 3 — Finalize & Save Progress")
        
        if "session_start_time" in st.session_state:
            end = st.session_state.get("session_end_time", datetime.datetime.now())
            calculated_hours = max((end - st.session_state.session_start_time).total_seconds() / 3600.0, 0.01)
        else:
            calculated_hours = 1.0

        total_hours = st.number_input("Adjust Monitored Hours Studied", min_value=0.01, max_value=24.0, value=float(f"{calculated_hours:.2f}"))
        problems = st.number_input("Number of Questions / Problems Solved", min_value=0, step=1, value=0, key="auto_problems")
        notes = st.text_area("Study Notes / Summary", placeholder="Write brief notes...", key="auto_notes")
        uploaded = st.file_uploader("Upload solution files (optional)", accept_multiple_files=True, key="auto_upload")

        if st.button("✅ Save Study Log to Database", key="save_auto_log"):
            date_value = datetime.date.today()
            try:
                insert_log(subject, topic, total_hours, problems, date_value)
                st.success(f"✅ Saved {total_hours:.2f}h for {topic} to database!")

                save_dir = os.path.join(os.path.dirname(__file__), "saved_solutions")
                os.makedirs(save_dir, exist_ok=True)
                for f in uploaded:
                    fname = f"{subject}_{topic}_{date_value}_{int(datetime.datetime.now().timestamp())}_{f.name}"
                    with open(os.path.join(save_dir, fname), "wb") as out:
                        out.write(f.getbuffer())

                if notes:
                    notes_fname = f"{subject}_{topic}_{date_value}_{int(datetime.datetime.now().timestamp())}_notes.txt"
                    with open(os.path.join(save_dir, notes_fname), "w", encoding="utf-8") as nf:
                        nf.write(notes)

                # Clean state records completely on drop transitions
                st.session_state.pop("session_start_time", None)
                st.session_state.pop("session_end_time", None)

                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Save failed: {e}")

    st.markdown("---")
    st.markdown("### Recent Logs")
    if not df.empty:
        st.dataframe(df.sort_values("Date", ascending=False).reset_index(drop=True), use_container_width=True)

    if st.button("⬅ Back to Log Menu"):
        st.session_state.pop("session_start_time", None)
        st.session_state.pop("session_end_time", None)
        st.session_state.page = "log_entry"
        st.rerun()

# --------------------------------
# 📈 PROGRESS PAGE
# --------------------------------
def progress_page(subject):
    st.markdown(f"## 📘 {subject} Progress Tracker")

    try:
        df = fetch_subject_df(subject)
    except Exception:
        st.error("Error reading data from database.")
        return

    if df.empty:
        st.info("No logs available yet. Go fill them out first!")
        if st.button("✏ Fill Out Logs Now"):
            st.session_state.page = "log_entry"
            st.rerun()
        return

    st.subheader("📄 Study Log")
    st.dataframe(df.sort_values("Date", ascending=False).reset_index(drop=True))

    total_hours = df["Hours Studied"].sum()
    total_problems = df["Problems Solved"].sum()
    avg_problems_per_hour = total_problems / total_hours if total_hours > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Hours", f"{total_hours:.1f}")
    col2.metric("Total Problems", f"{int(total_problems)}")
    col3.metric("Avg Problems/Hour", f"{avg_problems_per_hour:.2f}")

    st.markdown("### 🧠 Weekly Study Quality Analysis")
    df["Date"] = pd.to_datetime(df["Date"])
    current_week = datetime.date.today().isocalendar().week
    current_year = datetime.date.today().year
    df["Week"] = df["Date"].dt.isocalendar().week
    df["Year"] = df["Date"].dt.year
    week_df = df[(df["Week"] == current_week) & (df["Year"] == current_year)]

    if week_df.empty:
        st.info("No study data for this week yet. Start logging to see progress.")
    else:
        weekly_summary = week_df.groupby("Topic")["Hours Studied"].sum().reset_index()
        def get_quality(hours):
            if hours == 0:
                return "🔴 Not Started This Week"
            elif hours < 10:
                return "🟡 In Progress"
            else:
                return "🟢 Very Good"
        weekly_summary["Quality"] = weekly_summary["Hours Studied"].apply(get_quality)
        st.dataframe(
            weekly_summary.rename(columns={"Topic": "Topic", "Hours Studied": "Total Hours (This Week)"}),
        )

    st.markdown("---")
    st.markdown("### 📁 Uploaded Files & Study Notes (Sorted by Topic)")

    save_dir = os.path.join(os.path.dirname(__file__), "saved_solutions")

    if os.path.exists(save_dir):
        all_files = [f for f in os.listdir(save_dir) if subject in f]
        
        if all_files:
            files_by_topic = {}
            for file in sorted(all_files, reverse=True):
                parts = file.split("_")
                if len(parts) >= 4:
                    topic_name = "_".join(parts[1:-3])
                else:
                    topic_name = "Misc"
                files_by_topic.setdefault(topic_name, []).append(file)

            for topic_name in sorted(files_by_topic.keys()):
                with st.expander(f"📌 {topic_name} ({len(files_by_topic[topic_name])})"):
                    for fname in files_by_topic[topic_name]:
                        file_path = os.path.join(save_dir, fname)
                        try:
                            size_bytes = os.path.getsize(file_path)
                            size_kb = size_bytes / 1024.0
                        except Exception:
                            size_kb = None

                        is_notes = fname.endswith("_notes.txt")
                        
                        if is_notes:
                            st.markdown(f"**📝 Notes:** `{fname}`" + (f" — {size_kb:.1f} KB" if size_kb is not None else ""))
                        else:
                            st.markdown(f"**📄 File:** `{fname}`" + (f" — {size_kb:.1f} KB" if size_kb is not None else ""))

                        ext = os.path.splitext(fname)[1].lower()
                        
                        try:
                            if ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                                st.image(file_path, use_column_width=True)
                            elif ext in [".mp4", ".webm", ".mov", ".avi", ".mkv"]:
                                st.video(file_path)
                            elif ext in [".mp3", ".wav", ".ogg", ".flac"]:
                                st.audio(file_path)
                            elif is_notes:
                                try:
                                    with open(file_path, "r", encoding="utf-8") as nf:
                                        content = nf.read()
                                    st.text(content)
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        try:
                            with open(file_path, "rb") as bf:
                                data = bf.read()
                            st.download_button(
                                label=f"⬇️ Download {fname}",
                                data=data,
                                file_name=fname,
                                key=f"download_{fname}"
                            )
                        except Exception as e:
                            st.warning(f"Could not provide download for {fname}: {e}")

                        st.markdown("---")
        else:
            st.info(f"No files or notes found for {subject}.")
    else:
        st.info("Files directory not found. Start logging to save files and notes.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Open Dashboard View"):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("⬅ Back to Home"):
            st.session_state.page = "home"
            st.rerun()

# --------------------------------
# 📊 DASHBOARD PAGE (Topic-wise)
# --------------------------------
def dashboard_page(subject):
    st.markdown(f"## 📊 {subject} Dashboard Visualization")
    try:
        df = fetch_subject_df(subject)
    except Exception:
        st.error("Error reading data from database.")
        return

    if df.empty:
        st.info("No data found for this subject.")
        return

    df["Date"] = pd.to_datetime(df["Date"])
    topic_summary = df.groupby("Topic")[["Hours Studied", "Problems Solved"]].sum().reset_index()
    st.markdown("### 📘 Topic-wise Performance Overview")
    st.dataframe(topic_summary)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⏱ Hours Studied Over Time (per Topic)")
        line_chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("Date:T", title="Date"),
                y=alt.Y("Hours Studied:Q", title="Hours Studied"),
                color=alt.Color("Topic:N", title="Topic"),
                tooltip=["Date", "Topic", "Hours Studied"]
            )
            .properties(height=400)
            .interactive()
        )
        st.altair_chart(line_chart)

    with col2:
        st.subheader("🧩 Total Problems Solved per Topic")
        bar_chart = (
            alt.Chart(topic_summary)
            .mark_bar()
            .encode(
                x=alt.X("Topic:N", title="Topic"),
                y=alt.Y("Problems Solved:Q", title="Problems Solved"),
                color=alt.Color("Topic:N", legend=None),
                tooltip=["Topic", "Problems Solved"]
            )
            .properties(height=400)
        )
        st.altair_chart(bar_chart)

    col3, col4 = st.columns(2)
    with col3:
        if st.button("⬅ Back to Progress Page"):
            st.session_state.page = "progress"
            st.rerun()
    with col4:
        if st.button("🏠 Back to Home"):
            st.session_state.page = "home"
            st.rerun()

# --------------------------------
# 🧠 QUIZ PAGES
# --------------------------------
def quiz_subject_page():
    st.markdown("## 🧠 Choose a Subject for Your Quiz")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📘 DSA Quiz"):
            st.session_state.quiz_subject = "DSA"
            st.session_state.page = "quiz_topic"
            st.rerun()
    with col2:
        if st.button("📊 Data Science Quiz"):
            st.session_state.quiz_subject = "Data Science"
            st.session_state.page = "quiz_topic"
            st.rerun()
    if st.button("⬅ Back to Home"):
        st.session_state.page = "home"
        st.rerun()

def quiz_topic_page(subject):
    st.markdown(f"## 📚 {subject} Quiz Topics")
    if subject == "DSA":
        topics = ["Arrays", "Stacks", "Graphs", "Dynamic Programming"]
    else:
        topics = ["Python", "Statistics", "Machine Learning", "SQL"]
    for topic in topics:
        if st.button(f"📝 Start {topic} Quiz"):
            st.session_state.page = "quiz_questions"
            st.session_state.quiz_topic = topic
            st.rerun()
    if st.button("⬅ Back to Subjects"):
        st.session_state.page = "quiz_subject"
        st.rerun()

def quiz_questions_page(subject, topic):
    st.markdown(f"## 🧩 {subject} - {topic} Quiz")
    quiz_data = {
        "DSA": {
            "Arrays": [
                {"q": "What is the time complexity of accessing an element in an array?", 
                 "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "answer": "O(1)"},
                {"q": "Which data structure is used to implement an array?", 
                 "options": ["Sequential memory", "Linked list", "Stack", "Queue"], "answer": "Sequential memory"},
            ],
            "Stacks": [
                {"q": "Stacks follow which principle?", 
                 "options": ["FIFO", "LIFO", "LILO", "FILO"], "answer": "LIFO"},
                {"q": "Which operation is used to add an element to a stack?", 
                 "options": ["append()", "insert()", "push()", "enqueue()"], "answer": "push()"},
            ],
            "Graphs": [
                {"q": "A graph with all vertices connected is called?", 
                 "options": ["Complete Graph", "Tree", "Cycle", "Directed Graph"], "answer": "Complete Graph"},
            ],
            "Dynamic Programming": [
                {"q": "DP is used to solve problems with?", 
                 "options": ["Greedy property", "Overlapping subproblems", "Divide and conquer", "Independent subproblems"],
                 "answer": "Overlapping subproblems"},
            ],
        },
        "Data Science": {
            "Python": [
                {"q": "Which library is mainly used for data manipulation?", 
                 "options": ["NumPy", "Matplotlib", "Pandas", "Scikit-learn"], "answer": "Pandas"},
            ],
            "Statistics": [
                {"q": "Mean, Median, and Mode are measures of?", 
                 "options": ["Dispersion", "Central Tendency", "Probability", "Correlation"], "answer": "Central Tendency"},
            ],
            "Machine Learning": [
                {"q": "Which algorithm is used for classification?", 
                 "options": ["K-Means", "Linear Regression", "Decision Tree", "Apriori"], "answer": "Decision Tree"},
            ],
            "SQL": [
                {"q": "Which command is used to retrieve data from a database?", 
                 "options": ["GET", "SELECT", "FETCH", "SHOW"], "answer": "SELECT"},
            ],
        }
    }

    questions = quiz_data[subject][topic]
    
    with st.form(key=f"quiz_form_{subject}_{topic}"):
        user_choices = []
        for i, q in enumerate(questions, start=1):
            st.markdown(f"**Q{i}. {q['q']}**")
            choice = st.radio("Select your answer:", q["options"], key=f"radio_{subject}_{topic}_{i}")
            user_choices.append((choice, q["answer"]))
            st.markdown("---")
            
        submit_quiz = st.form_submit_button("Submit Quiz Answers")

    if submit_quiz:
        score = 0
        for idx, (user_choice, correct_answer) in enumerate(user_choices, start=1):
            if user_choice == correct_answer:
                st.success(f"Q{idx}: ✅ Correct!")
                score += 1
            else:
                st.warning(f"Q{idx}: ❌ Incorrect! Correct answer was: {correct_answer}")
        st.markdown(f"### 🎯 Final Score: {score}/{len(questions)}")

    if st.button("⬅ Back to Topics"):
        st.session_state.page = "quiz_topic"
        st.rerun()
    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"
        st.rerun()

# --------------------------------
# 🚀 PAGE CONTROLLER ROUTING
# --------------------------------
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "log_entry":
    log_entry_page()
elif st.session_state.page == "fill_logs":
    fill_logs_page(st.session_state.subject)
elif st.session_state.page == "progress":
    progress_page(st.session_state.subject)
elif st.session_state.page == "dashboard":
    dashboard_page(st.session_state.subject)
elif st.session_state.page == "quiz_subject":
    quiz_subject_page()
elif st.session_state.page == "quiz_topic":
    quiz_topic_page(st.session_state.quiz_subject)
elif st.session_state.page == "quiz_questions":
    quiz_questions_page(st.session_state.quiz_subject, st.session_state.quiz_topic)
