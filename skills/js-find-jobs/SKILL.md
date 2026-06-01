---
name: js-find-jobs
description: >
  Find job postings for the Job Search & Resume Assistant using web search. Use
  when the user says "find jobs", "search for jobs", "find new postings", or
  pastes a job URL/description. Discovers roles matching the user's profile,
  dedupes them, and writes job files into the workspace for evaluation.
---

# Find Jobs (web search)

Sources jobs with the WebSearch + WebFetch tools — no scraping, no Playwright.
Manual paste of a URL or JD text is a first-class path and the most reliable.

## Steps
1. **Read the profile** (resolve path via `python scripts/workspace.py paths`):
   use `search_keywords`, `location`, `work_model`, `salary`.
2. **Manual path (preferred when the user has a specific posting):** if the user
   pastes a URL, WebFetch it; if they paste JD text, use it directly. Skip to step 5.
3. **Search:** for the top 5–8 `search_keywords`, run WebSearch combining the title
   with location/remote intent. Prefer ATS-hosted boards that WebFetch reads well:
   `site:boards.greenhouse.io`, `site:jobs.lever.co`, `site:jobs.ashbyhq.com`, plus
   general queries. Collect candidate posting URLs.
4. **Dedupe** candidates against existing files in the workspace `jobs_dir`
   (by company+role slug) and within the current batch.
5. **WebFetch each surviving URL.** Ask the fetch to return the structured fields
   (company, role, location, salary if listed, work model) **AND the complete job
   description text VERBATIM — every responsibility, requirement, qualification, and
   section, not a summary.** If a page is blocked or JS-only (common for LinkedIn/
   Indeed) and the JD comes back thin or summarized, keep what you have and mark it
   `JD incomplete — paste full text to improve scoring` (and offer to take a pasted JD).
6. **Coarse pre-filter** using the profile: title fuzzy-match, location/remote fit,
   salary floor (missing salary is OK — it's handled during scoring).
7. **Present a numbered list of the passing jobs and get the user's approval
   BEFORE writing any files.** Let them drop any they don't want.
8. **For each approved job**, write a file to `jobs_dir` named
   `<company-slug>-<role-slug>-<YYYY-MM-DD>.md` using `references/job-file-template.md`.
   Fill Metadata, and paste the **COMPLETE job description text, verbatim**, into the
   `## Full Job Description` section — every responsibility, requirement, and section
   exactly as fetched or pasted. **Never summarize or truncate the JD** (evaluation and
   tailoring depend on the full text). Then add a pipeline row:
   ```bash
   python scripts/pipeline.py add "<Company>" "<Role>" "<relative/path/to/job.md>"
   ```
9. Tell the user how many were added and suggest running **js-evaluate**.

## Limits to surface honestly
- Search returns aggregator/expired links and some boards block WebFetch — coverage
  is best-effort, not exhaustive. Say so; don't imply you searched everywhere.
- Cap searches per run to keep it fast and cheap; mention if you capped.
