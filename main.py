import streamlit as st
import pandas as pd
import datetime
import os
import altair as alt
import cv2
import numpy as np

# --------------------------------
# 🗄️ STREAMLIT NATIVE SQL CONNECTION (PostgreSQL)
# --------------------------------
# Initialize the native SQL connection using your saved secrets
conn = st.connection("sql")

def ensure_table():
    """
    Creates the study_logs table automatically if it doesn't exist.
    Note: PostgreSQL uses SERIAL instead of AUTO_INCREMENT.
    """
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
    with conn.session as session:
        session.execute(sql)
        session.commit()

def insert_log(subject, topic, hours, problems, date_value):
    """
    Inserts a new study log using safe PostgreSQL named-parameter bindings.
    """
    sql = """
    INSERT INTO study_logs (subject, topic, hours_studied, problems_solved, date)
    VALUES (:subject, :topic, :hours, :problems, :date_value);
    """
    with conn.session as session:
        session.execute(
            sql, 
            {
                "subject": subject, 
                "topic": topic, 
                "hours": float(hours), 
                "problems": int(problems), 
                "date_value": date_value
            }
        )
        session.commit()

def fetch_subject_df(subject):
    """
    Fetches study records for a given subject. 
    Streamlit's conn.query automatically returns a formatted Pandas DataFrame.
    """
    sql = """
    SELECT subject AS "Subject", topic AS "Topic", 
           hours_studied AS "Hours Studied", problems_solved AS "Problems Solved", date AS "Date" 
    FROM study_logs WHERE subject = :subject;
    """
    # ttl="0x" disables caching so user dashboard updates display instantly
    return conn.query(sql, params={"subject": subject}, ttl="0x")

# Ensure table exists on startup
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
        transition: transform 0.3s ease 0.3s, box-shadow 0.3s ease;
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
# 📋 FILL LOGS PAGE
# --------------------------------
def fill_logs_page(subject):
    st.markdown(f"## ✏ Add {subject} Learning Logs")
    st.markdown("**📷 Real-time Camera Monitoring: Detect person sitting & auto-detect study hours.**")

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

    st.markdown("### 📷 Real-Time Study Monitoring (Detect Person Sitting)")
    st.info("📌 Click 'Start Monitoring' to begin. Session will auto-stop when you leave camera or after long inactivity. Hours are auto-detected and saved.")

    col_cam1, col_cam2 = st.columns([2, 1])
    with col_cam1:
        camera_placeholder = st.empty()
    with col_cam2:
        focus_metric = st.empty()
        duration_metric = st.empty()
        attention_metric = st.empty()

    # Initialize session state
    if "monitoring_active" not in st.session_state:
        st.session_state.monitoring_active = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "cap" not in st.session_state:
        st.session_state.cap = None
    if "study_frames" not in st.session_state:
        st.session_state.study_frames = 0
    if "total_frames" not in st.session_state:
        st.session_state.total_frames = 0
    if "no_person_frames" not in st.session_state:
        st.session_state.no_person_frames = 0
    if "prev_gray" not in st.session_state:
        st.session_state.prev_gray = None

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶ Start Monitoring", key="start_monitor"):
            st.session_state.monitoring_active = True
            st.session_state.start_time = datetime.datetime.now()
            cap = None
            for camera_idx in [0, 1, -1]:
                cap = cv2.VideoCapture(camera_idx)
                if cap.isOpened():
                    st.session_state.cap = cap
                    break
                else:
                    cap.release()
            
            if not st.session_state.cap or not st.session_state.cap.isOpened():
                st.error("❌ No camera found. Please check camera connection.")
                st.session_state.monitoring_active = False
                st.rerun()
                return
            st.rerun()

    with col_btn2:
        if st.button("⏹️ Stop Monitoring Now", key="stop_monitor"):
            st.session_state.monitoring_active = False
            if st.session_state.cap:
                st.session_state.cap.release()
                st.session_state.cap = None

    # Run monitoring if active
    if st.session_state.monitoring_active and st.session_state.cap:
        cap = st.session_state.cap

        if not cap.isOpened():
            st.error("❌ Camera disconnected.")
            st.session_state.monitoring_active = False
            st.rerun()
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        cap.set(cv2.CAP_PROP_FPS, 15)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        frames_per_update = 3
        frame_count = 0

        while frame_count < frames_per_update and st.session_state.monitoring_active:
            ret, frame = cap.read()
            if not ret:
                st.warning("⚠️ Camera frame not available. Retrying...")
                continue

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(40, 40))
            face_detected = len(faces) > 0

            if st.session_state.prev_gray is None:
                st.session_state.prev_gray = gray.copy()
                frame_color = (100, 100, 100)
                status = "⏸ Initializing..."
            else:
                frame_diff = cv2.absdiff(st.session_state.prev_gray, gray)
                motion_level = frame_diff.mean()
                st.session_state.prev_gray = gray.copy()

                if face_detected:
                    st.session_state.study_frames += 1
                    st.session_state.no_person_frames = 0
                    frame_color = (0, 255, 0)
                    status = "✅ Person Detected — Studying"
                else:
                    st.session_state.no_person_frames += 1
                    if st.session_state.no_person_frames > 100:
                        frame_color = (0, 0, 255)
                    else:
                        frame_color = (100, 100, 100)
                    status = "⏸ Waiting for Person"

            st.session_state.total_frames += 1
            frame_count += 1

            for (x, y, w_face, h_face) in faces:
                cv2.rectangle(frame, (x, y), (x + w_face, y + h_face), frame_color, 2)
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (0, 0), (w, h), frame_color, 3)
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, frame_color, 2)

            elapsed = datetime.datetime.now() - st.session_state.start_time
            elapsed_seconds = elapsed.total_seconds()
            elapsed_hours = int(elapsed_seconds // 3600)
            elapsed_minutes = int((elapsed_seconds % 3600) // 60)
            elapsed_secs = int(elapsed_seconds % 60)

            camera_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            efficiency = (st.session_state.study_frames / st.session_state.total_frames * 100) if st.session_state.total_frames > 0 else 0
            focus_metric.metric("Focus Rate", f"{efficiency:.1f}%")
            duration_metric.metric("Session Time", f"{elapsed_hours}h {elapsed_minutes}m {elapsed_secs}s")
            attention_metric.metric("Attention Level", "🟢 Good" if efficiency > 70 else "🟡 Fair" if efficiency > 40 else "🔴 Low")

            if st.session_state.no_person_frames > 150:
                st.session_state.monitoring_active = False
                if st.session_state.cap:
                    st.session_state.cap.release()
                    st.session_state.cap = None
                st.info("Session auto-stopped: No person detected for extended period.")
                break

        st.rerun()

    # Show finalize form after monitoring stopped
    if not st.session_state.monitoring_active and st.session_state.total_frames > 0:
        if st.session_state.cap:
            st.session_state.cap.release()
            st.session_state.cap = None

        st.markdown("---")
        st.markdown("### Step 2 — Finalize & Save Study Log")
        
        total_elapsed = datetime.datetime.now() - st.session_state.start_time
        total_hours = total_elapsed.total_seconds() / 3600.0
        
        st.markdown(f"- **Auto-detected hours:** {total_hours:.3f}h")
        st.markdown(f"- **Detected focus:** {(st.session_state.study_frames / st.session_state.total_frames * 100):.1f}%")

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

                for k in ("monitoring_active", "start_time", "cap", "study_frames", "total_frames", "no_person_frames", "prev_gray"):
                    if k in st.session_state:
                        del st.session_state[k]

                st.balloons()
                st.rerun()

            except Exception as e:
                st.error(f"❌ Save failed: {e}")

    # Show recent logs
    if not st.session_state.monitoring_active and st.session_state.total_frames == 0:
        st.markdown("---")
        st.markdown("### Recent Logs")
        if not df.empty:
            st.dataframe(df.sort_values("Date", ascending=False).reset_index(drop=True), use_container_width=True)

    # Navigation
    if st.button("⬅ Back to Log Menu"):
        st.session_state.page = "log_entry"
        if st.session_state.cap:
            st.session_state.cap.release()
            st.session_state.cap = None
        for k in ("monitoring_active", "start_time", "cap", "study_frames", "total_frames", "no_person_frames", "prev_gray"):
            if k in st.session_state:
                del st.session_state[k]
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
    score = 0
    for i, q in enumerate(questions, start=1):
        st.markdown(f"Q{i}. {q['q']}")
        choice = st.radio("Select your answer:", q["options"], key=f"{subject}{topic}{i}")
        if choice == q["answer"]:
            st.success("✅ Correct!")
            score += 1
        else:
            st.warning(f"❌ Wrong! Correct answer: {q['answer']}")
        st.markdown("---")
    st.markdown(f"### 🎯 Your Score: {score}/{len(questions)}")
    if st.button("⬅ Back to Topics"):
        st.session_state.page = "quiz_topic"
        st.rerun()
    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"
        st.rerun()

# --------------------------------
# 🚀 PAGE CONTROLLER
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
