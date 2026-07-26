"""
Pydantic schemas for generated resume content — one bullet per
matched requirement, generated strictly from retrieved facts.
"""

from pydantic import BaseModel, Field


class GeneratedBullet(BaseModel):
    """A single tailored resume bullet, tied back to the requirement
    it addresses and the facts it's supposed to be built from."""

    requirement_id: str = Field(..., description="Which job requirement this bullet addresses.")
    bullet_text: str = Field(
        ...,
        min_length=1,
        max_length=400,
        description="The tailored resume bullet text."
    )
    source_fact_ids: list[str] = Field(
        ...,
        description="The fact_id(s) this bullet claims to be based on. Used by the "
                    "verification chain to check the claim against the real ledger."
    )


class GeneratedResumeContent(BaseModel):
    """All generated bullets for one resume/job posting pairing."""

    resume_id: str
    posting_id: str
    bullets: list[GeneratedBullet] = Field(default_factory=list)