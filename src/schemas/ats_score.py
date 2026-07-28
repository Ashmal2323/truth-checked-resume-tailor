"""
Pydantic schema for the ATS (Applicant Tracking System) score —
a best-effort SIMULATION of how automated resume-scanning software
might evaluate a resume, not a guarantee of any real ATS's behavior.
There is no universal ATS standard, so this is deliberately framed
as an estimate with concrete, explainable reasoning.
"""

from pydantic import BaseModel, Field


class ATSCheckItem(BaseModel):
    """One individual check contributing to the overall score."""
    check_name: str
    passed: bool
    detail: str = Field(..., description="Plain-language explanation of this check's result.")


class ATSScoreReport(BaseModel):
    resume_id: str
    posting_id: str
    score: int = Field(..., ge=0, le=100, description="Overall estimated score, 0-100.")
    keyword_match_ratio: float = Field(..., ge=0.0, le=1.0)
    checks: list[ATSCheckItem] = Field(default_factory=list)
    disclaimer: str = (
        "This score is a best-effort simulation based on keyword overlap and "
        "common formatting checks. Real ATS systems vary widely and there is "
        "no universal standard — treat this as directional guidance, not a guarantee."
    )