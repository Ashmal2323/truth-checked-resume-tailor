"""End-to-end test: extract facts, retrieve, route, generate bullets,
then verify every single one. This is the real proof of the project's
core claim — print the fabrication rate at the end."""

from src.chains.extraction_chain import extract_facts_with_retry
from src.chains.retrieval_chain import build_vector_store
from src.chains.job_analysis_chain import extract_requirements_with_retry
from src.chains.router_chain import route_requirements
from src.chains.generation_chain import generate_bullets_with_retry
from src.chains.verification_chain import verify_all_bullets


def test_full_pipeline():
    with open("src/data/resumes/resume_1.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    with open("src/data/job_postings/posting_1.txt", "r", encoding="utf-8") as f:
        posting_text = f.read()

    print("1. Extracting resume facts...")
    ledger = extract_facts_with_retry(resume_text, resume_id="resume_1")
    print(f"   Got {len(ledger.facts)} facts.\n")

    print("2. Building vector store...")
    vector_store = build_vector_store(ledger)

    print("3. Extracting job requirements...")
    job_reqs = extract_requirements_with_retry(posting_text, posting_id="posting_1")
    print(f"   Got {len(job_reqs.requirements)} requirements.\n")

    print("4. Routing matched/gap...")
    routing = route_requirements(job_reqs, vector_store, resume_id="resume_1")
    print(f"   Matched: {len(routing.matched)}, Gaps: {len(routing.gaps)}\n")

    print("5. Generating tailored bullets...")
    generated = generate_bullets_with_retry(routing, ledger)
    print(f"   Generated {len(generated.bullets)} bullets:\n")
    for b in generated.bullets:
        print(f"   [{b.requirement_id}] {b.bullet_text}")
        print(f"       (based on: {b.source_fact_ids})\n")

    print("6. Verifying every bullet against real facts...")
    report = verify_all_bullets(generated, ledger)

    print(f"\n{'='*60}")
    print(f"FABRICATION RATE: {report.fabrication_rate:.1%}")
    print(f"{'='*60}\n")

    print(f"APPROVED ({len(report.approved_bullets)}):")
    for r in report.approved_bullets:
        print(f"  ✅ [{r.requirement_id}] {r.bullet_text}")
        print(f"      reasoning: {r.reasoning}\n")

    print(f"REJECTED ({len(report.rejected_bullets)}):")
    for r in report.rejected_bullets:
        print(f"  ❌ [{r.requirement_id}] {r.bullet_text}")
        print(f"      reasoning: {r.reasoning}")
        print(f"      unsupported: {r.unsupported_claims}\n")


if __name__ == "__main__":
    test_full_pipeline()