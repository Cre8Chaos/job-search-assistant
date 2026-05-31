"""
jobfile.py — shared helpers for reading the structured per-job markdown files.

A job file mixes the job's own '## ' sections (Metadata, Job Description,
Evaluation, Cover Letter, Notes) with a Tailored Resume that ALSO uses '## '
headers (Summary, Skills, Experience...). To extract the resume unambiguously,
the tailoring skill wraps it in explicit markers:

    ## Tailored Resume
    <!-- RESUME:START -->
    # Full Name
    ...
    <!-- RESUME:END -->

These helpers are stdlib-only so every script can import them freely.
"""
import re
from pathlib import Path

RESUME_START = "<!-- RESUME:START -->"
RESUME_END = "<!-- RESUME:END -->"

# Job-file '## ' sections that are siblings of the resume (used as fallback
# boundaries when the START/END markers are absent in an older file).
SIBLING_SECTIONS = (
    "Cover Letter", "Notes", "Full Job Description", "Job Description",
    "Evaluation", "Interview Prep", "Application Status",
)


def read(job_file: str) -> str:
    return Path(job_file).read_text(encoding="utf-8")


def section(content: str, header: str) -> str | None:
    """Return the body of a top-level '## <header>' section, or None."""
    pattern = rf"## {re.escape(header)}\n(.*?)(?=\n## |\Z)"
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1).strip() if m else None


def tailored_resume(content: str) -> str | None:
    """Extract the tailored resume body (markers preferred, heading as fallback)."""
    if RESUME_START in content and RESUME_END in content:
        body = content.split(RESUME_START, 1)[1].split(RESUME_END, 1)[0].strip()
        return body or None

    # Fallback: from '## Tailored Resume' up to the next sibling section.
    m = re.search(r"## Tailored Resume\n(.*)", content, re.DOTALL)
    if not m:
        return None
    body = m.group(1)
    boundary = re.search(rf"\n## (?:{'|'.join(re.escape(s) for s in SIBLING_SECTIONS)})\b", body)
    if boundary:
        body = body[: boundary.start()]
    # Trim leading metadata lines down to the first '# ' (name) heading.
    name = re.search(r"^# ", body, re.MULTILINE)
    if name:
        body = body[name.start():]
    return body.strip() or None


def top5_missing_keywords(content: str) -> list[str]:
    """Pull the Top 5 Missing Keywords list out of the Evaluation section."""
    m = re.search(r"Top 5 Missing Keywords[^\n:]*:\**\s*(.+)", content)
    if not m:
        return []
    tail = m.group(1).replace("*", "")
    # Could be a comma list on one line, or a numbered list across lines.
    inline = [k.strip(" .`") for k in tail.split(",") if k.strip(" .`")]
    if len(inline) >= 2:
        return inline[:5]
    numbered = re.findall(r"^\s*\d+\.\s*(.+)$",
                          content[m.start():], re.MULTILINE)
    return [k.strip(" .`*") for k in numbered[:5]] if numbered else inline
