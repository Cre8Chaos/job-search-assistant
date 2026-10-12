# career-profile.yaml — Schema

Written by the `js-assess` skill into the workspace at the `career_profile` path
from `scripts/workspace.py paths`. **Optional** — every skill and script treats a
missing or placeholder file as absent. Validated by `scripts/career_profile_qa.py`
(blocking for js-assess; soft/no-op for consumers).

**Parser constraint (hard):** the file must stay inside the engine's no-PyYAML
fallback parser subset — top-level scalars and lists, one level of nested map,
lists nested under a map key. **No lists of maps.** That is why `strengths` and
`transferable_skills` are maps (name → text), not lists of objects. Quote dates
and any free text containing `:` or `#`.

## Example

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
energizers:                      # what gives energy (user's words)
  - "untangling a messy process"
drains:                          # PRIVATE: what takes energy
  - "long stretches of status reporting"
weaknesses:                      # PRIVATE: kebab name -> description
  over-scoping: "Tends to take on too much before checking capacity"
interests:                       # context only
  - "trail running"
```

## Field rules

| Field | Required | Rule | Read by |
|---|---|---|---|
| `version` | yes | Integer `1`. | js-assess, career_profile_qa.py |
| `assessed` | yes | Quoted `YYYY-MM-DD`. | js-assess, career_profile_qa.py |
| `history` | no | List of quoted dates, append-only across re-runs. | js-assess, career_profile_qa.py |
| `strengths` | yes | Map, 3–6 entries; each value is a one-line evidence story (warn if empty). | js-tailor (tone) |
| `work_style` | yes | All three keys, values from the enums above. | js-evaluate Fit notes |
| `motivators` | yes | Non-empty ranked list; vocabulary: `mastery`, `income`, `mission`, `autonomy`, `status`, `stability`, `impact`, `learning`. No duplicates. | js-evaluate Fit notes |
| `transferable_skills` | no | Map: skill → origin. | js-tailor (framing), js-evaluate Fit notes |
| `risk` | no | `appetite` from `low`/`medium`/`high` (warn otherwise); `notes` free text. | context only (appetite and notes about risk, not constraints) |
| `adjacent_titles` | yes | Non-empty list of non-empty strings; concrete searchable titles. | search_planner.py, js-find-jobs |
| `trajectory_signals` | yes | `moving_toward` non-empty list of strings; `moving_away_from` a list (may be empty). | scoring-rubric Career Trajectory |
| `energizers` | no | List of non-empty strings; what gives energy, in the user's words. | js-tailor (framing), js-evaluate Fit notes |
| `drains` | no | List of non-empty strings; what takes energy. | PRIVATE: js-evaluate Fit notes and Interview Prep only |
| `weaknesses` | no | Map: kebab-case name → description. | PRIVATE: js-evaluate Fit notes and Interview Prep only |
| `interests` | no | List of non-empty strings; outside work. | context only |

Free text lives in strength/skill values, `risk.notes`, and the four v2 keys. `drains` and `weaknesses` are PRIVATE: js-evaluate Fit notes and Interview Prep only. A future web quiz
(Phase 3) emits this same file — the file format is the seam, not the interview.
