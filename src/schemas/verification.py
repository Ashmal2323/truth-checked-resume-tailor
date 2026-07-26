"""
Pydantic schemas for verification results — the pass/fail record
for every generated bullet, checked against the real Facts Ledger.
"""

from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    """The verdict for one generated bullet."""

    requirement_id: str
    bullet_text: str
    is_supported: bool = Field(
        ..., description="True only if every claim in the bullet is provable from the cited facts."
    )
    reasoning: str = Field(
        ..., description="Brief explanation of why this bullet was approved or rejected."
    )
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Specific phrases/claims in the bullet that could NOT be traced to a fact, if any."
    )


class VerificationReport(BaseModel):
    resume_id: str
    posting_id: str
    results: list[VerificationResult] = Field(default_factory=list)

    @property
    def approved_bullets(self) -> list[VerificationResult]:
        return [r for r in self.results if r.is_supported]

    @property
    def rejected_bullets(self) -> list[VerificationResult]:
        return [r for r in self.results if not r.is_supported]

    @property
    def fabrication_rate(self) -> float:
        """The headline metric your whole project is built around.
        0.0 means every generated bullet was fully supported by real facts."""
        if not self.results:
            return 0.0
        return len(self.rejected_bullets) / len(self.results)