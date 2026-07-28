"""Manual test: run the full pipeline through routing, then generate
both the ATS score and red-flag report from the same routing result."""

from src.chains.extraction_chain import extract_facts_with_retry
from src.chains.retrieval_chain import build_vector_store
from src.chains.job_analysis_chain import extract_requirements_with_retry
from src.chains.router_chain import route_requirements
from src.chains.ats_score_chain import compute_ats_score
from src.chains.red_flag_chain import build_red_flag_report


def test_ats_and_redflag():
    with open("src/data/resumes/resume_1.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    with open("src/data/job_postings/posting_1.txt", "r", encoding="utf-8") as f:
        posting_text = f.read()

    print("Extracting facts and requirements...")
    ledger = extract_facts_with_retry(resume_text, resume_id="resume_1")
    vector_store = build_vector_store(ledger)
    job_reqs = extract_requirements_with_retry(posting_text, posting_id="posting_1")
    routing = route_requirements(job_reqs, vector_store, resume_id="resume_1")
    print(f"Matched: {len(routing.matched)}, Gaps: {len(routing.gaps)}\n")

    print("Computing ATS score...")
    ats = compute_ats_score(job_reqs, ledger)
    print(f"\n{'='*50}")
    print(f"ATS SCORE: {ats.score}/100")
    print(f"{'='*50}")
    print(f"Disclaimer: {ats.disclaimer}\n")
    for check in ats.checks:
        status = "✅" if check.passed else "❌"
        print(f"  {status} {check.check_name}: {check.detail}")

    print("\nBuilding red-flag report (this calls the LLM once per gap)...")
    red_flags = build_red_flag_report(routing)
    print(f"\n{'='*50}")
    print(f"RED-FLAG REPORT ({red_flags.total_gaps} total gaps)")
    print(f"{'='*50}")

    print(f"\nMUST-HAVE GAPS ({len(red_flags.must_have_gaps)}):")
    for item in red_flags.must_have_gaps:
        print(f"  🔴 {item.requirement_text}")
        print(f"      Suggestion: {item.suggestion}\n")

    print(f"NICE-TO-HAVE GAPS ({len(red_flags.nice_to_have_gaps)}):")
    for item in red_flags.nice_to_have_gaps:
        print(f"  🟡 {item.requirement_text}")
        print(f"      Suggestion: {item.suggestion}\n")


if __name__ == "__main__":
    test_ats_and_redflag()