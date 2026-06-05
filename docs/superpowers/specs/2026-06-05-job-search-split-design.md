# Job Search: Personal Tool vs. Shippable Product — Design

**Date:** 2026-06-05
**Status:** Approved

## Context

Two related codebases drifted apart:

- `job-search-agent/` — the original, high-volume personal tool. A Playwright scraper
  (`scan_jobs.py`) sweeps LinkedIn, Indeed, Glassdoor, Builtin, and ~19 hardcoded
  company ATS portals, then fetches full JDs. Produced 251 real job files. Last run
  2026-05-13.
- `job-search-assistant/` — a reusable, **zero-personal-data** engine intended to ship
  to other users. Sourcing is ToS-safe WebSearch/WebFetch only (no scraper). Cleaner,
  but thinner sourcing — which is why results felt worse.

## Decision

Keep them as **two distinct products**, not one:

1. **`job-search-agent` = personal tool.** Keeps the scraper. Never shipped to others.
2. **`job-search-assistant` = the product.** Stays web-search-only (a scraper cannot be
   shipped to third parties). The owner must be able to run and test it himself against a
   demo persona, with zero personal data involved.

## Workstreams

### A. Restore the personal scraper

- **Problem:** the agent's `.venv` lost its `playwright` package (`import playwright`
  fails); `scan_jobs.py` crashes on import. Chromium browsers are still cached.
- **Fix:** reinstall `requirements.txt` (`pdfplumber`, `playwright==1.44.0`, `pyyaml`)
  into `.venv`, then verify `scan_jobs.py` imports and runs a short dry pass.
- No logic or data changes. This remains the private, scraper-powered tool.

### B. Make the product testable with a demo persona

- Commit `examples/sample-workspace/` to the engine: a **fictional** candidate
  (`config/profile.yaml` + `config/resume.md`), empty `data/jobs/`, fresh
  `data/pipeline.md`. A fixture, not personal data — consistent with "zero personal data."
  Doubles as a demo other users can inspect.
- Add `scripts/run_test.sh`: copies the fixture to a scratch dir, points
  `JOB_SEARCH_WORKSPACE` at the copy, runs `selftest.py`, and leaves a clean state to
  drive find → evaluate → tailor. Copying keeps the committed fixture pristine.
- Owner's real data never touches the product.

### C. Improve product sourcing (ToS-safe, no scraper)

- Add `scripts/search_planner.py` — pure stdlib. Given the profile, emits the exact set
  of search queries (keyword × location/remote × ATS-board `site:` filters for
  greenhouse / lever / ashby / workday / builtin). Deterministic and unit-testable, so
  coverage no longer depends on improvisation.
- Rewrite `skills/js-find-jobs/SKILL.md` to consume that query list, broaden board
  coverage, tighten dedupe, and report coverage honestly.
- Add a `selftest.py` case for the planner.

This closes the gap as far as ToS-safe sourcing allows. It will not match the personal
scraper's LinkedIn reach — that is the deliberate line between the two products.

## Non-goals

- No scraper, Playwright, or headless browser sourcing in the product, ever.
- No changes to the personal agent's logic or data.
- No hosted/multi-user deployment work (the `workspace.py` seam already anticipates it).

## Verification

- `python scripts/selftest.py` passes in the product (incl. new planner test).
- `run_test.sh` resolves the scratch workspace and validates green.
- Old agent: `.venv/bin/python -c "import playwright"` succeeds and `scan_jobs.py`
  imports without error.
