"""One-time utility: extracts plain text from PDF resumes so we have
clean .txt files to feed into the extraction chain. Includes cleanup
for common encoding artifacts from PDF text extraction."""

from pypdf import PdfReader
from pathlib import Path

# Common mis-encoded character sequences -> their correct characters.
# These show up when certain PDF fonts encode special punctuation
# in a way that doesn't map cleanly to UTF-8 during extraction.
ENCODING_FIXES = {
    "Â·": "·",
    "â€”": "—",
    "â€“": "–",
    "â€™": "'",
    "â€œ": '"',
    "â€\x9d": '"',
}

def clean_text(text: str) -> str:
    for broken, fixed in ENCODING_FIXES.items():
        text = text.replace(broken, fixed)
    return text

def pdf_to_text(pdf_path: str, output_path: str) -> None:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    text = clean_text(text)
    Path(output_path).write_text(text.strip(), encoding="utf-8")
    print(f"✅ Extracted text from {pdf_path} -> {output_path}")

if __name__ == "__main__":
    pdf_to_text("src/data/resumes/pdfs/resume_1.pdf", "src/data/resumes/resume_1.txt")
    pdf_to_text("src/data/resumes/pdfs/resume_2.pdf", "src/data/resumes/resume_2.txt")
    pdf_to_text("src/data/resumes/pdfs/resume_3.pdf", "src/data/resumes/resume_3.txt")