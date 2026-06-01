---
name: job-search
description: >
  Umbrella entry point for the Job Search & Resume Assistant. Use when the user
  says "help me find a job", "job search", "start my job hunt", or runs
  /job-search. Checks whether the user is set up, runs first-time setup if not,
  and routes to the right step: setup interview, resume review, find jobs,
  evaluate/qualify jobs, tailor resume + cover letter, or track applications.
---

# Job Search & Resume Assistant — Router

This is the front door. It figures out where the user is and dispatches to the
focused skills. **No personal data lives in this engine.** All per-user files
(profile, resume, pipeline, job files) live in a separate workspace resolved by
`scripts/workspace.py`.

## Engine vs workspace
- **Engine** = this project (`scripts/`, `references/`, the `js-*` skills). Run
  engine scripts with paths relative to this project root.
- **Workspace** = the user's data. Discover its paths by running:
  ```bash
  python scripts/workspace.py paths      # JSON of profile/resume/pipeline/jobs/pdf paths
  ```
  Always read and write user files at those resolved paths — never hardcode a path.

## Steps
1. **Check setup state:**
   ```bash
   python scripts/workspace.py ensure     # create workspace from template if missing
   python scripts/workspace.py validate   # exit 0 = ready, exit 1 = setup needed
   ```
2. **If validate fails (first run):** tell the user "Looks like this is your first
   run — let's get you set up (about 3 minutes)." Then invoke the **js-setup** skill
   (intake interview), and when it finishes, chain into **js-resume-review**.
3. **If validate passes:** print the menu below and route based on the user's intent.

## Menu (when set up)
```
Job Search & Resume Assistant — ready. Workspace: <root>

What would you like to do?
  • find jobs      — search the web for roles matching your profile   (js-find-jobs)
  • evaluate       — score/qualify found jobs A–F                      (js-evaluate)
  • tailor <file>  — tailor your resume + draft a cover letter         (js-tailor)
  • status         — show your application pipeline                    (js-pipeline)
  • review resume  — re-review or update your master resume            (js-resume-review)
  • setup          — redo the intake interview                         (js-setup)
```

## Routing table
| User intent | Skill |
|---|---|
| set up / redo interview / change targets | `js-setup` |
| review / update / import master resume | `js-resume-review` |
| find / search for jobs | `js-find-jobs` |
| evaluate / score / qualify jobs | `js-evaluate` |
| tailor resume / write cover letter / prep to apply | `js-tailor` |
| show pipeline / mark applied / status | `js-pipeline` |

## Hard rules (apply across all sub-skills)
- **Never auto-submit an application.** Prepare materials; the user applies manually.
- **Never fabricate** experience, skills, metrics, or credentials. The master
  resume (`config/resume.md`) is the source of truth.
- Always locate user files through `scripts/workspace.py`.

## Recommended setup (one time)
The core runs on Python 3 alone. Two features need extra packages and degrade
gracefully if missing — but for the best experience, recommend installing them:
- **ATS PDF export** needs **Playwright**: `pip install playwright && playwright install chromium`.
  On a user's first run, check if it's installed; if not, surface this command so PDF
  export works. Without it, the tailored resume markdown is still produced.
- **Resume import from PDF** needs **pdfplumber** (`pip install pdfplumber`); otherwise
  the user can paste their resume text.
