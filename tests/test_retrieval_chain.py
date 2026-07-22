"""Manual test: extract facts from a resume, embed them into Chroma,
then run a few sample queries to sanity-check that semantic search
actually finds related facts — even when wording differs."""

from src.chains.extraction_chain import extract_facts_with_retry
from src.chains.retrieval_chain import build_vector_store, retrieve_relevant_facts


def test_retrieval_on_sample():
    with open("src/data/resumes/resume_2.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()

    print("Extracting facts (this calls the LLM, may take a few seconds)...")
    ledger = extract_facts_with_retry(resume_text, resume_id="resume_2")
    print(f"Extracted {len(ledger.facts)} facts.\n")

    print("Building vector store (embedding facts locally, no API calls)...")
    vector_store = build_vector_store(ledger)
    print("Vector store built.\n")

    test_queries = [
        "stakeholder management",          # tests meaning-based match, not exact wording
        "reducing AI hallucination",       # should match the RAG/fabrication-reduction fact
        "cloud infrastructure experience", # should match AWS-related facts
    ]

    for query in test_queries:
        print(f"--- Query: \"{query}\" ---")
        results = retrieve_relevant_facts(vector_store, query, k=3)
        for doc in results:
            print(f"  [{doc.metadata['fact_id']}] ({doc.metadata['fact_type']}) {doc.page_content}")
        print()


if __name__ == "__main__":
    test_retrieval_on_sample()