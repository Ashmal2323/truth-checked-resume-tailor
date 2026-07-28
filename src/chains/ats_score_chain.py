"""
ATS Score Chain — a deterministic, explainable simulation of how an
automated resume scanner might evaluate a resume. Deliberately NOT
LLM-based for the scoring logic itself: ATS scores should be
reproducible and auditable, not subject to LLM variance. We DO reuse
the job requirements already extracted (Day 4) as our keyword source,
so we're not duplicating extraction work.
"""

import re
from src.schemas.ats_score import ATSCheckItem, ATSScoreReport
from src.schemas.job_requirements import JobRequirements
from src.schemas.facts import FactsLedger


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower())


# Generic phrasing that shows up in requirement templates but isn't
# itself a meaningful keyword an ATS would search for.
GENERIC_STOPWORDS = {
    "working", "knowledge", "experience", "familiarity", "ability",
    "practical", "strong", "comfort", "with", "least", "one", "years",
    "professional", "hands", "background", "competence", "preferred",
    "comparable", "framework", "solid", "good", "excellent", "demonstrated",
    "proven", "understanding", "skills", "skill", "including", "such",
    "similar", "related", "relevant",
}


def compute_keyword_match(job_requirements: JobRequirements, ledger: FactsLedger) -> tuple[float, list[str], list[str]]:
    """Checks whether at least one meaningful skill/tool keyword from
    each requirement appears in the candidate's facts. Real ATS keyword
    scanners typically check for keyword PRESENCE, not majority-of-words
    overlap — a requirement can be phrased with lots of descriptive
    filler ("comfort with", "working knowledge of") without that filler
    being what's actually being searched for."""
    resume_text = _normalize(" ".join(f.content for f in ledger.facts))

    matched_keywords = []
    missing_keywords = []

    for req in job_requirements.requirements:
        words = [
            w for w in _normalize(req.text).split()
            if len(w) > 3 and w not in GENERIC_STOPWORDS
        ]
        if not words:
            continue
        # Presence-based: does ANY meaningful keyword show up in the resume?
        has_match = any(w in resume_text for w in words)
        if has_match:
            matched_keywords.append(req.text)
        else:
            missing_keywords.append(req.text)

    total = len(matched_keywords) + len(missing_keywords)
    ratio = len(matched_keywords) / total if total > 0 else 0.0
    return ratio, matched_keywords, missing_keywords

def check_standard_sections(ledger: FactsLedger) -> list[ATSCheckItem]:
    """Checks for presence of fact types that typically correspond to
    standard resume sections ATS systems look for."""
    from src.schemas.facts import FactType

    checks = []
    section_checks = {
        FactType.SKILL: "Skills section",
        FactType.EXPERIENCE: "Work experience section",
        FactType.EDUCATION: "Education section",
    }
    for fact_type, label in section_checks.items():
        present = any(f.fact_type == fact_type for f in ledger.facts)
        checks.append(ATSCheckItem(
            check_name=label,
            passed=present,
            detail=f"{label} {'detected' if present else 'NOT detected'} in extracted facts."
        ))
    return checks


def compute_ats_score(job_requirements: JobRequirements, ledger: FactsLedger) -> ATSScoreReport:
    keyword_ratio, matched, missing = compute_keyword_match(job_requirements, ledger)
    section_checks = check_standard_sections(ledger)

    keyword_check = ATSCheckItem(
        check_name="Keyword overlap with job posting",
        passed=keyword_ratio >= 0.5,
        detail=f"{len(matched)} of {len(matched) + len(missing)} requirements have meaningful "
               f"keyword overlap with resume content ({keyword_ratio:.0%})."
    )

    all_checks = [keyword_check] + section_checks

    # Simple, transparent scoring: keyword overlap is worth 70 points,
    # each of the 3 section checks worth 10 points. Deliberately simple
    # and explainable rather than a black-box formula.
    score = int(keyword_ratio * 70) + sum(10 for c in section_checks if c.passed)

    return ATSScoreReport(
        resume_id=ledger.resume_id,
        posting_id=job_requirements.posting_id,
        score=min(score, 100),
        keyword_match_ratio=keyword_ratio,
        checks=all_checks,
    )