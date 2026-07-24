# js-assess — Career Assessment Module (Design)

**Date:** 2026-07-23
**Status:** Approved design, pending implementation plan
**Origin:** Gap analysis against tryapt.ai (Apt). Apt's differentiator is a career
assessment front-end plus an ongoing mentor layer wrapped around a job board. Our
engine already beats its job board (rubric scoring, zero-fabrication QA, live company
verification) but has no assessment layer. This spec adds Phase 1 of the shared-engine
plan: the career assessment. Phase 2 (mentor skills: negotiation, insights) and
Phase 3 (web front-end / lead-magnet quiz) are explicitly out of scope here.

## Goal

A new engine skill, `js-assess`, that runs a ~10–15 minute conversational career
assessment and produces a structured, versioned career profile that widens sourcing,
sharpens scoring, and improves tailoring — with zero behavior change for users who
never run it.

## Non-Goals

- No psychometric/Likert scoring model. V1 is an LLM-led structured interview.
- No web UI, no auth, no hosting. The YAML file format is the seam a future
  Phase 3 web quiz would emit; the interview is not that seam.
- No changes to rubric weights, grade bands, or dealbreaker gates.
- No Daily Driver (`job-search-agent`) changes. Data separation between the two
  products remains absolute; Michael consumes this personally via
  `JOB_SEARCH_WORKSPACE=~/Projects/Cre8-Your-Life/job-search`.
- No auto-apply, no fabrication — both engine invariants unchanged.

## Architecture

Engine/workspace split is preserved: the skill, question guide, schema reference, and
validator live in the engine (zero personal data); the produced profile and report
live in the user's workspace.

### New engine components

| Component | Location | Purpose |
|---|---|---|
| `js-assess` skill | `skills/js-assess/SKILL.md` | Runs the interview, writes profile + report, proposes diffs on re-run |
| Question guide | `references/assessment-questions.md` | Interview structure: 6 sections, one question at a time, follow-up rules |
| Profile schema | `references/career-profile-schema.md` | Schema + annotated example of `career-profile.yaml` |
| Validator | `scripts/career_profile_qa.py` | Stdlib-only schema/consistency validation (same layered pattern as `resume_qa.py`) |
| Template placeholder | `workspace-template/config/career-profile.yaml` | Placeholder comment pointing at js-assess (same pattern as `profile.yaml`) |

### Workspace artifacts (per user)

- `config/career-profile.yaml` — the structured profile (see Data below).
- `output/reports/adjacent-paths-<date>.md` — the "careers you never considered"
  report: 3–5 non-obvious directions, each with rationale grounded in interview
  answers, concrete example job titles, and what would need to be true to pursue it.

## Interview design

Six sections, one question at a time (same conversational pattern as `js-setup`):

1. **Strengths & energizers** — what work produces energy vs. drains it; peak-work stories.
2. **Work-style** — autonomy vs. structure, depth vs. breadth, collaboration mode.
3. **Motivators & values** — money/mission/mastery/status trade-offs, ranked.
4. **Transferable skills inventory** — skills abstracted from job history, including
   ones not on the resume.
5. **Risk appetite & constraints** — startup vs. enterprise, career-change tolerance,
   hard constraints (these cross-check `profile.yaml`, they do not replace it).
6. **Growth direction** — 3-year picture, what they're moving toward vs. away from.

Rules: prefer concrete stories over self-ratings; the skill synthesizes attributes
from stories rather than asking the user to self-label. If the user has done
`js-resume-review`, the master resume is used to pre-seed section 4 so the interview
confirms rather than re-collects.

## Data: `career-profile.yaml`

```yaml
version: 1                       # schema version — must be 1
assessed: "2026-07-23"           # date of this assessment, quoted YYYY-MM-DD
history:                         # every assessment date, append-only
  - "2026-07-23"
strengths:                       # 3-6 entries: kebab-case name -> one-line evidence story
  systems-thinking: "Mapped the whole claims intake flow before rebuilding it"
  cross-team-translation: "Bridged engineering and underwriting on the pricing rollout"
work_style:
  autonomy: high                 # high | medium | low
  depth_vs_breadth: breadth      # depth | breadth | both
  collaboration: cross-functional  # solo | small-team | cross-functional
motivators:                      # ranked, from the fixed vocabulary below
  - mastery
  - income
  - mission
transferable_skills:             # skill -> where it comes from
  stakeholder management: "insurance product delivery"
risk:
  appetite: medium               # low | medium | high
  notes: "open to Series B+, not pre-seed"
adjacent_titles:                 # real, searchable job titles — feeds js-find-jobs
  - "Solutions Consultant"
  - "Technical Program Manager"
trajectory_signals:              # feeds the Career Trajectory dimension in scoring
  moving_toward:
    - "AI-adjacent delivery leadership"
  moving_away_from:
    - "pure people management"
```

> Shape note (locked at implementation): `strengths` and `transferable_skills` are
> maps (name → text), not lists of objects, so the file stays inside the engine's
> no-PyYAML fallback-parser subset. See `references/career-profile-schema.md`.

Enums and the motivator vocabulary are fixed in the schema reference so the validator
can check them deterministically. Free text is allowed only in `evidence`/`notes`
fields.

## Pipeline integration (all additive, all degrade gracefully)

Absent `career-profile.yaml`, every consumer behaves exactly as today.

1. **`js-find-jobs` / `search_planner.py`** — when a valid profile exists,
   `adjacent_titles` are appended to the query plan as additional title terms.
   The existing search cap (~15–20 searches/run) is respected: adjacent-title
   searches fill remaining budget, never extend it.
2. **`js-evaluate` / `references/scoring-rubric.md`** — the *Career Trajectory*
   dimension's scoring guidance gains a subsection: when a profile exists, score
   trajectory against `trajectory_signals` (a role matching `moving_toward` scores
   high; one matching `moving_away_from` scores low). Weights, bands, and gates
   unchanged — grades stay comparable before/after assessment.
3. **`js-tailor`** — may draw phrasing from `strengths[].evidence` for bullets and
   cover-letter hooks. Framing only: every fact must still trace to the master
   resume, enforced by the existing `resume_qa.py` L1 fabrication gate. The profile
   is never a source of new claims.

## Re-assessment behavior

Re-running `js-assess` with an existing profile:
- Loads the current profile, runs an abbreviated interview focused on what changed.
- Presents a field-level diff (old → new) for user approval before writing.
- Appends the date to `history`; never silently overwrites.

## Validation & testing

- `career_profile_qa.py`: blocking checks = YAML parses, required keys present,
  enums/motivators from fixed vocabulary, `adjacent_titles` non-empty strings;
  warn-only = missing evidence on strengths, stale assessment (>12 months).
  Exit codes match `resume_qa.py` conventions.
- `selftest.py` gains cases: valid profile passes; each invalid class blocks;
  search planner with/without profile (title-append + cap respected); missing
  profile is a clean no-op everywhere.
- Skill instructs the model to run the validator after writing the file and fix
  blocking findings before declaring done.

## Error handling

- Malformed existing profile at consumption time (find-jobs/evaluate/tailor): warn
  once, proceed as if absent — a bad profile must never break the core pipeline.
- Malformed profile at js-assess re-run: surface the validator findings and offer
  a fresh full interview.
- Interview abandoned midway: nothing written; no partial profiles on disk.

## Release checklist (skill lifecycle rule)

1. SkillSpector scan (`skillspector scan --no-llm`) on the updated skill folder.
2. Repackage the umbrella skill so it includes `js-assess`:
   `python3 -m scripts.package_skill Projects/skills/job-search-assistant Projects/skills/`
   (verify the exact source folder name under `Projects/skills/` before running).
3. Update the Current Skills list in `Projects/CLAUDE.md` (job-search-assistant entry
   gains the assessment capability).
4. Update the existing job-search-assistant entry in the Notion SOPs & Build Library
   (no duplicate row), including the Tool Integrations section.
