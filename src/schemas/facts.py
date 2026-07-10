"""
Pydantic schemas for the Facts Ledger — the single source of truth
that every later chain (retrieval, generation, verification) must
trace back to. Nothing downstream is allowed to assert something
that isn't represented here.
"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class FactType(str, Enum):
    """Controlled vocabulary for what kind of fact this is.
    Using an Enum (not a free-text string) means the LLM's output
    is constrained to a known set of categories, which makes later
    routing/filtering logic reliable instead of guessing at strings."""
    SKILL = "skill"
    PROJECT = "project"
    QUANTIFIED_RESULT = "quantified_result"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CERTIFICATION = "certification"


class Fact(BaseModel):
    """A single, atomic, traceable claim extracted from a real resume."""

    fact_id: str = Field(
        ...,
        description="Unique identifier, e.g. 'fact_001'. Assigned at extraction time."
    )
    fact_type: FactType = Field(
        ...,
        description="What category of fact this is."
    )
    content: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The fact itself in plain language, e.g. 'Reduced reporting time by 30%'."
    )
    source_line: str = Field(
        ...,
        description="The exact line/sentence from the original resume this fact came from. "
                    "This is what makes verification possible later — every fact must be "
                    "traceable back to real text, not inferred or summarized away."
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Extraction confidence. Reserved for future use if we ever soft-flag "
                    "ambiguous extractions instead of hard-accepting them."
    )

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty_ish(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Fact content cannot be empty or whitespace-only.")
        return v.strip()


class FactsLedger(BaseModel):
    """The complete set of verified facts extracted from one resume.
    This is the object every later step (retrieval, generation,
    verification) reads from — and NEVER writes new facts into."""

    resume_id: str = Field(..., description="Identifier for the source resume, e.g. filename.")
    facts: list[Fact] = Field(default_factory=list)

    def get_by_type(self, fact_type: FactType) -> list[Fact]:
        """Helper used later by the router (Day 4) to split facts by category."""
        return [f for f in self.facts if f.fact_type == fact_type]

    def as_context_string(self) -> str:
        """Flattens facts into a plain-text block for prompt injection.
        Used later in Day 5's generation chain — the model is only ever
        shown facts through this method, never the raw resume text again."""
        lines = [f"[{f.fact_id}] ({f.fact_type.value}) {f.content}" for f in self.facts]
        return "\n".join(lines)