# Assessment v2: a Constraints Gate, and profile fields that actually get read

Date: 2026-10-12. Status: design approved section by section in chat by the
maintainer; awaiting review of this written spec.
Scope: the Product (`job-search-assistant`) only. The Daily Driver is out of scope.

## Problem

`career-profile.yaml` has seven content fields, and only three drive anything today:
`strengths` (js-tailor tone), `adjacent_titles` (js-find-jobs sourcing), and
`trajectory_signals` (the Career Trajectory score). `work_style`, `motivators`,
`transferable_skills`, and `risk` are asked for in rounds 2 to 5 of the js-assess
interview, validated by `career_profile_qa.py`, and never read.

A real re-assessment (the maintainer's, 2026-10-08) also captured answers with no
field to hold them: a weakness, a drain, energizers, interests outside work, hard
constraints (remote or hybrid inside the home radius, no relocation, home most
nights), and a tension (enjoys personal travel, needs to be home most nights). They
ended up as prose in the adjacent-paths report, where nothing reads them.

The constraints cost real time. In a 2026-10-12 triage of 23 graded jobs, one role
stating 30%+ travel and two office-based roles outside the commute radius (both
graded B) had to be filtered by hand. The current rubric only zeroes the location score for an office
outside the radius, and it records travel % as "note only".

## Decisions (made by the maintainer, 2026-10-12)

1. **Gates and framing are separate.** Constraints decide which jobs survive.
   Everything else shapes what the user reads and never changes a grade.
2. **An explicit conflict caps the grade at F. Silence is flagged with no penalty.**
   This copies the existing Sponsorship Gate.
3. **The travel cutoff is a number: 20%.** Stored per user, not hardcoded.
4. **Drains and weaknesses are private.** They may appear only in js-evaluate's Fit
   notes and Interview Prep, never in a resume or cover letter, and a QA check
   enforces that.
5. **Approach 1:** hard constraints live in `profile.yaml` next to
   `work_authorization`. Soft fields live in `career-profile.yaml`.

## Success criteria

- Every field in both schemas names its reader, or is labeled `context only`.
- With no `travel` block and none of the new career-profile keys, every skill and
  script behaves exactly as it does today.
- The three hand-filtered roles from the 2026-10-12 triage (30%+ travel, and two
  office-based roles outside the radius) would be graded F by the gate, each with a
  quoted JD line.
- No drain or weakness text can reach a tailored resume or cover letter without
  `resume_qa.py` failing.

## 1. Data model

### `profile.yaml`: new optional `travel` block

Documented in `references/profile-schema.md`.

```yaml
travel:                 # optional; absent = Constraints Gate dormant (today's behavior)
  max_pct: 20           # integer 0-100; an explicit JD figure above this is a conflict
  relocation: false     # false = an explicit relocation requirement is a conflict
```

- `js-setup` asks for it as one intake question: "What is the most travel you will
  accept, as a percentage, and would you relocate?" Users who skip it get no block.
- The gate also reads the existing `location.city/state/zip`, `location.radius_miles`,
  `location.remote`, and `work_model`. Those fields do not move.
- Validation lives in `scripts/workspace.py validate`, which today only checks that
  the profile and resume are not placeholders. It gains one check: if a `travel`
  block is present, `max_pct` must be an integer from 0 to 100 and `relocation` a
  boolean, or validate reports the problem and exits 1. An absent block is valid.

### `career-profile.yaml`: four new optional keys

`version` stays `1`. The keys are additive and optional, so no existing reader breaks.
All four stay inside the no-PyYAML fallback parser subset (no lists of maps).

```yaml
energizers:             # list of short phrases, in the user's words
  - "untangling a messy process"
drains:                 # PRIVATE. List, in the user's words
  - "long stretches of status reporting"
weaknesses:             # PRIVATE. Map: kebab-case name -> one-line description
  over-scoping: "says yes to too much at the start of a project"
interests:              # CONTEXT ONLY. Read by nothing
  - "trail running"
```

`career_profile_qa.py` rules for the new keys:

| Key | Rule | On failure |
|---|---|---|
| `energizers` | list of non-empty strings | warn |
| `drains` | list of non-empty strings | warn |
| `weaknesses` | map, kebab-case keys, non-empty string values | warn |
| `interests` | list of non-empty strings | warn |

None of the four blocks a run. `REQUIRED_KEYS` is unchanged.

### The Read-by column

Both schema tables (`profile-schema.md`, `career-profile-schema.md`) gain a
**Read by** column. Every row holds one of: a named consumer (skill or script),
`context only`, or `PRIVATE: js-evaluate Fit notes and Interview Prep only`.
This is documentation, not a script check. Its job is to make an unread field
visible at review time.

| Field | Read by (after v2) |
|---|---|
| `strengths` | js-tailor (tone) |
| `work_style` | js-evaluate Fit notes |
| `motivators` | js-evaluate Fit notes |
| `transferable_skills` | js-tailor (framing), js-evaluate Fit notes |
| `risk` | context only (appetite and notes about risk, not constraints) |
| `adjacent_titles` | search_planner.py, js-find-jobs |
| `trajectory_signals` | scoring-rubric Career Trajectory |
| `energizers` | js-tailor (framing), js-evaluate Fit notes |
| `drains` | PRIVATE: js-evaluate Fit notes and Interview Prep only |
| `weaknesses` | PRIVATE: js-evaluate Fit notes and Interview Prep only |
| `interests` | context only |
| `travel.max_pct`, `travel.relocation` | scoring-rubric Constraints Gate, js-find-jobs pre-filter |

### Migration

A profile whose `risk.notes` holds constraint text (the maintainer's does) is not
rewritten automatically. js-assess re-assessment mode proposes moving that text into
`profile.yaml`'s `travel` block and the new keys, one line at a time, and writes
only what the user approves.

## 2. The Constraints Gate

A new section in `references/scoring-rubric.md`, placed directly after the
Sponsorship Gate and run before scoring.

**When it runs:** only when `profile.yaml` has a `travel` block. With no block the
entire gate, including check 3, stays dormant.

**Placeholders filled from the profile:** `{{MAX_TRAVEL_PCT}}`, `{{RELOCATION_OK}}`,
plus the existing `{{LOCATION}}` and `{{RADIUS_MILES}}`.

**Three checks. Each CONFLICT requires a quoted line from the JD body. No quote, no F.**

1. **Travel.** A stated percentage above `{{MAX_TRAVEL_PCT}}` is a conflict. For a
   range or an "up to", use the top number: "up to 25%" and "10-25%" both read as 25.
2. **Relocation.** When `{{RELOCATION_OK}}` is false: "must relocate", "relocation
   required", or "must be based in <city>" (a city outside the radius) is a conflict.
   "Relocation assistance available" is not.
3. **Onsite outside the radius.** An explicit requirement to work from an office
   beyond `{{RADIUS_MILES}}` of `{{LOCATION}}` (days per week, "onsite", "in-office")
   is a conflict.

**Output, one line in every evaluation:**

- `Constraints Gate: PASS`
- `Constraints Gate: CONFLICT → F: "<quote>"`. The grade is capped at F, the reason is
  printed, and the job is not passed to js-tailor.
- `Constraints Gate: CHECK: <what is unstated or vague>`. No penalty. This covers
  silence and qualitative wording ("travel as required", "frequent travel",
  `#LI-HYBRID`). Words with no number never produce an F.
- `Constraints Gate: dormant (no travel block in profile.yaml)`

**Edits elsewhere in the rubric:**

- In "3. Remote / Location", the bullet "Note only (no score change): required working
  hours/timezone and travel %" loses "and travel %" and gains a pointer to the
  Constraints Gate. Working hours and timezone stay note-only. This removal is
  required: an older instruction left in place would let the gate be read around.
- The six scoring weights and the existing location caps (including the
  2026-07-30 "Score the JD body, never the location label" rules, commit `e2404d1`)
  are unchanged.

**Mirror in `skills/js-find-jobs/SKILL.md` step 6 (coarse pre-filter):** the same three
checks, matching the sponsorship pattern. An explicit conflict is dropped or kept
flagged `constraints: conflict`. When unsure, keep and flag.

**Sanity check against the kinds of JD lines seen in the 2026-10-12 triage:**

| JD says | Expected (max 20%, no relocation) |
|---|---|
| "Travel up to 30%+ for onsite workshops" | CONFLICT → F (travel) |
| "This role operates in a standard office environment", office 60 mi away | CONFLICT → F (onsite outside radius) |
| A city name only, no work-model statement in the body | CHECK (onsite unconfirmed) |
| "Travel: up to 10%" | PASS |
| "Teams meet once or twice per quarter for 2-4 days", no % | PASS |
| "You'll work embedded with client teams" | CHECK |
| `#LI-REMOTE OR #LI-HYBRID`, no travel stated | CHECK |

## 3. Framing

### js-evaluate: a new Fit notes block

Written to the job file's `## Evaluation` after the scores. It never changes a grade.

- **Why it fits:** up to 2 lines. Each pairs a quoted JD phrase with a named profile
  field drawn from `motivators`, `work_style`, `energizers`, or `transferable_skills`.
  Format: `"<JD quote>" ↔ <field>: <value>`.
- **Watch out:** up to 2 lines from `drains`, `weaknesses`, or a `work_style`
  mismatch. Each ends with one question to ask in the interview. These questions are
  also added to the existing Interview Prep pack.
- **Tracing rule:** a line without both a JD quote and a field name is not written.
  Fewer lines is fine. An empty block says why ("no JD line matched a profile field").
- **No career profile:** the block prints `Fit notes: skipped, no career profile`, so
  an empty result and a broken step never look the same.

This tracing rule is the seam the later per-job pitch builds on.

### js-tailor

Reads `transferable_skills` and `energizers` for summary and cover-letter framing.
Same rule as `strengths` today: framing only, never a new fact. Never reads `drains`,
`weaknesses`, or `interests`; the SKILL.md says so explicitly.

### resume_qa.py: the private-leak check

A new check, enforced in code because an instruction alone has already failed once
(the 2026-10-12 triage found five tailored summaries, in a sibling system with a
stricter gate than this one, claiming work never done, and all had passed QA).

- Loads `drains` and `weaknesses` from the career profile, if present.
- Normalizes case, punctuation, and whitespace on both sides.
- Fails the resume or cover letter if any drain phrase, weakness description, or
  weakness kebab name (hyphens read as spaces) appears in it.
- No career profile, or neither key present: the check does not run, and the output
  says so in one line.

### interests

Read by nothing. Labeled `context only` in the schema.

## 4. Testing

**Degradation contract.** With no `travel` block and none of the new keys:
- `scripts/selftest.py` passes with no changes to existing fixtures.
- `search_planner.py` output is byte-identical before and after, for the existing
  fixture profiles.

**Unit tests, added to `scripts/selftest.py`:**
- `career_profile_qa.py`: valid new keys pass. Each wrong type warns and never
  blocks. The July-shaped v1 profile gets the same verdict as before.
- `workspace.py validate` on `travel`: `max_pct` 0 to 100 integer, `relocation`
  boolean, absent block valid, malformed block exits 1 with the problem named.
- Private-leak check: a planted drain phrase fails; a weakness kebab name fails; a
  casing or punctuation near-miss fails; a clean resume passes; no profile skips.
- **Mutation proof:** with the leak check disabled, the failing cases go red. This
  proves the check matches something.

**Instruction-driven behavior (the gate and Fit notes) gets known-answer fixtures,**
because a unit test cannot prove what a model does with a rubric:
- Five JDs under `tests/fixtures/constraints/`, expected results written by hand in a
  file the graded run cannot see:
  1. "Travel up to 30%" → CONFLICT
  2. "Relocation to Chicago required" → CONFLICT
  3. "3 days a week in our Chicago office", fixture profile in Springfield IL with a
     35 mi radius → CONFLICT
  4. "Travel as required" → CHECK
  5. "Fully remote, up to 10% travel" → PASS
- Each fixture is run through js-evaluate in a fresh `claude -p` session that holds
  only the skill and rubric, then graded against the expected file.
- Text checks on the rubric: all three checks present, the "no quote, no F" rule
  present, and "and travel %" absent from the Remote / Location note-only bullet.

**Before done:**
- `/cross-check` with Codex through `codex_judge.py`.
- Skill lifecycle for each changed skill (js-assess, js-evaluate, js-tailor,
  js-find-jobs, js-setup): SkillSpector scan, package, the CLAUDE.md skills entry for
  `job-search-assistant`, and its Notion SOP row.

## Out of scope

- The Daily Driver (the maintainer's separate personal system). It does not get the
  gate until it is ported.
- The per-job pitch (its own spec; it consumes the Fit notes tracing rule).
- A web quiz.
- Any change to scoring weights, grade bands, or the Sponsorship Gate.

## Files touched

| File | Change |
|---|---|
| `references/profile-schema.md` | `travel` block, Read-by column |
| `references/career-profile-schema.md` | four keys, Read-by column, privacy labels |
| `references/scoring-rubric.md` | Constraints Gate section, note-only bullet edit, Fit notes in Output |
| `references/assessment-questions.md` | where each new key is captured (rounds 1, 5) |
| `skills/js-setup/SKILL.md` | one travel/relocation intake question |
| `skills/js-assess/SKILL.md` | write the new keys; re-assessment migration step |
| `skills/js-evaluate/SKILL.md` | run the gate; write Fit notes; Watch-out questions into Interview Prep |
| `skills/js-tailor/SKILL.md` | read `transferable_skills` and `energizers`; never the private keys |
| `skills/js-find-jobs/SKILL.md` | pre-filter mirror |
| `scripts/career_profile_qa.py` | warn-only validation of the four keys |
| `scripts/workspace.py` | `travel` block check in `validate` |
| `scripts/resume_qa.py` | private-leak check |
| `scripts/selftest.py` | the unit tests above |
| `tests/fixtures/constraints/` | five JDs and the hidden expected file |
