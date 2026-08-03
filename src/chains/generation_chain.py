"""
Generation Chain — writes tailored resume bullets for matched
requirements, using ONLY the retrieved supporting facts as source
material. The prompt strictly forbids adding anything not present
in the provided facts — this is the first line of defense against
fabrication, though it's the VERIFICATION chain (not this prompt)
that actually proves the guarantee.
"""

import os
import time
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq

from src.schemas.generated_content import GeneratedResumeContent
from src.schemas.facts import FactsLedger
from src.chains.router_chain import RoutingResult

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found. Check your .env file.")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0, 

parser = PydanticOutputParser(pydantic_object=GeneratedResumeContent)

GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a resume writer. You will be given a list of MATCHED
requirements, and for each one, the SPECIFIC facts that were found to support it.

ABSOLUTE RULES — violating these defeats the entire purpose of this system:
- You may ONLY use information contained in the provided facts. Do not add
  any skill, number, outcome, or claim that is not explicitly present in
  the facts given to you for that requirement.
- Do NOT invent metrics, team sizes, durations, or outcomes. If a fact doesn't
  contain a number, do not add one.
- Do NOT combine facts from different requirements into a single bullet unless
  they were both explicitly provided for that same requirement.
- NEVER write hedging, speculative, or uncertain language such as "no direct
  experience with X", "which may involve Y", "but not explicitly mentioned",
  or similar commentary about what ISN'T in the facts. A resume bullet states
  what the candidate DID or HAS — it never discusses gaps or uncertainty.
  If the facts don't cleanly support the requirement, write a short, confident
  bullet using ONLY what the facts actually say, without mentioning the
  requirement's other unmet aspects at all.
- Every bullet must list which fact_id(s) it is based on, in source_fact_ids.
- Write in professional resume language (action verb, concise, past tense
  where appropriate) — but the CONTENT must be fully traceable to the facts.

{format_instructions}
"""),
    ("human", """Resume ID: {resume_id}
Posting ID: {posting_id}

Matched requirements and their supporting facts:
{matched_context}
""")
])

def format_matched_context(routing_result: RoutingResult, ledger: FactsLedger) -> str:
    """Builds the human-readable block showing each matched requirement
    alongside the ACTUAL fact text it was matched to — so the generator
    never has to guess what a fact_id refers to."""
    fact_lookup = {f.fact_id: f for f in ledger.facts}
    lines = []
    for routed in routing_result.matched:
        req = routed.requirement
        lines.append(f"Requirement [{req.requirement_id}]: {req.text}")
        for fid in routed.supporting_fact_ids:
            fact = fact_lookup.get(fid)
            if fact:
                lines.append(f"  Supporting fact [{fact.fact_id}]: {fact.content}")
        lines.append("")
    return "\n".join(lines)


def build_generation_chain():
    return GENERATION_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    ) | llm | parser


def generate_bullets_with_retry(
    routing_result: RoutingResult,
    ledger: FactsLedger,
    max_retries: int = 3,
) -> GeneratedResumeContent:
    matched_context = format_matched_context(routing_result, ledger)

    if not matched_context.strip():
        # No matched requirements at all — return an empty result rather
        # than calling the LLM with nothing meaningful to work from.
        return GeneratedResumeContent(
            resume_id=routing_result.resume_id,
            posting_id=routing_result.posting_id,
            bullets=[],
        )

    chain = build_generation_chain()
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            result = chain.invoke({
                "resume_id": routing_result.resume_id,
                "posting_id": routing_result.posting_id,
                "matched_context": matched_context,
            })
            return result
        except Exception as e:
            last_error = e
            print(f"⚠️  Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = 15
                print(f"Waiting {wait_time}s before retrying...")
                time.sleep(wait_time)

    raise RuntimeError(f"Generation failed after {max_retries} attempts. Last error: {last_error}")