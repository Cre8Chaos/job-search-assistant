---
name: js-evaluate
description: >
  Score and qualify jobs for the Job Search & Resume Assistant. Use when the user
  says "evaluate", "score these jobs", "qualify jobs", or runs evaluate on a job
  file or all new jobs. Applies the user's config-driven A–F rubric and writes the
  evaluation into each job file.
---

# Evaluate / Qualify Jobs

Scores one job or all "New" jobs against the user's profile using the rubric in
`references/scoring-rubric.md`. **All thresholds come from `config/profile.yaml`** —
read it first and fill the rubric tokens (weights, salary band, location, domains)
from the user's actual profile.

## Usage
- Evaluate one: point at a job file path.
- Evaluate all: process every job with status `New` in the pipeline.

## Autonomous execution
Run evaluations without pausing for confirmation. Apply the rubric mechanically:
- Borderline between grades → use the math, take the grade the score lands in.
- Missing salary → score from the verified comp benchmark (step 3.5); only if still
  unconfirmed, score salary as 6 (unknown, assume market).
- Company facts (size, ownership, funding) → confirm by web search first (step 3.5);
  only if still unconfirmed, stability 5–6 and label the fact "unverified".
- Any other uncertainty → make a call, note the reasoning in the table, keep going.

## Steps
1. **Read inputs** (paths via `python scripts/workspace.py paths`):
   `config/profile.yaml` (weights + thresholds) and `config/resume.md` (for the
   career-trajectory and domain-gate comparison). Read `references/scoring-rubric.md`.
   Also read `config/career-profile.yaml` if present (optional; a missing or
   placeholder file means Fit notes are skipped).
1.5. **Constraints Gate (runs first, before every other gate)** (only if `profile.yaml`
   has a `travel` block; otherwise record
   `**Constraints Gate:** dormant (no travel block in profile.yaml)`): per
   `references/scoring-rubric.md` → "Constraints Gate". A travel figure above
   `travel.max_pct`, a relocation requirement when `travel.relocation` is false, or an
   explicit onsite requirement outside the radius is a CONFLICT, quoting the exact JD
   line. No quote, no F. Silence or vague wording is `CHECK: ...` with no penalty.
   On a CONFLICT, write the F (Constraint Conflict) evaluation per the rubric, update
   the grade/status, and stop: skip the Domain-Expertise and Sponsorship gates and
   scoring. Otherwise record the `**Constraints Gate:**` line (PASS / CHECK / dormant)
   and include it in whatever Evaluation a later step writes, including the
   Domain-Expertise D note and the Sponsorship F note.
2. **Domain-Expertise Gate** (after the Constraints Gate): if the JD hard-requires
   expertise absent from the resume / listed in `domain.dealbreakers`, cap at D, skip
   the rubric, write the mismatch note (with the `**Constraints Gate:**` line), update
   the grade, and move on.
3. **Sponsorship Gate** (only if `work_authorization.needs_sponsorship` is true; skip
   otherwise): per `references/scoring-rubric.md`, if the JD explicitly refuses
   sponsorship, **cap at F**, write the "No Visa Sponsorship" note quoting the exact
   text (with the `**Constraints Gate:**` line), set `Sponsorship: refused`, update
   grade/status, and move on. If it explicitly offers sponsorship record `offered`;
   if silent record `not stated`, then continue.
3.5. **Company intelligence (live, verified):** before scoring Salary and Stability,
   run targeted web searches to confirm ownership/structure, funding/valuation,
   headcount, HQ, recent developments, culture, and a comp benchmark — per
   `references/scoring-rubric.md` → "Company Intelligence". Never state these from
   memory; label anything unconfirmed "unverified" and never invent a source. These
   verified facts drive the Salary Fit and Company Stability scores and populate the
   Company Snapshot in the output.
4. **Score the 6 dimensions** 0–10 each, weight from the profile, sum to a 0–100
   total → letter grade.
5. **Director-written bullet detection** → adjust grade if a rare/specific
   requirement doesn't match the background; record Key Requirements either way.
6. **Write the `## Evaluation` block** to the job file (score table, recommendation,
   the web-verified **Company Snapshot** with its "verified as of" date, Sponsorship
   line if applicable, Timezone/Travel, Top 5 Missing Keywords, Key Requirements,
   Grade Adjustment, and the full **Interview Prep** pack — recruiter screen, one-line
   positioning, hiring-manager technical Q&A, questions to ask, comp strategy,
   logistics, night-before checklist — grounded in the resume and the Company
   Snapshot). Also include the `**Constraints Gate:**` line, and the **Fit notes**
   block (Why it fits / Watch out, each line pairing a JD quote with a named
   career-profile field). Add each Watch-out question to Interview Prep's questions
   to ask. `drains` and `weaknesses` appear ONLY in Fit notes and Interview Prep.
   **Preserve the `## Full Job Description` section in full** — if the
   complete JD verbatim isn't already there, add it; never replace it with a summary.
7. **Update the pipeline grade/status:**
   ```bash
   python scripts/pipeline.py update "<Company>" "<Role>" --grade <A|B|C|D|F> --status Evaluated
   ```
8. **Batch summary** when evaluating all: print counts by grade and suggest
   tailoring the A/B jobs (`js-tailor`).

## Rules
- The Top 5 Missing Keywords you record drive the later resume tailoring — be precise.
- Only A/B jobs should proceed to tailoring; C/D/F stop here.
- When reporting a single evaluation to the user, lead with the verified
  ownership/structure and comp benchmark from the Company Snapshot (with the "verified
  as of" date so they know it's current), note that the Interview Prep pack is in the
  job file, and ask which interview stage is coming up so it can be weighted.
