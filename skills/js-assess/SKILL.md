---
name: js-assess
description: >
  Career assessment interview for the Job Search & Resume Assistant. Use when
  the user says "assess my career", "career assessment", "what else could I do",
  "help me figure out my direction", or asks for adjacent career paths. Runs a
  10-15 minute conversational assessment and writes config/career-profile.yaml
  plus an adjacent-paths report. Optional — every other skill works without it.
---

# Career Assessment

Produces the optional `config/career-profile.yaml` — it widens sourcing
(adjacent titles feed the search planner automatically), sharpens Career
Trajectory scoring, and gives tailoring honest strengths language. Interview
script: `references/assessment-questions.md`. Schema + fixed enums:
`references/career-profile-schema.md`.

## Steps
1. **Ensure the workspace exists** and learn its paths:
   ```bash
   python scripts/workspace.py ensure
   python scripts/workspace.py paths     # note career_profile and reports_dir
   ```
2. **Check for an existing real profile** at the `career_profile` path (real =
   exists and contains no `<!-- PLACEHOLDER` marker).
   - **Exists → re-assessment mode:** read it, run an abbreviated interview
     focused on what changed since `assessed`, then present a field-level diff
     (old → new) and get explicit approval before writing. Append today's date
     to `history` — never drop prior dates. If `risk.notes` holds hard constraints
     (travel, relocation, commute), propose moving them to `profile.yaml`'s `travel`
     block one line at a time, and write only what the user approves.
   - **Absent/placeholder → full interview.**
3. **Run the six rounds** from `references/assessment-questions.md`, one
   question at a time. Synthesize attributes from the user's stories — never
   ask them to self-label with a score or enum. If a real master resume exists
   (`config/resume.md`, not a placeholder), pre-seed Round 4 from it and
   confirm rather than re-collect.
4. **Present the draft profile** conversationally (strengths, work style,
   motivator ranking, adjacent titles, trajectory) and get approval.
   **Nothing is written before approval** — an abandoned interview must leave
   no partial file on disk.
5. **Write the profile** to the `career_profile` path, matching
   `references/career-profile-schema.md` exactly (quoted dates, fixed enums,
   maps — not lists of maps). Write `energizers` and `drains` (round 1), `weaknesses`
   (round 5), and `interests` (round 6) when the user gave them, in the user's words.
   `drains` and `weaknesses` are PRIVATE.
6. **Validate (blocking):**
   ```bash
   python scripts/career_profile_qa.py
   ```
   - **Exit 1** → fix the flagged fields, rewrite, re-run. Do not declare the
     assessment done until exit 0.
   - **Exit 2** → the file isn't where expected; re-check the path from step 1.
7. **Write the adjacent-paths report** to
   `<reports_dir>/adjacent-paths-<YYYY-MM-DD>.md`: 3–5 non-obvious career
   directions. For each: why it fits (grounded in the user's own interview
   answers), 2–3 concrete example job titles, and what would have to be true to
   pursue it. Honest, not flattering — a direction with a real gap names the gap.
8. **Confirm and hand off:** where both files are; that `js-find-jobs` now
   automatically includes the adjacent titles in sourcing; and offer to
   re-evaluate borderline (C-grade) jobs with `js-evaluate`, since trajectory
   scoring now has signals.

## Rules
- The career profile informs **framing and search only**. It is NEVER a source
  of resume facts — `config/resume.md` stays the only source of truth, and the
  resume QA gate still enforces that on every tailored resume.
- Don't invent preferences. Synthesize from answers, confirm before writing.
- Write only to workspace paths from `workspace.py paths`. Never touch the
  engine, never hardcode a path.
