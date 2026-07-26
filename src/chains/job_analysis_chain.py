"""
Job Posting Analysis Chain — extracts structured requirements from a
raw job posting. Mirrors Day 2's extraction pattern: LLM + Pydantic
parser + retry, applied to a different input/output shape.
"""

import os
import time
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq

from src.schemas.job_requirements import JobRequirements

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found. Check your .env file.")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0,
)

parser = PydanticOutputParser(pydantic_object=JobRequirements)

JOB_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a precise job posting analyzer. Your job is to extract
the concrete requirements from the posting below.

STRICT RULES:
- Extract only what the posting actually states — do not infer requirements
  that aren't explicitly mentioned.
- Classify each requirement as 'must_have' (explicitly required, or listed
  under a "Requirements"/"What we are looking for" section) or 'nice_to_have'
  (listed under a "Nice to have"/"Preferred" section).
- Keep each requirement atomic — one skill or qualification per entry.
- Assign each requirement a unique requirement_id like 'req_001', 'req_002'.
- Do NOT include trailing empty objects or incomplete entries.

{format_instructions}
"""),
    ("human", "Posting ID: {posting_id}\n\nJob posting text:\n{posting_text}")
])


def build_job_analysis_chain():
    return JOB_ANALYSIS_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    ) | llm | parser


def extract_requirements_with_retry(
    posting_text: str, posting_id: str, max_retries: int = 3
) -> JobRequirements:
    chain = build_job_analysis_chain()
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            result = chain.invoke({
                "posting_id": posting_id,
                "posting_text": posting_text,
            })
            return result
        except Exception as e:
            last_error = e
            print(f"⚠️  Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = 15
                print(f"Waiting {wait_time}s before retrying...")
                time.sleep(wait_time)

    raise RuntimeError(
        f"Job requirements extraction failed after {max_retries} attempts. Last error: {last_error}"
    )