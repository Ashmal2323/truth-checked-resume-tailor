"""
Targeted re-run for evaluation pairs that failed due to the Groq daily
token limit (not a code bug — see Day 8 notes). Re-runs ONLY the
specific failed examples, logging results to the SAME LangSmith
dataset/experiment lineage, rather than re-running the whole suite
and wasting tokens re-doing pairs that already succeeded.
"""

import time
from langsmith import Client
from langsmith.evaluation import evaluate

from src.evaluation.dataset import build_eval_dataset
from src.evaluation.eval_runner import pipeline_for_eval, DATASET_NAME
from src.evaluation.evaluators import (
    fabrication_rate_evaluator,
    requirement_coverage_evaluator,
    latency_evaluator,
)

# From the LangSmith dashboard: rows 3 and 5 (0-indexed: 2 and 4) failed
# with "Extraction failed after 3 attempts" due to the daily token cap.
FAILED_INDICES = [2, 4]


def get_failed_examples():
    client = Client()
    dataset = list(client.list_datasets(dataset_name=DATASET_NAME))[0]
    all_examples = list(client.list_examples(dataset_id=dataset.id))
    # LangSmith doesn't guarantee example order matches our original list,
    # so we match by resume_id/posting_id pairs instead of raw index,
    # to be safe and explicit rather than assuming ordering held.
    all_pairs = build_eval_dataset()
    target_pairs = [all_pairs[i]["inputs"] for i in FAILED_INDICES]

    matched = []
    for ex in all_examples:
        for target in target_pairs:
            if (ex.inputs.get("resume_id") == target["resume_id"]
                    and ex.inputs.get("posting_id") == target["posting_id"]):
                matched.append(ex)
    return dataset, matched


def rerun_missing():
    dataset, failed_examples = get_failed_examples()
    print(f"Found {len(failed_examples)} example(s) to re-run:")
    for ex in failed_examples:
        print(f"  - resume_id={ex.inputs.get('resume_id')}, posting_id={ex.inputs.get('posting_id')}")

    if not failed_examples:
        print("No matching examples found — check FAILED_INDICES against dataset.py.")
        return

    results = evaluate(
        pipeline_for_eval,
        data=failed_examples,  # pass the actual Example objects, not just their IDs
        evaluators=[
            fabrication_rate_evaluator,
            requirement_coverage_evaluator,
            latency_evaluator,
        ],
        experiment_prefix="resume-tailor-eval-retry",
        max_concurrency=1,
    )
    print("\nRe-run complete. Check LangSmith dashboard — this creates a NEW experiment "
          "for just these 2 examples, which you can view alongside the original.")


if __name__ == "__main__":
    rerun_missing()