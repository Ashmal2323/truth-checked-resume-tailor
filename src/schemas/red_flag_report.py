"""
Pydantic schema for the red-flag report — the gap list from Day 4's
router, ranked by how severely the job posting emphasized each
missing requirement (must_have gaps matter more than nice_to_have gaps).
"""

from pydantic import BaseModel, Field
from src.schemas.job_requirements import RequirementPriority


class RedFlagItem(BaseModel):
    requirement_id: str
    requirement_text: str
    priority: RequirementPriority
    suggestion: str = Field(
        ..., description="A short, honest suggestion for addressing this gap."
    )


class RedFlagReport(BaseModel):
    resume_id: str
    posting_id: str
    must_have_gaps: list[RedFlagItem] = Field(default_factory=list)
    nice_to_have_gaps: list[RedFlagItem] = Field(default_factory=list)

    @property
    def total_gaps(self) -> int:
        return len(self.must_have_gaps) + len(self.nice_to_have_gaps)