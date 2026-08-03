"""Quick diagnostic: re-run the exact same resume/posting pair and print
full verification reasoning for every bullet, so we can see WHY specific
bullets were rejected — same level of detail as Day 5's test script."""

from src.pipeline import run_full_pipeline

# Paste your actual resume_2 text and posting_2 text below, or load from file:
with open("src/data/resumes/resume_2.txt", "r", encoding="utf-8") as f:
    resume_text = f.read()
with open("src/data/job_postings/posting_2.txt", "r", encoding="utf-8") as f:
    posting_text = f.read()

result = run_full_pipeline(
    resume_text=resume_text,
    posting_text=posting_text,
    resume_id="resume_2",
    posting_id="posting_2",
)

print(f"\nFABRICATION RATE: {result.fabrication_rate:.1%}\n")

print("APPROVED:")
for r in result.verification_report.approved_bullets:
    print(f"  ✅ {r.bullet_text}")

print("\nREJECTED:")
for r in result.verification_report.rejected_bullets:
    print(f"  ❌ {r.bullet_text}")
    print(f"      reasoning: {r.reasoning}")
    print(f"      unsupported: {r.unsupported_claims}\n")