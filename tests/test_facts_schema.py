"""Manual smoke test — run this to confirm the schema behaves before
trusting it inside a real chain tomorrow."""

from src.schemas.facts import Fact, FactsLedger, FactType


def test_valid_fact_and_ledger():
    fact = Fact(
        fact_id="fact_001",
        fact_type=FactType.QUANTIFIED_RESULT,
        content="Reduced reporting time by 30%",
        source_line="Built an internal dashboard that reduced reporting time by 30%.",
    )
    ledger = FactsLedger(resume_id="test_resume", facts=[fact])

    assert len(ledger.facts) == 1
    assert ledger.get_by_type(FactType.QUANTIFIED_RESULT)[0].fact_id == "fact_001"
    assert "fact_001" in ledger.as_context_string()
    print("✅ Schema works as expected.")


if __name__ == "__main__":
    test_valid_fact_and_ledger()