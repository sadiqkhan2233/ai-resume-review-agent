"""AI Resume Review Agent - Streamlit front end."""
import json
import os

import streamlit as st

from resume_agent.agent import ReviewError, review_resume
from resume_agent.config import (
    APP_NAME,
    DEFAULT_MODEL,
    DISCLAIMER,
    MAX_FILE_SIZE_MB,
    MAX_JD_CHARS,
)
from resume_agent.extractors import ExtractionError, extract_resume_text
from resume_agent.report import build_pdf_report
from resume_agent.scoring import build_score_rows, grade_label, job_match, overall_score

st.set_page_config(page_title=APP_NAME, page_icon="📄", layout="wide")

STATUS_ICON = {"strong": "🟢", "adequate": "🟡", "weak": "🟠", "missing": "🔴"}


def get_default_api_key() -> str:
    """Streamlit secrets (cloud) first, then environment / .env (local)."""
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "")


def show_list(title: str, items: list, icon: str = "•") -> None:
    if items:
        st.markdown(f"**{title}**")
        for item in items:
            st.markdown(f"{icon} {item}")


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    default_key = get_default_api_key()
    api_key = st.text_input(
        "Groq API key",
        value="",
        type="password",
        placeholder="Using the configured key" if default_key else "gsk_...",
        help="Get a free key at console.groq.com/keys. Your key is only used for this session.",
    ) or default_key
    model = st.text_input("Groq model", value=DEFAULT_MODEL, help="Change this if the model is unavailable or rate-limited.")
    st.divider()
    st.markdown(
        "**Privacy**\n\nResumes are processed in memory only and are never saved to disk. "
        "Text is sent to Groq's API for analysis."
    )
    st.caption("Built with CrewAI • Groq • Streamlit")

# -------------------------------------------------------------------- main
st.title("📄 AI Resume Review Agent")
st.write("Upload your resume to get recruiter-style feedback, an ATS-style score, a job match analysis and an improvement plan.")
st.warning(DISCLAIMER)

col_left, col_right = st.columns(2)
with col_left:
    uploaded = st.file_uploader(f"Upload resume (PDF or DOCX, max {MAX_FILE_SIZE_MB} MB)", type=["pdf", "docx"])
    job_title = st.text_input("Target job title (optional)", placeholder="e.g. Junior Data Analyst")
with col_right:
    job_description = st.text_area(
        "Job description (optional)",
        height=200,
        placeholder="Paste the job description here for job-match scoring...",
        help=f"Only the first {MAX_JD_CHARS} characters are used.",
    )

resume_text = ""
if uploaded is not None:
    try:
        resume_text = extract_resume_text(uploaded.name, uploaded.getvalue())
        st.success(f"Read {len(resume_text):,} characters from **{uploaded.name}**.")
    except ExtractionError as err:
        st.error(str(err))

if resume_text and st.checkbox("Show extracted text preview"):
    st.text_area("Extracted text", resume_text, height=250, disabled=True)

analyze = st.button("🔍 Analyze Resume", type="primary", disabled=not resume_text)

if analyze:
    with st.spinner("The Professional Resume Reviewer is analysing your resume... (10-60 seconds)"):
        try:
            review = review_resume(resume_text, job_title, job_description, api_key, model)
            rows = build_score_rows(review)
            total = overall_score(rows)
            match = job_match(review)
            pdf_bytes = build_pdf_report(review, rows, total, grade_label(total), match, job_title)
            st.session_state["result"] = {
                "review": review,
                "rows": rows,
                "total": total,
                "match": match,
                "pdf": pdf_bytes,
            }
        except ReviewError as err:
            st.session_state.pop("result", None)
            st.error(str(err))
        except Exception as err:  # last-resort safety net
            st.session_state.pop("result", None)
            st.error(f"Unexpected error: {err}")

# ----------------------------------------------------------------- results
result = st.session_state.get("result")
if result and resume_text:
    review, rows, total, match = result["review"], result["rows"], result["total"], result["match"]

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Overall ATS-style score", f"{total:g} / 100")
    m2.metric("Rating", grade_label(total))
    m3.metric("Job match", f"{match['percent']}%" if match else "N/A")
    st.progress(min(total / 100, 1.0))

    tab_scores, tab_sections, tab_match, tab_recs, tab_rewrites, tab_download = st.tabs(
        ["📊 Scores", "🧩 Sections", "🎯 Job match", "💡 Recommendations", "✍️ Rewrites", "⬇️ Download"]
    )

    with tab_scores:
        for r in rows:
            st.markdown(f"**{r['label']}** — {r['score']:g} / {r['max']}")
            st.progress(r["score"] / r["max"])
            st.caption(r["explanation"])
        c1, c2 = st.columns(2)
        with c1:
            show_list("✅ Strengths", review.strengths)
        with c2:
            show_list("⚠️ Weaknesses", review.weaknesses)
        show_list("❓ Missing information", review.missing_information)

    with tab_sections:
        for s in review.section_analysis:
            icon = STATUS_ICON.get(s.status.strip().lower(), "⚪")
            with st.expander(f"{icon} {s.section} — {s.status}"):
                st.write(s.feedback)

    with tab_match:
        if match:
            st.metric("Job match score", f"{match['percent']}%")
            st.caption("How it is calculated: " + match["formula"])
            a, b = st.columns(2)
            with a:
                show_list("✅ Matching skills", match["matched"])
            with b:
                show_list("❌ Missing skills", match["missing"])
        else:
            st.info("Paste a job description and run the analysis again to see a job match score.")
        show_list("🎯 Job-specific recommendations", review.job_specific_recommendations)

    with tab_recs:
        show_list("🧠 Suggested skills", review.suggested_skills)
        show_list("🎓 Recommended certifications", review.recommended_certifications)
        show_list("📚 Education suggestions", review.education_suggestions)
        show_list("💼 Experience suggestions", review.experience_suggestions)
        show_list("🗺️ Action plan", review.action_plan, "👉")
        if review.improved_summary:
            st.markdown("**📝 Improved professional summary**")
            st.info(review.improved_summary)
            st.caption("Review this carefully and replace any [placeholders] with real facts.")

    with tab_rewrites:
        if review.rewritten_bullets:
            for b in review.rewritten_bullets:
                x, y = st.columns(2)
                x.markdown("**Original**")
                x.write(b.original)
                y.markdown("**Improved**")
                y.write(b.improved)
                if b.note:
                    st.caption(b.note)
                st.divider()
            st.caption("Replace any [placeholders] with your real numbers and tools. Never add facts that are not true.")
        else:
            st.info("No bullet rewrites were generated.")

    with tab_download:
        st.download_button("📄 Download PDF report", result["pdf"], "resume_review_report.pdf", "application/pdf")
        st.download_button(
            "🧾 Download raw JSON",
            json.dumps(review.model_dump(), indent=2),
            "resume_review.json",
            "application/json",
        )
