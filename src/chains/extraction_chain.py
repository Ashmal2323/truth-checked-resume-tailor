"""
Facts Extraction Chain — turns raw resume text into a structured
FactsLedger. This is the first and most important place fabrication
risk can enter the system: if a fact is invented or distorted here,
no later verification step can fully catch it, because verification
only checks generated text AGAINST this ledger.
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.schemas.facts import FactsLedger
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError(
        "GOOGLE_API_KEY not found. Check your .env file."
    )

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    google_api_key=GOOGLE_API_KEY,
    temperature=0,
)

# The parser reads our Pydantic schema and knows exactly what JSON
# shape to expect and validate against.
parser = PydanticOutputParser(pydantic_object=FactsLedger)

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a precise resume-fact extractor. Your ONLY job is to
break down the resume below into individual, atomic facts.

STRICT RULES:
- Every fact MUST be traceable to an exact line/sentence in the original resume (source_line).
- NEVER infer, assume, or add anything not explicitly stated in the text.
- NEVER combine multiple claims into one fact — keep facts atomic (one skill, one result, one project each).
- If a number or result is mentioned, extract it as a QUANTIFIED_RESULT fact.
- Assign each fact a unique fact_id like 'fact_001', 'fact_002', etc.

{format_instructions}
"""),
    ("human", "Resume ID: {resume_id}\n\nResume text:\n{resume_text}")
])


def build_extraction_chain():
    """Returns the LCEL chain: prompt -> LLM -> parser.
    The '|' operator pipes the output of one step into the input of the next."""
    return EXTRACTION_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    ) | llm | parser


import time

def extract_facts_with_retry(resume_text: str, resume_id: str, max_retries: int = 1) -> FactsLedger:
    """Runs extraction with a repair loop: if Gemini's free tier rate-limits us
    (common given the low free-tier request cap), we wait an appropriate amount
    before retrying, rather than hammering the API and burning through quota."""

    chain = build_extraction_chain()
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            result = chain.invoke({
                "resume_id": resume_id,
                "resume_text": resume_text,
            })
            return result
        except Exception as e:
            last_error = e
            print(f"⚠️  Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = 40  # free tier quota resets roughly every 60s; 40s is a safe buffer
                print(f"Waiting {wait_time}s before retrying (respecting free-tier rate limit)...")
                time.sleep(wait_time)

    raise RuntimeError(
        f"Extraction failed after {max_retries} attempts. Last error: {last_error}"
    )