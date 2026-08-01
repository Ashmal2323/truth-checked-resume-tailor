"""
Interview Prep Chain — generates one likely interview question per
VERIFIED resume bullet (never per rejected/unverified content). This
keeps interview prep tightly scoped to claims the candidate can
actually defend, since those are the only claims reaching the final
resume in the first place.
"""

import os
import time
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from src.schemas.interview_prep import InterviewQuestion, InterviewPrepReport
from src.schemas.verification import VerificationReport

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found. Check your .env file.")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

QUESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You generate realistic interview questions. Given a specific
resume claim, write ONE natural interview question that a hiring manager
would likely ask to have the candidate explain or defend exactly that claim.
Keep it to one sentence, conversational, and specific to the claim given —
not generic ("tell me about yourself"). Return ONLY the question text,
nothing else."""),
    ("human", "Resume claim: \"{bullet_text}\"")
])


def build_question_chain():
    return QUESTION_PROMPT | llm | StrOutputParser()


def generate_question_with_retry(bullet_text: str, max_retries: int = 2) -> str:
    chain = build_question_chain()
    for attempt in range(1, max_retries + 1):
        try:
            return chain.invoke({"bullet_text": bullet_text}).strip()
        except Exception:
            if attempt < max_retries:
                time.sleep(10)
    return f"Can you walk me through this: \"{bullet_text}\"?"


def build_interview_prep(verification_report: VerificationReport) -> InterviewPrepReport:
    """Only generates questions for APPROVED bullets — verified claims
    the candidate can actually stand behind. Rejected/unsupported
    bullets never reach this step at all, since they never reach
    the final resume either."""
    report = InterviewPrepReport(
        resume_id=verification_report.resume_id,
        posting_id=verification_report.posting_id,
    )

    for result in verification_report.approved_bullets:
        question = generate_question_with_retry(result.bullet_text)
        report.questions.append(InterviewQuestion(
            requirement_id=result.requirement_id,
            bullet_text=result.bullet_text,
            question=question,
        ))

    return report