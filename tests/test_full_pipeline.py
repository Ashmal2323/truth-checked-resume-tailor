"""The real end-to-end test: one function call, all four deliverables."""

from src.pipeline import run_full_pipeline

def test_pipeline():
    with open("src/data/resumes/resume_1.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    with open("src/data/job_postings/posting_1.txt", "r", encoding="utf-8") as f:
        posting_text = f.read()

    result = run_full_pipeline(
        resume_text=resume_text,
        posting_text=posting_text,
        resume_id="resume_1",
        posting_id="posting_1",
    )

    print(f"PDF generated at: {result.pdf_path}")
    print(f"Fabrication rate: {result.fabrication_rate:.1%}")
    print(f"ATS score: {result.ats_score}/100")
    print(f"Red-flag gaps: {result.red_flag_report.total_gaps}")
    print(f"Interview questions generated: {len(result.interview_prep.questions)}")

    print("\nSample interview questions:")
    for q in result.interview_prep.questions[:3]:
        print(f"  Q: {q.question}")
        print(f"     (based on: \"{q.bullet_text}\")\n")


if __name__ == "__main__":
    test_pipeline()