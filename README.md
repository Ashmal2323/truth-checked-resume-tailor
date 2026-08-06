# Truth-Checked Resume Tailor

**An AI resume-tailoring assistant that proves it doesn't lie.**

Most AI resume tools optimize for sounding impressive. This one is built around a harder constraint: every claim in the output must be independently verified against the candidate's real resume before it's shown to them. Nothing is invented — if a claim can't be traced back to a real fact, it's rejected or flagged as a gap, never fabricated.

Live demo: https://huggingface.co/spaces/ashmal-mustafa-2323/truth-checked-resume-tailor

## The Problem

AI resume tools routinely invent things: fabricated team sizes, made-up metrics, exaggerated ownership of projects. This isn't hypothetical — it can cost someone a job offer if caught in an interview, or their job entirely if a fabricated claim becomes part of an official record.

Separately, most tools also don't tell candidates what's actually missing from their resume for a specific role, or how to interpret an ATS score honestly.

## The Solution

Give the system a resume and a job posting. It returns:

1. A tailored resume PDF, using only verified real facts
2. A red-flag report of genuine gaps, ranked by severity, with honest suggestions
3. An ATS score, a deterministic and explainable simulation, not a guarantee
4. Interview prep questions, generated only for claims that survived verification

## Architecture

Resume text goes into a facts extraction step, which produces a structured Facts Ledger. Those facts are embedded into a vector database for semantic search. Separately, the job posting goes through a requirements extraction step. A router compares job requirements against the facts using a calibrated similarity threshold, splitting them into matched requirements and gaps.

Matched requirements go to a generation step that writes resume bullets using only the retrieved facts. Every generated bullet is then sent to a separate verification step, an independent LLM call with a skeptical prompt plus a deterministic backup check, which either approves or rejects it. Only approved bullets reach the final PDF and the interview prep generator. Gaps go to the red-flag report.

Generation and verification are deliberately two separate LLM calls, not one, so the model is never grading its own homework.

## Real Results

Evaluated across a LangSmith test suite of 6 resume and job posting pairs, including strong matches, weak matches, and deliberately mismatched pairs:

- Fabrication rate: 0.00 average across all 6 evaluated pairs
- Requirement coverage: 1.00 average
- Pipeline latency: 39 to 260 seconds depending on complexity

This was scaled down from an originally planned 40 to 50 test cases due to free tier LLM token limits.

The verification chain was calibrated across real failure cases during development: an early version over-rejected valid resume phrasing at a 58 percent false-fabrication rate, a second version let hedging language slip through at 33 percent, and the final calibrated version reached 0 to 8 percent depending on match quality, with every rejection traceable to a specific, inspectable reason.

## Tech Stack

LangChain, LangSmith, Groq (llama-3.3-70b-versatile), Chroma, Hugging Face sentence-transformers for free local embeddings, Gradio for the web interface, Hugging Face Spaces for deployment, and GitHub Actions for CI.

## Honest Limitations

- The ATS score is a best-effort simulation, not a guarantee. There is no universal ATS standard.
- The semantic-match threshold used by the router was empirically calibrated using real data from testing, not theoretically derived. It deliberately favors missing a real match over fabricating one, which means some genuine skills can be conservatively classified as gaps.
- Fabrication rate can vary slightly between runs on identical inputs due to LLM non-determinism, even after lowering generation temperature to reduce this.
- The evaluation suite was scaled down from 40 to 50 cases to 6 curated cases due to free tier daily token limits.
- PDF output is intentionally simple. Verification quality was prioritized over PDF styling.

## Running Locally

Clone the repository, create a virtual environment, install requirements.txt, add your own GROQ_API_KEY and LANGCHAIN_API_KEY to a .env file, then run app.py.

## Project Structure

The src folder contains schemas (data models), chains (the LangChain pipeline steps), evaluation (the LangSmith test suite), and pipeline.py (which ties everything together). app.py is the Gradio web interface. tests contains automated tests, and .github/workflows contains the CI configuration.