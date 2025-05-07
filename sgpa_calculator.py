import streamlit as st
import json
import os
from io import BytesIO

st.set_page_config(page_title="SGPA Grade Target Calculator", layout="centered")

# Theme Styling
st.markdown("""
    <style>
        body {
            background: linear-gradient(135deg, #f0f4f8, #d9e2ec);
            color: #1f2937;
        }
        [data-theme="dark"] body {
            background: linear-gradient(135deg, #1e293b, #0f172a);
            color: #f8fafc;
        }
        button[kind="primary"], .stButton > button {
            background: linear-gradient(to right, #667eea, #764ba2);
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }
        [data-theme="dark"] .stButton > button {
            background: linear-gradient(to right, #06b6d4, #3b82f6);
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Grade scale
grade_data = {
    "O (10)": {"min_total": 91, "points": 10},
    "A+ (9)": {"min_total": 81, "points": 9},
    "A (8)": {"min_total": 71, "points": 8},
    "B+ (7)": {"min_total": 61, "points": 7},
    "B (6)": {"min_total": 51, "points": 6},
    "RA (0)": {"min_total": 0, "points": 0},
}
grade_options = list(grade_data.keys())

SESSIONS_FILE = "sgpa_sessions.json"

# Load saved sessions from file if exists
if os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, "r") as f:
        st.session_state.past_sessions = json.load(f)
else:
    st.session_state.past_sessions = []

def save_sessions():
    with open(SESSIONS_FILE, "w") as f:
        json.dump(st.session_state.past_sessions, f, indent=4)

if "current_subjects" not in st.session_state:
    st.session_state.current_subjects = []

if "current_session_name" not in st.session_state:
    st.session_state.current_session_name = ""

# Sidebar: Past Sessions
with st.sidebar:
    st.markdown("## 📚 Past SGPA Sessions")

    
    if st.session_state.past_sessions:
        st.markdown("### 📂 Load Previous Session")
        for idx, session in enumerate(st.session_state.past_sessions):
            col1, col2, col3 = st.columns([4, 1, 1])

            if col1.button(f"📄 {session['name']}", key=f"load_{idx}"):
                st.session_state.current_session_name = session['name']
                st.session_state.current_subjects = session['subjects'].copy()
                st.success(f"Loaded session: {session['name']}")
                st.rerun()

            if col2.button("✏️", key=f"rename_{idx}"):
                new_name = st.text_input(f"Rename '{session['name']}' to:", key=f"rename_input_{idx}")
                if new_name.strip():
                    st.session_state.past_sessions[idx]['name'] = new_name.strip()
                    save_sessions()
                    st.success(f"Renamed to: {new_name.strip()}")
                    st.rerun()

            if col3.button("❌", key=f"delete_{idx}"):
                st.session_state.past_sessions.pop(idx)
                save_sessions()
                st.success(f"Deleted session: {session['name']}")
                st.rerun()
    else:
        st.caption("No previous sessions yet.")

    if st.button("➕ Start New Session"):
        st.session_state.current_session_name = ""
        st.session_state.current_subjects = []

# Main Title
st.title("📈 GradeX - SGPA Target Calculator")

# Step 1: Get session name
if not st.session_state.current_session_name:
    st.subheader("🔖 Enter a name for your SGPA session")
    session_name_input = st.text_input("Session Name")
    if st.button("✅ Start Session") and session_name_input.strip():
        st.session_state.current_session_name = session_name_input.strip()
        st.success(f"Started session: {session_name_input.strip()}")

# Step 2: Add subjects
if st.session_state.current_session_name:
    st.markdown(f"### 📘 Session: **{st.session_state.current_session_name}**")
    with st.form("subject_form"):
        col1, col2, col3 = st.columns([2, 1, 1])
        subject = col1.text_input("Subject Name")
        internal_marks = col2.number_input("Internal Marks (out of 60)", min_value=0.0, max_value=60.0, step=0.01)
        credits = col3.number_input("Credits", min_value=1, max_value=5, step=1)
        grade = st.select_slider("Desired Grade", options=grade_options)
        submit = st.form_submit_button("➕ Add Subject")

        if submit and subject:
            st.session_state.current_subjects.append({
                "Subject": subject,
                "Internal": internal_marks,
                "Grade": grade,
                "Credits": credits
            })
            st.success(f"Added subject '{subject}'")

# Display and calculate SGPA
if st.session_state.current_subjects:
    st.markdown("### 📊 Subject Details and Required End-Sem Marks")
    total_points = 0
    total_credits = 0
    updated_subjects = []
    invalid_subjects = []

    for i, sub in enumerate(st.session_state.current_subjects):
        with st.expander(f"📚 {sub['Subject']}"):
            col1, col2, col3 = st.columns(3)
            new_internal = col1.number_input(
                f"Update Internal", value=sub["Internal"], min_value=0.0, max_value=60.0, step=0.01, key=f"int_{i}"
            )
            new_grade = col2.select_slider(
                "Update Grade", options=grade_options, value=sub["Grade"], key=f"grade_{i}"
            )
            new_credits = col3.number_input(
                "Credits", value=sub["Credits"], min_value=1, max_value=5, step=1, key=f"credits_{i}"
            )

            min_total = grade_data[new_grade]["min_total"]
            req_40 = min_total - new_internal
            req_75 = round((req_40 / 40) * 75, 2)
            color = "red" if req_75 > 75 else "green"

            if req_75 > 75:
                invalid_subjects.append(sub["Subject"])

            st.markdown(
                f"<span style='font-size:17px;'>"
                f"You got <strong>{new_internal:.2f}/60</strong> in <strong>{sub['Subject']}</strong>.<br>"
                f"You need <strong><span style='color:{color};'>{req_75:.2f}/75</span></strong> in end-sem to get <strong>{new_grade}</strong>."
                f"</span>",
                unsafe_allow_html=True
            )

            updated_subjects.append({
                "Subject": sub["Subject"],
                "Internal": new_internal,
                "Grade": new_grade,
                "Credits": new_credits
            })

            total_points += grade_data[new_grade]["points"] * new_credits
            total_credits += new_credits

    if invalid_subjects:
        for name in invalid_subjects:
            st.error(f"Error in desired grade of {name}")
    else:
        sgpa = total_points / total_credits if total_credits else 0
        st.success(f"🌟 Estimated SGPA: {sgpa:.2f}")

        if st.button("📅 Save This Session"):
            st.session_state.past_sessions.append({
                "name": st.session_state.current_session_name,
                "subjects": updated_subjects,
                "sgpa": sgpa
            })
            save_sessions()
            st.success("Session saved!")
            st.session_state.current_session_name = ""
            st.session_state.current_subjects = []
            st.rerun()

