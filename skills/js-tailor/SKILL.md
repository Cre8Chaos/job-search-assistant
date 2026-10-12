---
name: js-tailor
description: >
  Tailor the master resume to a specific job and draft a cover letter for the Job
  Search & Resume Assistant. Use when the user says "tailor my resume", "customize
  my resume for this job", "write a cover letter", or "prep me to apply". Runs the
  resume QA gate and optionally renders an ATS PDF. Only for A/B grade jobs.
---

# Tailor Resume + Cover Letter (apply prep)

Tailors `config/resume.md` to a specific job, drafts a cover letter, validates the
result with the QA gate, and optionally renders an ATS PDF. Follow
`references/ats-rules.md` (tailoring) and `references/cover-letter-rules.md`.

## Steps
0. **Grade gate:** read the job file's `## Evaluation`. If grade is C/D/F or a
   Domain-Expertise Mismatch, STOP and tell the user the grade — do not tailor.
1. **Read inputs** (paths via `python scripts/workspace.py paths`): full
   `config/resume.md`; the job file's `## Full Job Description` and `## Evaluation`
   (including its Top 5 Missing Keywords and Key Requirements). Skip the **Fit notes**
   block and the **Interview Prep** pack inside `## Evaluation`: they hold PRIVATE
   career-profile text and are not tailoring inputs.
2. **Tailor the resume** per `references/ats-rules.md`: extract 15–20 ATS keywords,
   reuse the Top 5 Missing Keywords, apply the X-Y-Z formula to bullets using only
   facts/metrics already in the master, reorder for relevance, address director-written
   Key Requirements, and address any Timezone/Travel note in the summary. No fabrication.
   If the workspace has a real `config/career-profile.yaml`, you may draw
   phrasing from its strengths evidence for the summary and cover-letter voice —
   **framing only, never new facts**: every employer, date, metric, and claim
   must still trace to the master resume (the QA gate enforces this).
   It may also use `transferable_skills` and `energizers` from the career profile for
   framing in the summary and cover letter: framing only, never a new fact, the same
   rule as `strengths`. Never read `drains`, `weaknesses`, or `interests`.
   `resume_qa.py` fails any resume or cover letter that contains them.
3. **Write the tailored resume** into the job file under `## Tailored Resume`, wrapped
   in the `<!-- RESUME:START -->` / `<!-- RESUME:END -->` markers (required so the QA
   gate and PDF renderer can extract it). Structure per `references/job-file-template.md`.
4. **Run the QA gate (blocking):**
   ```bash
   python scripts/resume_qa.py --mode tailored --job "<job_file>"
   ```
   - **Exit 1** → fix the flagged items (Layer 1 fabrication and Layer 2 ATS are
     blocking; a Layer 1 failure means a claim doesn't trace to the master — correct it),
     then re-run. **Do not proceed to PDF or mark Ready until exit 0.**
   - **Exit 0** → proceed.
5. **Draft the cover letter** per `references/cover-letter-rules.md` and write it to
   the job file's `## Cover Letter`. Self-check every claim against the master resume.
   Anchor the "why this company" hook in a **verified fact from the Company Snapshot**
   (a recent move, the ownership structure, a strategic shift) — never a company fact
   stated from memory.
6. **Optional ATS PDF** (only after QA passes):
   ```bash
   python scripts/render_pdf.py "<job_file>"
   ```
   This needs **Playwright**. If it isn't installed the script degrades gracefully
   (prints where the markdown is and exits 0). The first time a user wants a PDF,
   recommend they install it once so future exports work:
   ```bash
   pip install playwright && playwright install chromium
   ```
7. **Update status:**
   ```bash
   python scripts/pipeline.py update "<Company>" "<Role>" --status Tailored
   ```
   (Use `Ready` once a PDF exists and the user has reviewed it.)
8. **Confirm** to the user: what was tailored, QA result, where the files are, and that
   they should review before applying manually. Point them to the **Interview Prep**
   pack in the job file's `## Evaluation` and ask which interview stage is coming up so
   it can be weighted.

## Rules
- **Never auto-apply.** Output materials for the user to submit themselves.
- The QA gate is mandatory before PDF/Ready. Honest keyword gaps (Layer 4 warnings)
  are allowed and surfaced, not blocked.
