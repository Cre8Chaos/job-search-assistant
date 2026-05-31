---
name: js-pipeline
description: >
  Show and manage the application tracking pipeline for the Job Search & Resume
  Assistant. Use when the user says "show my pipeline", "job status", "what have I
  applied to", "mark applied", or "skip this job". Displays the tracking table and
  updates statuses.
---

# Pipeline / Application Tracking

Displays and manages the workspace `data/pipeline.md` tracking table. Format and
commands are in `references/pipeline-template.md`.

## Usage
- Show all (sorted by grade), or filter by status/grade on request.

## Steps
1. **Read the pipeline** (path via `python scripts/workspace.py paths`). Parse rows,
   skipping the header.
2. **Display** sorted A→B→C→D→F, newest first within a grade. Show a header with
   totals by grade, then group rows by grade, then a SKIPPED group. Include the job
   file path for each row.
3. **Resume queue:** after the table, list any A/B jobs with status `Evaluated`
   (not yet tailored/skipped) and ask once whether to tailor all of them or skip some.
   For any the user skips:
   ```bash
   python scripts/pipeline.py update "<Company>" "<Role>" --status Skip
   ```
   Then point them at `js-tailor` for the rest.
4. **Inline commands** (only when the user explicitly types them after the table):
   - `skip [N]` → set row N's status to `Skip`.
   - `apply [N]` → ask for the application date (default today), then:
     ```bash
     python scripts/pipeline.py update "<Company>" "<Role>" --status Applied --date <YYYY-MM-DD>
     ```

## Rules
- Read/write only through the resolved workspace pipeline path.
- Status flow: New → Evaluated → Tailored → Ready → Applied (or Skip).
