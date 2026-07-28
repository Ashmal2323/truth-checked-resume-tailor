"""
Red-Flag Report Chain — takes Day 4's routing gaps and produces a
ranked, actionable report. Mostly deterministic (sorting by priority,
already known from job_requirements), with one light LLM call per
gap to generate a short, honest suggestion — NOT to invent whether
the candidate has the skill, only to suggest how they might address
a genuine, confirmed gap (e.g. "consider a short course," "highlight
transferable experience if any exists elsewhere").
"""

import os
import time
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from src.schemas.red_flag_report import RedFlagItem, RedFlagReport
from src.schemas.job_requirements import RequirementPriority
from src.chains.router_chain import RoutingResult

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found. Check your .env file.")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

SUGGESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You give brief, honest, practical suggestions for addressing a
resume gap. You are NOT verifying whether the candidate has this skill — that
has already been confirmed as a genuine gap. Your only job is to suggest a
realistic next step (e.g. a specific type of course, a way to highlight
related/transferable experience if it plausibly exists, or simply noting
it's worth learning before applying). Keep it to one sentence. Never claim
the candidate already has this skill."""),
    ("human", "Missing requirement: {requirement_text}")
])


def build_suggestion_chain():
    return SUGGESTION_PROMPT | llm | StrOutputParser()


def generate_suggestion_with_retry(requirement_text: str, max_retries: int = 2) -> str:
    chain = build_suggestion_chain()
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return chain.invoke({"requirement_text": requirement_text}).strip()
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(10)
    # Fail gracefully — a missing suggestion is not critical enough to
    # crash the whole report.
    return "Consider addressing this gap before applying, if relevant to your goals."


def build_red_flag_report(routing_result: RoutingResult) -> RedFlagReport:
    report = RedFlagReport(
        resume_id=routing_result.resume_id,
        posting_id=routing_result.posting_id,
    )

    for gap in routing_result.gaps:
        suggestion = generate_suggestion_with_retry(gap.requirement.text)
        item = RedFlagItem(
            requirement_id=gap.requirement.requirement_id,
            requirement_text=gap.requirement.text,
            priority=gap.requirement.priority,
            suggestion=suggestion,
        )
        if gap.requirement.priority == RequirementPriority.MUST_HAVE:
            report.must_have_gaps.append(item)
        else:
            report.nice_to_have_gaps.append(item)

    return report