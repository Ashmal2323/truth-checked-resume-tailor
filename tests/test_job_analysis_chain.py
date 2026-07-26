"""Manual test: extract structured requirements from a real job posting."""

from src.chains.job_analysis_chain import extract_requirements_with_retry

def test_job_analysis():
    with open("src/data/job_postings/posting_1.txt", "r", encoding="utf-8") as f:
        posting_text = f.read()

    result = extract_requirements_with_retry(posting_text, posting_id="posting_1")

    print(f"\n✅ Job Title: {result.job_title}")
    print(f"Extracted {len(result.requirements)} requirements:\n")
    for req in result.requirements:
        print(f"  [{req.requirement_id}] ({req.priority.value}) {req.text}")

if __name__ == "__main__":
    test_job_analysis()