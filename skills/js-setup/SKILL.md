---
name: js-setup
description: >
  First-run setup wizard and intake interview for the Job Search & Resume
  Assistant. Use when setting up job search for the first time, or when the user
  says "set up job search", "redo my intake", or "change my target roles". Asks
  what matters in the user's next role, confirms target job titles, and writes
  config/profile.yaml.
---

# Setup & Intake Interview

Produces the user's `config/profile.yaml` — the profile every other skill reads
for filtering and scoring. Follow the interview script in
`references/intake-questions.md`. Schema and a generic example are in
`references/profile-schema.md`.

## Steps
1. **Ensure the workspace exists** and learn its paths:
   ```bash
   python scripts/workspace.py ensure
   python scripts/workspace.py paths
   ```
2. **Run the six intake rounds** from `references/intake-questions.md`, in order:
   1. Target roles — propose normalized titles + search keywords, then
      **explicitly confirm the title list with the user before writing anything.**
   2. Location & work model, plus travel and relocation → `travel.max_pct` (an integer
      percentage, e.g. 25) and `travel.relocation` (true/false). If the user skips it,
      omit the `travel` block (the Constraints Gate stays dormant).
   3. Work authorization → `work_authorization.needs_sponsorship` (default false).
   4. Compensation.
   5. What matters most → 1–5 importance ratings → **normalize to scoring_weights
      that sum to exactly 100.**
   6. Domain preferences & dealbreakers.
   - Ask each round as ONE grouped message. Use AskUserQuestion for multiple-choice
     parts; plain prompts for open-ended parts.
3. **Write `config/profile.yaml`** at the resolved profile path, matching
   `references/profile-schema.md`. Double-check `scoring_weights` sums to 100, and
   include the `work_authorization` block (default `needs_sponsorship: false`)
   and the `travel` block when the user gave one.
4. **Confirm** a short summary of the saved profile to the user (include whether
   they need visa sponsorship, so the gate behavior is explicit).
5. **Hand off** to the `js-resume-review` skill to import and review their master
   resume (setup isn't complete until there's a real resume on file).

## Rules
- Do not invent the user's preferences — ask. The only thing you propose (and then
  confirm) is the normalized title/keyword list in Round 1.
- Write only to the workspace profile path from `workspace.py paths`. Never touch
  the engine or hardcode a path.
