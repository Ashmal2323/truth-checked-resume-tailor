"""
Smoke test for CI — fast, no-API-call checks that catch broken imports,
schema errors, or basic misconfiguration before deployment. Deliberately
does NOT call any LLM API (Groq) to avoid burning tokens/quota on every
single CI run, per the project's 'lightweight test gate' scope decision.
"""

def test_imports():
    """If any of these fail, something is fundamentally broken -
    a bad import, missing dependency, or syntax error."""
    from src.schemas.facts import Fact, FactsLedger, FactType
    from src.schemas.job_requirements import JobRequirement, JobRequirements
    from src.schemas.verification import VerificationResult, VerificationReport
    from src.schemas.generated_content import GeneratedBullet, GeneratedResumeContent
    from src.schemas.ats_score import ATSScoreReport
    from src.schemas.red_flag_report import RedFlagReport
    from src.schemas.interview_prep import InterviewPrepReport
    from src.chains.extraction_chain import extract_facts_with_retry
    from src.chains.retrieval_chain import build_vector_store
    from src.chains.router_chain import route_requirements
    from src.chains.generation_chain import generate_bullets_with_retry
    from src.chains.verification_chain import verify_all_bullets
    from src.chains.ats_score_chain import compute_ats_score
    from src.chains.red_flag_chain import build_red_flag_report
    from src.chains.interview_prep_chain import build_interview_prep
    from src.chains.pdf_generator import generate_resume_pdf
    from src.pipeline import run_full_pipeline
    print("✅ All core modules import successfully.")


def test_facts_schema_basic():
    """Confirms the core schema still validates correctly - the same
    check from Day 1, run automatically now instead of manually."""
    from src.schemas.facts import Fact, FactsLedger, FactType

    fact = Fact(
        fact_id="fact_001",
        fact_type=FactType.SKILL,
        content="Python",
        source_line="Skills: Python, SQL",
    )
    ledger = FactsLedger(resume_id="test", facts=[fact])
    assert len(ledger.facts) == 1
    assert ledger.get_by_type(FactType.SKILL)[0].fact_id == "fact_001"
    print("✅ Facts schema validates correctly.")


def test_ats_score_deterministic_logic():
    """Confirms the ATS scoring's keyword-matching logic (pure Python,
    no API calls) still behaves as expected."""
    from src.chains.ats_score_chain import _normalize, GENERIC_STOPWORDS

    assert _normalize("Hello, World! 123") == "hello  world  123"
    assert "working" in GENERIC_STOPWORDS
    print("✅ ATS scoring helper functions work correctly.")


if __name__ == "__main__":
    test_imports()
    test_facts_schema_basic()
    test_ats_score_deterministic_logic()
    print("\n✅ All smoke tests passed.")