"""
Pydantic schema for structured job requirements — extracted from a
raw job posting so we can systematically compare each requirement
against the candidate's FactsLedger, rather than doing vague,
unstructured comparison.
"""

from enum import Enum
from pydantic import BaseModel, Field


class RequirementPriority(str, Enum):
    """How strongly the posting emphasizes this requirement. Used later
    (Day 6) to weight the red-flag report by severity — a missing
    'must-have' matters more than a missing 'nice-to-have'."""
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"


class JobRequirement(BaseModel):
    """A single, atomic requirement extracted from a job posting."""

    requirement_id: str = Field(..., description="Unique id, e.g. 'req_001'.")
    text: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="The requirement in plain language, e.g. 'Experience with AWS'."
    )
    priority: RequirementPriority = Field(
        ...,
        description="Whether the posting treats this as required or preferred."
    )


class JobRequirements(BaseModel):
    """All requirements extracted from one job posting."""

    posting_id: str = Field(..., description="Identifier for the source posting, e.g. filename.")
    job_title: str = Field(..., min_length=1, description="The job title as stated in the posting.")
    requirements: list[JobRequirement] = Field(default_factory=list)