# Job Search & Resume Assistant — Engine

A reusable, multi-user-ready job search assistant. It interviews the user about
their next role, reviews their master resume, finds and qualifies jobs, and tailors
a resume + cover letter per job — never auto-applying, never fabricating.

## Architecture: ENGINE vs WORKSPACE (read this first)
- **Engine** = this project (`skills/`, `references/`, `scripts/`). It contains
  **zero personal data**. Run engine scripts with paths relative to this project root.
- **Workspace** = the user's private data (profile, master resume, job files,
  pipeline, PDFs). Its location is resolved by `scripts/workspace.py`, defaulting to
  `~/Projects/job-search`, overridable via the `JOB_SEARCH_WORKSPACE` env var (the
  seam a future hosted/multi-user service uses to scope per-user data).

  ```bash
  python scripts/workspace.py ensure     # create the workspace from the template if missing
  python scripts/workspace.py paths      # JSON: profile / resume / pipeline / jobs_dir / pdf_dir
  python scripts/workspace.py validate   # exit 0 = ready, 1 = setup still needed
  ```
  **Always read/write user files at the paths from `workspace.py` — never hardcode one.**

## Skills (in `skills/`)
| Skill | When |
|---|---|
| `job-search` | Umbrella router / entry point. Start here. |
| `js-setup` | First-run intake interview → writes `config/profile.yaml`. |
| `js-resume-review` | Import + health-check the master resume. |
| `js-find-jobs` | Web-search sourcing → job files in the workspace. |
| `js-evaluate` | Config-driven A–F scoring of jobs. |
| `js-tailor` | Tailor resume + cover letter, QA gate, optional ATS PDF. |
| `js-pipeline` | Application tracking. |

## Scripts (in `scripts/`, stdlib-first)
| Script | Purpose |
|---|---|
| `workspace.py` | The engine↔workspace seam (resolve/ensure/paths/validate). |
| `pipeline.py` | Add/update rows in the workspace pipeline. |
| `resume_qa.py` | Zero-dependency resume QA gate (fabrication/ATS/structure/keywords). |
| `extract_resume.py` | Extract text from a resume PDF (pdfplumber optional). |
| `render_pdf.py` | ATS-safe PDF render (Playwright optional; degrades gracefully). |
| `jobfile.py` | Shared job-file section extractors. |
| `selftest.py` | Deterministic self-tests for the engine. |

## References (in `references/`)
Shared rubrics/schemas: `scoring-rubric.md`, `profile-schema.md`, `ats-rules.md`,
`cover-letter-rules.md`, `intake-questions.md`, `job-file-template.md`,
`pipeline-template.md`.

## Hard rules
- **Never auto-submit an application.** Prepare materials; the user applies manually.
- **Never fabricate** experience, skills, metrics, or credentials. `config/resume.md`
  is the immutable source of truth; the QA gate enforces this on tailored resumes.
- All personal data lives in the workspace, never in this engine.

## Typical flow
`job-search` → (first run: `js-setup` → `js-resume-review`) → `js-find-jobs` →
`js-evaluate` → `js-tailor` (A/B jobs) → `js-pipeline`.
