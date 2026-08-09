"""
Truth-Checked Resume Tailor — Streamlit UI
Reuses the exact same backend pipeline (src/pipeline.py) as the Gradio
version. This file is presentation-only.
"""

import streamlit as st
from src.pipeline import run_full_pipeline

st.set_page_config(
    page_title="Truth-Checked Resume Tailor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# GLOBAL STYLES
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="css"], .stMarkdown, p, div { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

#MainMenu, footer, header {visibility: hidden;}

.block-container {
    padding-top: 2rem !important;
    max-width: 1180px !important;
}

/* ---------- HERO ---------- */
.hero {
    position: relative;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #1e3a8a 100%);
    padding: 56px 40px 48px 40px;
    border-radius: 24px;
    text-align: center;
    color: white;
    margin-bottom: 32px;
    overflow: hidden;
    box-shadow: 0 20px 50px -12px rgba(15, 23, 42, 0.45);
}
.hero::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(96,165,250,0.35) 0%, transparent 70%);
    border-radius: 50%;
}
.hero::after {
    content: "";
    position: absolute;
    bottom: -80px; left: -40px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(52,211,153,0.25) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-eyebrow {
    display: inline-block;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.18);
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 0.78em;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #93c5fd;
    margin-bottom: 18px;
    position: relative;
}
.hero h1 {
    font-size: 2.7em;
    font-weight: 800;
    margin: 0 0 14px 0;
    letter-spacing: -0.02em;
    position: relative;
    color: #ffffff;
}
.hero p {
    color: #cbd5e1;
    font-size: 1.08em;
    max-width: 640px;
    margin: 0 auto 24px auto;
    line-height: 1.6;
    position: relative;
}
.badge-row { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; position: relative; }
.badge {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.18);
    backdrop-filter: blur(8px);
    padding: 8px 16px;
    border-radius: 999px;
    font-size: 0.85em;
    font-weight: 600;
    color: #e2e8f0;
    transition: all 0.2s ease;
}
.badge:hover { background: rgba(255,255,255,0.14); transform: translateY(-1px); }

/* ---------- SECTION CARDS ---------- */
.section-card {
    background: white;
    border-radius: 18px;
    padding: 26px 28px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03), 0 4px 12px -4px rgba(0,0,0,0.04);
    height: 100%;
}
.section-title {
    display: flex; align-items: center; gap: 10px;
    font-size: 1.15em; font-weight: 700; color: #0f172a;
    margin-bottom: 4px;
}
.section-subtitle {
    color: #64748b; font-size: 0.88em; margin-bottom: 18px;
}
.step-number {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white; font-weight: 700; font-size: 0.8em;
    border-radius: 8px;
}

/* ---------- BUTTON ---------- */
div.stButton > button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 1.05em !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 0 !important;
    box-shadow: 0 6px 20px -4px rgba(37, 99, 235, 0.5) !important;
    transition: all 0.2s ease !important;
    width: 100%;
}
div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px -4px rgba(37, 99, 235, 0.6) !important;
}

/* ---------- METRICS ---------- */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 8px 0 24px 0;
}
.metric-tile {
    background: white;
    border-radius: 16px;
    padding: 20px 16px;
    text-align: center;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.metric-tile .value {
    font-size: 1.9em; font-weight: 800; letter-spacing: -0.02em;
}
.metric-tile .label {
    font-size: 0.78em; color: #64748b; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.03em; margin-top: 4px;
}
.metric-green .value { color: #059669; }
.metric-blue .value { color: #2563eb; }
.metric-amber .value { color: #d97706; }
.metric-purple .value { color: #7c3aed; }

/* ---------- GAP / QUESTION ITEMS ---------- */
.gap-item {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.gap-item.nice {
    background: #fffbeb;
    border-left-color: #f59e0b;
}
.gap-item b { color: #0f172a; }
.gap-item .suggestion { color: #64748b; font-size: 0.9em; margin-top: 4px; }

.question-item {
    background: #f0f9ff;
    border-left: 4px solid #0ea5e9;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.question-item .q { color: #0f172a; font-weight: 600; }
.question-item .based-on { color: #64748b; font-size: 0.85em; margin-top: 4px; font-style: italic; }

/* ---------- FOOTER ---------- */
.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 0.88em;
    padding: 28px 0 10px 0;
    border-top: 1px solid #e2e8f0;
    margin-top: 40px;
}
.footer a { color: #2563eb; text-decoration: none; font-weight: 600; }

/* ---------- FILE UPLOADER / TEXTAREA ---------- */
[data-testid="stFileUploaderDropzone"] {
    border-radius: 12px !important;
    border: 2px dashed #cbd5e1 !important;
}
.stTextArea textarea {
    border-radius: 12px !important;
    border: 1.5px solid #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HERO
# ============================================================
st.markdown("""
<div class="hero">
    <span class="hero-eyebrow">🛡️ Zero-Fabrication AI Resume Engine</span>
    <h1>Truth-Checked Resume Tailor</h1>
    <p>Upload your resume and paste a job posting. Every single claim in the tailored output
    is independently verified against your real resume before you ever see it — nothing is invented, ever.</p>
    <div class="badge-row">
        <span class="badge">✅ 0% Fabrication Rate</span>
        <span class="badge">🔍 Independently Verified</span>
        <span class="badge">⚡ Groq + LangChain + LangSmith</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# INPUT SECTION
# ============================================================
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("""
    <div class="section-card">
        <div class="section-title"><span class="step-number">1</span> Your Resume</div>
        <div class="section-subtitle">Upload a plain text (.txt) version of your resume</div>
    """, unsafe_allow_html=True)
    resume_file = st.file_uploader("Upload Resume", type=["txt"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="section-card">
        <div class="section-title"><span class="step-number">2</span> Target Job Posting</div>
        <div class="section-subtitle">Paste the full job description you're applying to</div>
    """, unsafe_allow_html=True)
    posting_text = st.text_area("Job posting", height=160, label_visibility="collapsed",
                                 placeholder="Paste the full job description here...")
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")
submit = st.button("✨  Tailor My Resume — Verified & Honest", type="primary")
st.markdown(
    "<center><span style='color:#94a3b8; font-size:0.85em;'>⏱️ Processing takes 1–4 minutes — "
    "every claim is checked against your real facts before it's shown to you.</span></center>",
    unsafe_allow_html=True
)

# ============================================================
# PIPELINE EXECUTION
# ============================================================
if submit:
    if resume_file is None:
        st.error("📄 Please upload a resume file.")
    elif not posting_text.strip():
        st.error("💼 Please paste a job posting.")
    else:
        resume_text = resume_file.read().decode("utf-8", errors="ignore")

        with st.spinner("🔎 Extracting facts → matching requirements → generating → verifying every claim..."):
            try:
                result = run_full_pipeline(
                    resume_text=resume_text,
                    posting_text=posting_text,
                    resume_id="uploaded_resume",
                    posting_id="pasted_posting",
                )
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.stop()

        st.balloons()
        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------- Metric tiles ----------------
        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-tile metric-green">
                <div class="value">{result.fabrication_rate:.0%}</div>
                <div class="label">Fabrication Rate</div>
            </div>
            <div class="metric-tile metric-blue">
                <div class="value">{result.ats_score}</div>
                <div class="label">ATS Score / 100</div>
            </div>
            <div class="metric-tile metric-amber">
                <div class="value">{result.red_flag_report.total_gaps}</div>
                <div class="label">Gaps Found</div>
            </div>
            <div class="metric-tile metric-purple">
                <div class="value">{len(result.interview_prep.questions)}</div>
                <div class="label">Interview Qs</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with open(result.pdf_path, "rb") as f:
            st.download_button(
                "📥  Download Your Tailored Resume (PDF)",
                data=f.read(),
                file_name="tailored_resume.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        st.write("")
        tab1, tab2 = st.tabs(["🚩  Red-Flag Report", "🎤  Interview Prep"])

        with tab1:
            if result.red_flag_report.must_have_gaps:
                st.markdown("#### 🔴 Must-Have Gaps")
                for item in result.red_flag_report.must_have_gaps:
                    st.markdown(f"""
                    <div class="gap-item">
                        <b>{item.requirement_text}</b>
                        <div class="suggestion">{item.suggestion}</div>
                    </div>
                    """, unsafe_allow_html=True)
            if result.red_flag_report.nice_to_have_gaps:
                st.markdown("#### 🟡 Nice-to-Have Gaps")
                for item in result.red_flag_report.nice_to_have_gaps:
                    st.markdown(f"""
                    <div class="gap-item nice">
                        <b>{item.requirement_text}</b>
                        <div class="suggestion">{item.suggestion}</div>
                    </div>
                    """, unsafe_allow_html=True)
            if not result.red_flag_report.must_have_gaps and not result.red_flag_report.nice_to_have_gaps:
                st.success("No significant gaps found — strong match!")

        with tab2:
            if result.interview_prep.questions:
                for q in result.interview_prep.questions:
                    st.markdown(f"""
                    <div class="question-item">
                        <div class="q">{q.question}</div>
                        <div class="based-on">Based on: "{q.bullet_text}"</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No verified claims were strong enough to generate interview questions for this match.")

st.markdown("""
<div class="footer">
    Built with <b>LangChain</b> · <b>LangSmith</b> · <b>Groq</b><br>
    <a href="https://github.com/Ashmal2323/truth-checked-resume-tailor" target="_blank">View source on GitHub →</a>
</div>
""", unsafe_allow_html=True)