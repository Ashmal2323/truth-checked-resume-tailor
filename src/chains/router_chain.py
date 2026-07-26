"""
Matched/Gap Router — for each job requirement, searches the candidate's
FactsLedger (via Day 3's retrieval) for genuinely relevant supporting
facts. Requirements with a strong match go to 'matched' (for Day 5's
generation step); everything else goes to 'gap' (for the red-flag
report). This is the enforcement point for "never invent — only
report what's真实ly there."
"""

from pydantic import BaseModel, Field
from langchain_chroma import Chroma

from src.schemas.job_requirements import JobRequirement, JobRequirements
from src.chains.retrieval_chain import retrieve_relevant_facts

# Below this similarity distance, a "match" is too weak to trust.
# Chroma's default similarity_search returns closest-first, but doesn't
# give us a normalized 0-1 score directly — so we use the score-aware
# variant and a distance threshold determined by manual testing.
RELEVANCE_DISTANCE_THRESHOLD = 1.10  


class RoutedRequirement(BaseModel):
    """A requirement, tagged with whatever supporting facts (if any)
    were found, and the resulting matched/gap classification."""
    requirement: JobRequirement
    supporting_fact_ids: list[str] = Field(default_factory=list)
    is_matched: bool = False


class RoutingResult(BaseModel):
    posting_id: str
    resume_id: str
    matched: list[RoutedRequirement] = Field(default_factory=list)
    gaps: list[RoutedRequirement] = Field(default_factory=list)


def route_requirements(
    job_requirements: JobRequirements,
    vector_store: Chroma,
    resume_id: str,
    k: int = 3,
) -> RoutingResult:
    """For each requirement, retrieve the top-k candidate facts and check
    if any is close enough to count as a genuine match. This is the
    'never invent' enforcement point: only requirements with strong,
    real supporting evidence get routed to 'matched'."""

    result = RoutingResult(posting_id=job_requirements.posting_id, resume_id=resume_id)

    for req in job_requirements.requirements:
        # similarity_search_with_score returns (Document, distance) pairs —
        # lower distance means more semantically similar.
        scored_results = vector_store.similarity_search_with_score(req.text, k=k)

        supporting_ids = [
            doc.metadata["fact_id"]
            for doc, distance in scored_results
            if distance <= RELEVANCE_DISTANCE_THRESHOLD
        ]

        routed = RoutedRequirement(
            requirement=req,
            supporting_fact_ids=supporting_ids,
            is_matched=len(supporting_ids) > 0,
        )

        if routed.is_matched:
            result.matched.append(routed)
        else:
            result.gaps.append(routed)

    return result