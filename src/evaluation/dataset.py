"""
Evaluation dataset definition — a curated set of (resume, job posting)
pairs for LangSmith evaluation. Deliberately includes strong matches,
partial matches, and one clearly weak match (posting_3 against an
unrelated resume) to test that the system behaves honestly across
the full range of match quality, not just easy cases.
"""

import os

RESUME_DIR = "src/data/resumes"
POSTING_DIR = "src/data/job_postings"


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Each entry: (resume_filename, resume_id, posting_filename, posting_id, expected_match_quality)
# expected_match_quality is a human judgment call, used only for our own
# sanity-checking of results — NOT fed into the pipeline itself.
EVAL_PAIRS = [
    ("resume_1.txt", "resume_1", "posting_1.txt", "posting_1", "strong"),   # AI Engineer x AI Engineer
    ("resume_2.txt", "resume_2", "posting_2.txt", "posting_2", "strong"),   # Full Stack x Full Stack
    ("resume_3.txt", "resume_3", "posting_1.txt", "posting_1", "weak"),     # cross-match, likely weak
    ("resume_1.txt", "resume_1", "posting_3.txt", "posting_3", "weak"),    # deliberately mismatched
    ("resume_2.txt", "resume_2", "posting_1.txt", "posting_1", "weak"),    # Full Stack x AI posting
    ("resume_3.txt", "resume_3", "posting_2.txt", "posting_2", "partial"), # cross-match, partial overlap possible
]


def build_eval_dataset() -> list[dict]:
    """Returns a list of dicts ready to upload as LangSmith dataset examples."""
    examples = []
    for resume_file, resume_id, posting_file, posting_id, expected in EVAL_PAIRS:
        resume_text = load_text(os.path.join(RESUME_DIR, resume_file))
        posting_text = load_text(os.path.join(POSTING_DIR, posting_file))
        examples.append({
            "inputs": {
                "resume_text": resume_text,
                "posting_text": posting_text,
                "resume_id": resume_id,
                "posting_id": posting_id,
            },
            "outputs": {
                "expected_match_quality": expected,
            },
        })
    return examples