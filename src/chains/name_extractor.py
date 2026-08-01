"""
Lightweight name extractor — pulls the candidate's name from raw
resume text. Kept separate from the Facts Ledger (Day 1-2's schema)
since a person's name isn't really a "fact" to verify — it's metadata
needed for display purposes only, like the PDF header.
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0,
)

NAME_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Extract ONLY the candidate's full name from the top of this
resume. Return just the name, nothing else — no titles, no job title, no
explanation. If no clear name is present, return exactly: Unknown Candidate"""),
    ("human", "{resume_text}")
])


def extract_candidate_name(resume_text: str) -> str:
    """Returns the candidate's name, or 'Unknown Candidate' if extraction
    fails or no clear name is found — never a fabricated placeholder name."""
    try:
        chain = NAME_PROMPT | llm | StrOutputParser()
        # Only need the first chunk of text — name is always at the top
        name = chain.invoke({"resume_text": resume_text[:500]}).strip()
        return name if name else "Unknown Candidate"
    except Exception:
        return "Unknown Candidate"