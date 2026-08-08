"""
Fabrication Verification Chain — THE core guarantee of this project.
For every generated bullet, an independent LLM call checks: "is every
claim in this bullet provably supported by the cited facts, and
nothing more?" This is deliberately a SEPARATE call from generation,
using a skeptical prompt, so the model isn't grading its own homework.

A secondary, deterministic keyword-overlap check backs up the LLM
judgment as a cheap sanity check — not a replacement for it, but an
extra layer, since LLM judges can occasionally be too lenient.
"""

import os
import time
import re
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq

from src.schemas.verification import VerificationResult, VerificationReport
from src.schemas.generated_content import GeneratedResumeContent
from src.schemas.facts import FactsLedger

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found. Check your .env file.")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0,  # back to 0 — verification needs to be as consistent/strict as possible
)

parser = PydanticOutputParser(pydantic_object=VerificationResult)

VERIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a SKEPTICAL fact-checker. Your job is to catch FABRICATION —
not to reject reasonable, standard resume phrasing.

A bullet is FABRICATION (is_supported = false) if it contains:
- Any number, percentage, or metric NOT present in the cited facts.
- Any team size, duration, scope, or outcome NOT present in the cited facts.
- Any exaggeration of seniority/ownership (e.g. "led" when the fact only
  says "contributed to" or "assisted with").
- Any skill, tool, or technology NOT present in the cited facts.
- Any combination of facts that implies something neither fact states alone.

A bullet is ACCEPTABLE (is_supported = true) if it:
- States that the candidate has/used/worked with a skill that IS listed in
  the cited facts, even using standard resume verbs like "utilized," "used,"
  "applied," or "worked with" — listing a skill on a resume inherently means
  the candidate has some experience with it. Do NOT reject a bullet merely
  because the exact verb isn't quoted in the fact.
- Rephrases a fact into natural resume language WITHOUT adding new numbers,
  scope, or claims beyond what the fact states.

Focus your scrutiny on WHAT is claimed (numbers, scope, ownership, outcomes),
not on whether the exact wording matches the fact verbatim.

If you find a genuine fabrication as defined above, is_supported MUST be
false, and you must list the specific unsupported phrase(s) in
unsupported_claims. Otherwise, is_supported is true.

{format_instructions}
"""),
    ("human", """Bullet to verify: "{bullet_text}"

Cited facts (the ONLY source of truth for this bullet):
{cited_facts_text}
""")
])

def build_verification_chain():
    return VERIFICATION_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    ) | llm | parser


def _keyword_sanity_check(bullet_text: str, cited_facts_text: str) -> bool:
    """A cheap, deterministic backup check: do any numbers mentioned in the
    bullet actually appear somewhere in the cited facts? This won't catch
    subtle exaggeration, but it WILL catch a clear case of an invented
    number slipping past the LLM judge. Belt-and-suspenders, not a
    replacement for the LLM check above."""
    bullet_numbers = set(re.findall(r"\d+%?", bullet_text))
    fact_numbers = set(re.findall(r"\d+%?", cited_facts_text))
    invented_numbers = bullet_numbers - fact_numbers
    return len(invented_numbers) == 0


def verify_bullet_with_retry(
    bullet_text: str,
    source_fact_ids: list[str],
    requirement_id: str,
    ledger: FactsLedger,
    max_retries: int = 3,
) -> VerificationResult:
    """Verifies a single generated bullet against its cited source facts.

    Runs the skeptical LLM check first, then applies the deterministic
    keyword sanity check as a one-directional override: if the LLM
    approves a bullet but the sanity check finds an invented number,
    we downgrade to rejected. The reverse never happens — a rejection
    from the LLM is never overturned by the sanity check. This is
    intentional: a cheap regex check is trustworthy enough to catch an
    obvious miss, but not sophisticated enough to overrule a considered
    rejection.
    """
    fact_lookup = {f.fact_id: f for f in ledger.facts}

    chain = build_verification_chain()
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            result = chain.invoke({
                "bullet_text": bullet_text,
                "cited_facts_text": cited_facts_text,
            })

            # Backup deterministic check — if it disagrees with the LLM
            # (finds an invented number the LLM missed), we override to
            # rejected. We NEVER let the deterministic check override an
            # LLM rejection into an approval — only tighten, never loosen.
            if result.is_supported and not _keyword_sanity_check(bullet_text, cited_facts_text):
                result.is_supported = False
                result.unsupported_claims.append(
                    "Deterministic check found a number in the bullet not present in cited facts."
                )
                result.reasoning += " [Overridden by keyword sanity check: unexplained number found.]"

            result.requirement_id = requirement_id
            result.bullet_text = bullet_text
            return result

        except Exception as e:
            last_error = e
            print(f"⚠️  Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(15)

    raise RuntimeError(f"Verification failed after {max_retries} attempts. Last error: {last_error}")


def verify_all_bullets(
    generated: GeneratedResumeContent,
    ledger: FactsLedger,
) -> VerificationReport:
    """Runs verification on every generated bullet and compiles the
    final report, including the headline fabrication_rate metric."""
    report = VerificationReport(resume_id=generated.resume_id, posting_id=generated.posting_id)

    for bullet in generated.bullets:
        result = verify_bullet_with_retry(
            bullet_text=bullet.bullet_text,
            source_fact_ids=bullet.source_fact_ids,
            requirement_id=bullet.requirement_id,
            ledger=ledger,
        )
        result.source_fact_ids = bullet.source_fact_ids  # carry through for later use (e.g. PDF sectioning)
        report.results.append(result)

    return report