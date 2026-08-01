"""
Pydantic schema for interview prep questions — one per VERIFIED
resume claim, so the candidate is ready to defend exactly what
their tailored resume says, and nothing more.
"""

from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    requirement_id: str
    bullet_text: str
    question: str = Field(..., min_length=1, max_length=300)


class InterviewPrepReport(BaseModel):
    resume_id: str
    posting_id: str
    questions: list[InterviewQuestion] = Field(default_factory=list)