"""
Custom LangSmith evaluators for the Truth-Checked Resume Tailor.
Each evaluator takes a pipeline run's output and produces a named,
numeric score LangSmith can track and chart across runs.
"""


def fabrication_rate_evaluator(run, example) -> dict:
    """The headline metric. Lower is better; 0.0 is the goal.
    Pulled directly from the real VerificationReport, not estimated."""
    outputs = run.outputs or {}
    rate = outputs.get("fabrication_rate", None)
    if rate is None:
        return {"key": "fabrication_rate", "score": None, "comment": "No fabrication_rate in output."}
    return {
        "key": "fabrication_rate",
        "score": rate,
        "comment": f"{rate:.1%} of generated bullets were rejected as unsupported.",
    }


def requirement_coverage_evaluator(run, example) -> dict:
    """Of all requirements the router found a genuine match for, how many
    survived verification (i.e. actually made it into the final resume)?
    This measures generation+verification quality, not just routing."""
    outputs = run.outputs or {}
    matched_count = outputs.get("matched_count", 0)
    approved_count = outputs.get("approved_count", 0)
    if matched_count == 0:
        return {"key": "requirement_coverage", "score": None, "comment": "No matched requirements to evaluate."}
    coverage = approved_count / matched_count
    return {
        "key": "requirement_coverage",
        "score": coverage,
        "comment": f"{approved_count}/{matched_count} matched requirements survived verification.",
    }


def latency_evaluator(run, example) -> dict:
    """Wall-clock time for the full pipeline run, in seconds."""
    outputs = run.outputs or {}
    duration = outputs.get("duration_seconds", None)
    if duration is None:
        return {"key": "latency_seconds", "score": None}
    return {
        "key": "latency_seconds",
        "score": round(duration, 4),
        "comment": f"Full pipeline took {duration:.1f}s.",
    }