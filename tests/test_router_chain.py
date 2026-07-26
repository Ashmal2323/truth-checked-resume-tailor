"""Manual test: run the full pipeline (extract facts, build retriever,
extract job requirements, route matched/gap) and print raw distances
so we can calibrate RELEVANCE_DISTANCE_THRESHOLD based on real numbers,
not a guess."""

from src.chains.extraction_chain import extract_facts_with_retry
from src.chains.retrieval_chain import build_vector_store
from src.chains.job_analysis_chain import extract_requirements_with_retry
from src.chains.router_chain import route_requirements


def test_router():
    with open("src/data/resumes/resume_1.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    with open("src/data/job_postings/posting_1.txt", "r", encoding="utf-8") as f:
        posting_text = f.read()

    print("Extracting resume facts...")
    ledger = extract_facts_with_retry(resume_text, resume_id="resume_1")
    print(f"Got {len(ledger.facts)} facts.\n")

    print("Building vector store...")
    vector_store = build_vector_store(ledger)

    print("Extracting job requirements...")
    job_reqs = extract_requirements_with_retry(posting_text, posting_id="posting_1")
    print(f"Got {len(job_reqs.requirements)} requirements.\n")

    print("--- Raw similarity distances (for threshold calibration) ---\n")
    for req in job_reqs.requirements:
        scored = vector_store.similarity_search_with_score(req.text, k=2)
        print(f"[{req.requirement_id}] {req.text}")
        for doc, distance in scored:
            print(f"    distance={distance:.3f}  ->  {doc.page_content}")
        print()

    print("--- Routing result (using current threshold) ---\n")
    routing = route_requirements(job_reqs, vector_store, resume_id="resume_1")

    print(f"MATCHED ({len(routing.matched)}):")
    for r in routing.matched:
        print(f"  ✅ [{r.requirement.requirement_id}] {r.requirement.text} -> facts: {r.supporting_fact_ids}")

    print(f"\nGAPS ({len(routing.gaps)}):")
    for r in routing.gaps:
        print(f"  ❌ [{r.requirement.requirement_id}] {r.requirement.text}")


if __name__ == "__main__":
    test_router()