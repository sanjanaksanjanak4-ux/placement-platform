from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
JOBS_FILE = DATA_DIR / "sample_jobs.csv"

st.set_page_config(
    page_title="Campus Career Match",
    page_icon="🎓",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #080d18 0%, #101827 55%, #11152b 100%);
    color: #edf2ff;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background-color: #0b1220; }
.block-container { max-width: 1100px; padding-top: 2rem; }
h1, h2, h3, p, label { color: #edf2ff !important; }
.hero {
    padding: 28px;
    border: 1px solid #293754;
    border-radius: 20px;
    background: linear-gradient(120deg, #17243b, #17172f);
    margin-bottom: 22px;
}
.hero h1 { margin: 0 0 8px 0; font-size: 2.2rem; }
.hero p { color: #b8c5df !important; margin: 0; }
.panel {
    padding: 22px;
    border: 1px solid #293754;
    border-radius: 18px;
    background: #111a2a;
    margin: 12px 0;
}
.job-card {
    padding: 20px;
    border: 1px solid #2b3a58;
    border-radius: 16px;
    background: linear-gradient(135deg, #121e31, #15172b);
    margin: 12px 0;
}
.job-title { font-size: 1.2rem; font-weight: 700; color: #f3f6ff; }
.job-meta { color: #a8b7d2; margin: 5px 0 12px; }
.badge {
    display: inline-block;
    background: #203652;
    color: #9fd7ff;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: .85rem;
}
.small-note { color: #a8b7d2; font-size: .9rem; }
.stButton > button {
    border: 0;
    border-radius: 10px;
    background: linear-gradient(90deg, #7257ff, #398bff);
    color: white;
    font-weight: 700;
    min-height: 44px;
}
.stButton > button:hover { border: 1px solid #a9c6ff; color: white; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🎓 Campus Career Match</h1>
  <p>Enter your skills and CGPA to explore matching jobs and internships.</p>
</div>
""", unsafe_allow_html=True)

if not JOBS_FILE.exists():
    st.error("I couldn't find data/sample_jobs.csv. Check that the jobs CSV is inside your project's data folder.")
    st.stop()

jobs = pd.read_csv(JOBS_FILE)

required_columns = {"role", "company", "required_skills", "location"}
if not required_columns.issubset(jobs.columns):
    st.error("The jobs CSV must include: role, company, required_skills, and location.")
    st.stop()


def parse_skills(value):
    if pd.isna(value):
        return set()
    return {
        item.strip().lower()
        for item in str(value).replace(",", ";").split(";")
        if item.strip()
    }


def safe_text(value):
    return escape(str(value)) if pd.notna(value) else ""


with st.form("career_form"):
    st.subheader("Your profile")
    col1, col2 = st.columns([2, 1])

    with col1:
        skills_input = st.text_input(
            "Your skills",
            placeholder="Example: Python, SQL, communication",
            help="Separate skills with commas.",
        )

    with col2:
        cgpa = st.number_input(
            "CGPA (out of 10)",
            min_value=0.0,
            max_value=10.0,
            value=7.0,
            step=0.1,
        )

    preference = st.selectbox(
        "What are you looking for?",
        ["All opportunities", "Jobs", "Internships"],
    )

    submitted = st.form_submit_button("Find my matches", use_container_width=True)

if submitted:
    student_skills = parse_skills(skills_input)

    if not student_skills:
        st.warning("Enter at least one skill so I can compare your profile with the listings.")
        st.stop()

    ranked_jobs = []

    for _, job in jobs.iterrows():
        role = str(job["role"])
        role_lower = role.lower()
        is_internship = "intern" in role_lower

        if preference == "Jobs" and is_internship:
            continue
        if preference == "Internships" and not is_internship:
            continue

        required_skills = parse_skills(job["required_skills"])
        matched = student_skills & required_skills
        missing = required_skills - student_skills

        skill_score = (
            len(matched) / len(required_skills) * 100
            if required_skills else 0
        )
        cgpa_score = cgpa / 10 * 100

        # Ranking heuristic: skills count for 80%, CGPA for 20%.
        match_score = round((skill_score * 0.8) + (cgpa_score * 0.2))

        ranked_jobs.append({
            "role": role,
            "company": job["company"],
            "location": job["location"],
            "score": match_score,
            "matched": sorted(matched),
            "missing": sorted(missing),
            "description": job.get("description", ""),
        })

    ranked_jobs.sort(key=lambda item: item["score"], reverse=True)

    st.markdown('<div class="panel"><h2>Your recommended opportunities</h2></div>',
                unsafe_allow_html=True)

    if not ranked_jobs:
        st.info("No listings match that category yet. Try “All opportunities” or add more listings to sample_jobs.csv.")
    else:
        st.caption(
            "The match percentage is a simple project demo based on listed skills (80%) "
            "and CGPA (20%). It is not an employer's official eligibility or interview decision."
        )

        for item in ranked_jobs:
            matched_text = ", ".join(item["matched"]) if item["matched"] else "No listed skills matched yet"
            missing_text = ", ".join(item["missing"]) if item["missing"] else "No missing listed skills"

            st.markdown(f"""
            <div class="job-card">
              <div class="job-title">{safe_text(item["role"])} · {safe_text(item["company"])}</div>
              <div class="job-meta">📍 {safe_text(item["location"])}
                &nbsp;&nbsp; <span class="badge">{item["score"]}% profile match</span>
              </div>
              <p><b>Matching skills:</b> {escape(matched_text)}</p>
              <p><b>Skills to build:</b> {escape(missing_text)}</p>
              <p class="small-note">{safe_text(item["description"])}</p>
            </div>
            """, unsafe_allow_html=True)