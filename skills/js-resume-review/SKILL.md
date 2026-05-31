---
name: js-resume-review
description: >
  Import and review the user's master resume for the Job Search & Resume
  Assistant. Use when the user says "review my resume", "import my resume",
  "check my resume", or pastes/points to a resume. Saves it as the immutable
  source-of-truth (config/resume.md) and produces a scored health report.
---

# Master Resume Review

Imports the user's master resume into the workspace and reviews it. This file
becomes the **immutable source of truth** — every tailored resume is later checked
against it for fabrication. Other skills only READ it.

## Steps
1. **Locate the resume path:**
   ```bash
   python scripts/workspace.py paths      # use the "resume" path
   ```
2. **Ingest the resume** by whichever the user provides:
   - **Paste:** write the pasted text to the resume path.
   - **File path (.md/.txt):** read it and write to the resume path.
   - **File path (.pdf):**
     ```bash
     python scripts/extract_resume.py "/path/to/resume.pdf"
     ```
     Review/clean the extracted text into well-formed markdown, then write it to
     the resume path. If pdfplumber isn't installed (exit 3), ask the user to paste
     the text instead.
   - **No resume yet:** offer a guided skeleton (contact, Summary, Skills,
     Experience with bullets, Education, Certifications) and fill it in with them.
   - Format it with standard headers: `# Name`, a contact line, `## Summary`,
     `## Skills`, `## Experience` (with `### Title` + `Company | Dates` + `- ` bullets),
     `## Education`, `## Certifications`.
3. **Run the health check:**
   ```bash
   python scripts/resume_qa.py --mode master
   ```
   This reports: core sections present, % of bullets that are quantified, ATS-safety
   of the source, length sanity, contact line present. (`--mode master` is advisory —
   it never blocks; exit 0 unless the resume file is missing.)
4. **Summarize the report** to the user and offer a short, prioritized punch-list of
   improvements (e.g., "7 of 9 bullets aren't quantified — add a metric where one
   truly exists"). Only apply edits the user approves, and never invent facts.
5. If this was part of first-run setup, tell the user they're ready and point them at
   the menu (find jobs → evaluate → tailor).

## Rules
- `config/resume.md` is the source of truth. Keep it truthful and complete; do not
  pad it with skills/metrics the user doesn't actually have.
- Write only to the resolved workspace resume path.
