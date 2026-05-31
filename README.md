# Job Search & Resume Assistant

A reusable, AI-powered job-search assistant you run inside Claude Code. It
interviews you about what you want in your next role, reviews your master resume,
finds and qualifies jobs, and tailors a resume + cover letter per job — and it
**never auto-applies and never fabricates** anything.

It is built so the same logic can later power a hosted, multi-user service: the
**engine** (this repo) holds zero personal data, and every per-user file lives in a
separate **workspace** resolved through one seam (`scripts/workspace.py`).

## What it does (v1)
1. **Intake interview** — understand what matters to you and confirm your target titles.
2. **Master resume review** — import your resume and health-check it.
3. **Find jobs** — web-search postings matching your profile (no scraping).
4. **Qualify jobs** — score each A–F against your weighted profile.
5. **Tailor + apply prep** — tailor your resume to a job, draft a cover letter, run a
   resume QA gate (blocks fabrication / ATS problems), and optionally render an ATS PDF.
6. **Track** — a local markdown application pipeline.

## Quick start
1. Open this project in Claude Code.
2. Say **"help me find a job"** (or run the `job-search` skill). On first run it will:
   - create your workspace (default `~/Projects/job-search`),
   - walk you through the ~3-minute intake interview,
   - import and review your master resume.
3. Then: **find jobs → evaluate → tailor** the A/B ones → **status** to track.

## Engine vs. workspace
- **Engine** = `skills/`, `references/`, `scripts/` here. No personal data.
- **Workspace** = your data: `config/profile.yaml`, `config/resume.md`,
  `data/jobs/*.md`, `data/pipeline.md`, `output/pdfs/`.
  - Default location: `~/Projects/job-search`.
  - Override with the `JOB_SEARCH_WORKSPACE` env var, or a one-line path in
    `~/.config/job-search/workspace`.

```bash
python scripts/workspace.py paths      # show where your files live
python scripts/selftest.py             # verify the engine (no network needed)
```

## Optional dependencies
The core is pure Python stdlib. Two features are optional and degrade gracefully:
- **PDF rendering** (`render_pdf.py`) needs Playwright: `pip install playwright && playwright install chromium`. Without it, your tailored resume markdown is still produced.
- **PDF resume import** (`extract_resume.py`) needs `pip install pdfplumber`. Without it, paste your resume text instead.

## Safety
- Never submits applications for you — it prepares materials you submit yourself.
- `config/resume.md` is your immutable source of truth; `resume_qa.py` blocks any
  tailored resume that introduces an employer, title, date, credential, or metric
  that doesn't trace back to it.

## Note on job-board use
Job sourcing uses general web search/fetch. You are responsible for using target
sites in line with their terms of service.

## Roadmap (not in v1)
- Dedicated interview-prep skill (beyond the Q&A already in evaluations).
- Per-job application checklist + richer status tracking.
- Optional Notion / Google Sheets pipeline export.
- Hosted multi-user service via the Claude Agent SDK (the `workspace.py` seam is the
  hook: set `JOB_SEARCH_WORKSPACE` per request, or swap file I/O for a per-user store).
