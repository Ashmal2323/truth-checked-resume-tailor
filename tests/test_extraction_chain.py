"""Manual test: run extraction on real sample resumes and print
the result so you can manually verify no facts are missing,
misgrouped, or invented — per Day 2's plan."""

from src.chains.extraction_chain import extract_facts_with_retry

def test_extraction_on_sample(resume_filename: str, resume_id: str):
    with open(f"src/data/resumes/{resume_filename}", "r", encoding="utf-8") as f:
        resume_text = f.read()

    ledger = extract_facts_with_retry(resume_text, resume_id=resume_id)

    print(f"\n✅ Extracted {len(ledger.facts)} facts from {resume_id}:\n")
    for fact in ledger.facts:
        print(f"  [{fact.fact_id}] ({fact.fact_type.value}) {fact.content}")
        print(f"      source: \"{fact.source_line}\"\n")

if __name__ == "__main__":
    test_extraction_on_sample("resume_3.txt", "resume_3")