---
name: js-find-jobs
description: >
  Find job postings for the Job Search & Resume Assistant using web search. Use
  when the user says "find jobs", "search for jobs", "find new postings", or
  pastes a job URL/description. Discovers roles matching the user's profile,
  dedupes them, and writes job files into the workspace for evaluation.
---

# Find Jobs (web search)

Sources jobs with the WebSearch + WebFetch tools — **no scraping, no Playwright**.
A deterministic query plan (`scripts/search_planner.py`) drives coverage so it is
consistent run-to-run instead of improvised. Manual paste of a URL or JD text is a
first-class path and the most reliable.

## Steps

1. **Read the profile** (resolve path via `python scripts/workspace.py paths`):
   note `search_keywords`, `location`, `work_model`, `salary`, and
   `work_authorization` (whether `needs_sponsorship` is true — it adjusts steps 3
   and 6; when false/absent, sourcing is unchanged).
   Also check for a career profile (`career_profile` path): when one exists, the
   query plan below automatically includes its `adjacent_titles`.

2. **Manual path (preferred when the user has a specific posting):** if the user
   pastes a URL, WebFetch it; if they paste JD text, use it directly. Skip to step 5.

3. **Build the query plan, then search.** Generate the deterministic query set:
   ```bash
   python scripts/search_planner.py --json        # or --profile <path> for a test workspace
   ```
   Each query is tagged with `board` (greenhouse / lever / ashby / workday / builtin /
   general), `keyword`, and `kind` (remote / location). These ATS boards are chosen
   because WebFetch reads them reliably; LinkedIn/Indeed are deliberately excluded (JS-
   walled and ToS-sensitive — that reach lives in the separate personal scraper tool,
   not this product).
   - Run WebSearch for a **breadth-first slice**: take the first query for **each board
     across the top 3–4 keywords** before going deep on any single keyword, so coverage
     is spread rather than exhausting one title. Cap at **~15–20 searches per run** to
     stay fast and cheap.
   - The planner already encodes sponsorship intent (`needs_sponsorship: true` appends
     `visa sponsorship` to queries and you should favor larger/established employers).
     This is best-effort bias, not a guarantee — verify each posting in step 6.
   - The planner also appends `adjacent_titles` from `config/career-profile.yaml`
     when a real one exists (run the `js-assess` skill to create it). They fill
     remaining keyword budget — the ~15–20 searches/run cap is unchanged. A
     `warning:` line on stderr means the career profile was unreadable and was
     skipped; surface that to the user once, then proceed normally.
   - Collect candidate posting URLs from the results.

4. **Dedupe** candidates against existing files in the workspace `jobs_dir`
   (by company+role slug) and within the current batch, before any WebFetch.

5. **WebFetch each surviving URL.** Ask the fetch to return the structured fields
   (company, role, location, salary if listed, work model) **AND the complete job
   description text VERBATIM — every responsibility, requirement, qualification, and
   section, not a summary.** If a page is blocked or JS-only and the JD comes back thin
   or summarized, keep what you have and mark it
   `JD incomplete — paste full text to improve scoring` (and offer to take a pasted JD).

6. **Coarse pre-filter** using the profile: title fuzzy-match, location/remote fit,
   salary floor (missing salary is OK — handled during scoring).
   - **If `needs_sponsorship` is true:** scan each JD for explicit refusal language
     ("no visa sponsorship", "must be authorized without sponsorship", "US citizens/GC
     holders only"). Drop those, or keep them clearly flagged `sponsorship: refused`.
     Label every surfaced job with its sponsorship stance (`offered` / `not stated` /
     `refused`). Stance is best-effort from JD text — say so.

7. **Present a numbered list of the passing jobs and get the user's approval
   BEFORE writing any files.** Let them drop any they don't want. When sponsorship
   matters, show each job's sponsorship stance in the list.

8. **For each approved job**, write a file to `jobs_dir` named
   `<company-slug>-<role-slug>-<YYYY-MM-DD>.md` using `references/job-file-template.md`.
   Fill Metadata (set the `sponsorship` field — `offered`/`not-stated`/`refused` — when
   `needs_sponsorship` is true; leave blank otherwise), and paste the **COMPLETE job
   description text, verbatim**, into the `## Full Job Description` section — every
   responsibility, requirement, and section exactly as fetched or pasted. **Never
   summarize or truncate the JD** (evaluation and tailoring depend on the full text).
   Then add a pipeline row:
   ```bash
   python scripts/pipeline.py add "<Company>" "<Role>" "<relative/path/to/job.md>"
   ```

9. Tell the user how many were added and suggest running **js-evaluate**.

## Coverage honesty (always surface)

- Report how many of the planned queries you actually ran and which boards you covered
  vs. capped. Don't imply you searched everywhere.
- Web search returns aggregator/expired links and some boards block WebFetch — coverage
  is best-effort. If you hit the per-run cap, say so and offer to run another slice
  (the plan is deterministic, so the next slice picks up where this one left off).
