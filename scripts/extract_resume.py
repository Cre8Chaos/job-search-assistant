"""
extract_resume.py — extract raw text from a resume PDF so it can be reviewed and
saved as the workspace master resume (config/resume.md).

The PDF path is a REQUIRED argument — there is no personal default. pdfplumber is
optional; if it is not installed, the script prints an actionable message and exits
non-zero so the calling skill can fall back to "paste the text instead."

Usage:
    python scripts/extract_resume.py /path/to/resume.pdf
"""
import sys
from pathlib import Path


def extract_text(pdf_path: str) -> str:
    try:
        import pdfplumber
    except ImportError:
        print(
            "pdfplumber is not installed, so this PDF cannot be parsed here.\n"
            "Either install it (pip install pdfplumber) or paste your resume text "
            "directly and the resume-review skill will save it.",
            file=sys.stderr,
        )
        sys.exit(3)

    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                lines.append(f"<!-- Page {i} -->\n{text}")
    return "\n\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    print(extract_text(pdf_path))


if __name__ == "__main__":
    main()
