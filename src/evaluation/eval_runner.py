"""
Evaluation runner — wraps the full pipeline in a LangSmith-trackable
function that returns simple, flat metrics alongside the real outputs,
then runs the whole eval dataset through LangSmith's evaluate().
"""

import time
from langsmith import Client
from langsmith.evaluation import evaluate

from src.pipeline import run_full_pipeline
from src.evaluation.dataset import build_eval_dataset
from src.evaluation.evaluators import (
    fabrication_rate_evaluator,
    requirement_coverage_evaluator,
    latency_evaluator,
)

DATASET_NAME = "truth-checked-resume-tailor-eval-v1"


def pipeline_for_eval(inputs: dict) -> dict:
    """Wraps run_full_pipeline so LangSmith gets flat, evaluator-friendly
    outputs. Any exception is caught and returned as a failed run rather
    than crashing the whole evaluation sweep."""
    start = time.time()
    try:
        result = run_full_pipeline(
            resume_text=inputs["resume_text"],
            posting_text=inputs["posting_text"],
            resume_id=inputs["resume_id"],
            posting_id=inputs["posting_id"],
        )
        duration = time.time() - start

        matched_count = len(result.verification_report.results)
        approved_count = len(result.verification_report.approved_bullets)

        return {
            "fabrication_rate": result.fabrication_rate,
            "matched_count": matched_count,
            "approved_count": approved_count,
            "ats_score": result.ats_score,
            "duration_seconds": duration,
            "pdf_path": result.pdf_path,
        }
    except Exception as e:
        duration = time.time() - start
        return {
            "error": str(e),
            "duration_seconds": duration,
            "fabrication_rate": None,
            "matched_count": 0,
            "approved_count": 0,
        }


def setup_dataset(client: Client):
    """Creates the LangSmith dataset if it doesn't already exist, and
    uploads our curated eval pairs as examples."""
    existing = list(client.list_datasets(dataset_name=DATASET_NAME))
    if existing:
        print(f"Dataset '{DATASET_NAME}' already exists — reusing it.")
        return existing[0]

    dataset = client.create_dataset(dataset_name=DATASET_NAME)
    examples = build_eval_dataset()
    for ex in examples:
        client.create_example(
            inputs=ex["inputs"],
            outputs=ex["outputs"],
            dataset_id=dataset.id,
        )
    print(f"Created dataset '{DATASET_NAME}' with {len(examples)} examples.")
    return dataset


def run_evaluation():
    client = Client()
    dataset = setup_dataset(client)

    print("Running evaluation suite (this will take several minutes)...")
    results = evaluate(
        pipeline_for_eval,
        data=DATASET_NAME,
        evaluators=[
            fabrication_rate_evaluator,
            requirement_coverage_evaluator,
            latency_evaluator,
        ],
        experiment_prefix="resume-tailor-eval",
        max_concurrency=1,  # CRITICAL: our pipeline uses a shared Chroma persist
                             # directory and hits Groq's free-tier rate limits —
                             # running examples in parallel causes silent, fast
                             # failures. Force strictly sequential execution.
    )
    print("\nEvaluation complete. View results in your LangSmith dashboard.")
    return results


if __name__ == "__main__":
    run_evaluation()