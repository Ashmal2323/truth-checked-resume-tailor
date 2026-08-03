"""
Gradio web app for Truth-Checked Resume Tailor. Deployed on Render
as a standard web service (not Hugging Face Spaces' native Gradio
hosting), so this file explicitly binds to Render's expected host/port.
"""

import os
import gradio as gr

from src.pipeline import run_full_pipeline

try:
    import spaces
except ImportError:
    spaces = None

def process_resume(resume_file, posting_text):
    """Gradio callback: takes an uploaded resume file + pasted job
    posting text, runs the full pipeline, and returns all four
    deliverables for display."""

    if resume_file is None:
        return "Please upload a resume file.", "", "", None

    if not posting_text or not posting_text.strip():
        return "Please paste a job posting.", "", "", None

    # Read uploaded file - support .txt directly; for .pdf we'd need
    # extra handling, so for now we require plain text uploads
    # (matches Day 1's scope-down decision: plain text/simple input only)
    with open(resume_file.name, "r", encoding="utf-8", errors="ignore") as f:
        resume_text = f.read()

    resume_id = "uploaded_resume"
    posting_id = "pasted_posting"

    try:
        result = run_full_pipeline(
            resume_text=resume_text,
            posting_text=posting_text,
            resume_id=resume_id,
            posting_id=posting_id,
        )
    except Exception as e:
        return f"Pipeline error: {e}", "", "", None

    summary = (
        f"**Fabrication Rate:** {result.fabrication_rate:.1%}\n\n"
        f"**ATS Score:** {result.ats_score}/100\n\n"
        f"**Total Gaps Found:** {result.red_flag_report.total_gaps}\n\n"
        f"**Interview Questions Generated:** {len(result.interview_prep.questions)}"
    )

    red_flags_text = "### Must-Have Gaps\n"
    for item in result.red_flag_report.must_have_gaps:
        red_flags_text += f"- **{item.requirement_text}**\n  - {item.suggestion}\n"
    red_flags_text += "\n### Nice-to-Have Gaps\n"
    for item in result.red_flag_report.nice_to_have_gaps:
        red_flags_text += f"- {item.requirement_text}\n  - {item.suggestion}\n"

    interview_text = "### Interview Prep Questions\n"
    for q in result.interview_prep.questions:
        interview_text += f"- {q.question}\n  *(based on: \"{q.bullet_text}\")*\n"

    return summary, red_flags_text, interview_text, result.pdf_path


CUSTOM_CSS = """
.gradio-container {
    max-width: 1100px !important;
    margin: auto !important;
}
#header-title {
    text-align: center;
    font-size: 2.2em !important;
    font-weight: 700 !important;
    margin-bottom: 0.2em !important;
}
#header-subtitle {
    text-align: center;
    color: #666 !important;
    margin-bottom: 1.5em !important;
}
#submit-btn {
    font-size: 1.1em !important;
    height: 48px !important;
}
.metric-box {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 16px;
    background: #fafafa;
}
"""

with gr.Blocks(title="Truth-Checked Resume Tailor") as demo:
    gr.Markdown("# 🛡️ Truth-Checked Resume Tailor", elem_id="header-title")
    gr.Markdown(
        "Upload your resume and paste a job posting. Every claim in the tailored "
        "output is independently verified against your real resume — **nothing is "
        "ever fabricated.**",
        elem_id="header-subtitle",
    )

    with gr.Row():
        with gr.Column(scale=1):
            resume_input = gr.File(
                label="📄 Upload Resume (.txt)",
                file_types=[".txt"],
            )
            posting_input = gr.Textbox(
                label="💼 Paste Job Posting",
                lines=12,
                placeholder="Paste the full job description here...",
            )
            submit_btn = gr.Button(
                "✨ Tailor My Resume", variant="primary", elem_id="submit-btn"
            )
            gr.Markdown(
                "*Processing takes 1–4 minutes — every claim is checked against your "
                "real facts before it's shown to you.*"
            )

        with gr.Column(scale=1):
            pdf_output = gr.File(label="📥 Download Tailored Resume PDF")
            summary_output = gr.Markdown(elem_classes=["metric-box"])

    with gr.Tabs():
        with gr.TabItem("🚩 Red-Flag Report"):
            redflags_output = gr.Markdown()
        with gr.TabItem("🎤 Interview Prep"):
            interview_output = gr.Markdown()

    submit_btn.click(
        fn=process_resume,
        inputs=[resume_input, posting_input],
        outputs=[summary_output, redflags_output, interview_output, pdf_output],
    )

    gr.Markdown(
        "---\n*Built with LangChain + LangSmith + Groq. "
        "[View source on GitHub](https://github.com/Ashmal2323/truth-checked-resume-tailor)*"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port, theme=gr.themes.Soft(), css=CUSTOM_CSS)