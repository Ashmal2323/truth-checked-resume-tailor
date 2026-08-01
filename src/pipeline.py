"""
End-to-End Pipeline — the single function that ties together every
chain built across Days 2-7. This is what Day 9's Gradio app will
call directly: resume + job posting text in, all four deliverables
out. Each stage is logged so failures are traceable to a specific step.
"""

import os
from dataclasses import dataclass

from src.chains.extraction_chain import extract_facts_with_retry
from src.chains.retrieval_chain import build_vector_store
from src.chains.job_analysis_chain import extract_requirements_with_retry
from src.chains.router_chain import route_requirements
from src.chains.generation_chain import generate_bullets_with_retry
from src.chains.verification_chain import verify_all_bullets
from src.chains.ats_score_chain import compute_ats_score
from src.chains.red_flag_chain import build_red_flag_report
from src.chains.interview_prep_chain import build_interview_prep
from src.chains.pdf_generator import generate_resume_pdf
from src.chains.name_extractor import extract_candidate_name

@dataclass
class PipelineResult:
    pdf_path: str
    fabrication_rate: float
    ats_score: int
    red_flag_report: object
    interview_prep: object
    verification_report: object


def run_full_pipeline(
    resume_text: str,
    posting_text: str,
    resume_id: str,
    posting_id: str,
    output_dir: str = "outputs",
) -> PipelineResult:
    """Runs the complete Truth-Checked Resume Tailor pipeline end to end."""

    os.makedirs(output_dir, exist_ok=True)

    print(f"[1/7] Extracting resume facts ({resume_id})...")
    ledger = extract_facts_with_retry(resume_text, resume_id=resume_id)
    candidate_name = extract_candidate_name(resume_text)

    print(f"[2/7] Building vector store...")
    vector_store = build_vector_store(ledger)

    print(f"[3/7] Extracting job requirements ({posting_id})...")
    job_reqs = extract_requirements_with_retry(posting_text, posting_id=posting_id)

    print(f"[4/7] Routing matched/gap requirements...")
    routing = route_requirements(job_reqs, vector_store, resume_id=resume_id)

    print(f"[5/7] Generating tailored bullets...")
    generated = generate_bullets_with_retry(routing, ledger)

    print(f"[6/7] Verifying every bullet against real facts...")
    verification = verify_all_bullets(generated, ledger)
    print(f"    Fabrication rate: {verification.fabrication_rate:.1%}")

    print(f"[7/7] Building ATS score, red-flag report, interview prep, and PDF...")
    ats = compute_ats_score(job_reqs, ledger)
    red_flags = build_red_flag_report(routing)
    interview_prep = build_interview_prep(verification)

    pdf_path = os.path.join(output_dir, f"{resume_id}_{posting_id}_tailored.pdf")
    generate_resume_pdf(verification, ledger, job_reqs.job_title, pdf_path, candidate_name=candidate_name)

    print("Pipeline complete.\n")

    return PipelineResult(
        pdf_path=pdf_path,
        fabrication_rate=verification.fabrication_rate,
        ats_score=ats.score,
        red_flag_report=red_flags,
        interview_prep=interview_prep,
        verification_report=verification,
    )