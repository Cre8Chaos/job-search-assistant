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
```

## Field rules

| Field | Required | Rule |
|---|---|---|
| `version` | yes | Integer `1`. |
| `assessed` | yes | Quoted `YYYY-MM-DD`. |
| `history` | no | List of quoted dates, append-only across re-runs. |
| `strengths` | yes | Map, 3–6 entries; each value is a one-line evidence story (warn if empty). |
| `work_style` | yes | All three keys, values from the enums above. |
| `motivators` | yes | Non-empty ranked list; vocabulary: `mastery`, `income`, `mission`, `autonomy`, `status`, `stability`, `impact`, `learning`. No duplicates. |
| `transferable_skills` | no | Map: skill → origin. |
| `risk` | no | `appetite` from `low`/`medium`/`high` (warn otherwise); `notes` free text. |
| `adjacent_titles` | yes | Non-empty list of non-empty strings; concrete searchable titles. |
| `trajectory_signals` | yes | `moving_toward` non-empty list of strings; `moving_away_from` a list (may be empty). |

Free text lives only in strength/skill values and `risk.notes`. A future web quiz
(Phase 3) emits this same file — the file format is the seam, not the interview.
