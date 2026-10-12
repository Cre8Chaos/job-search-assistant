# profile.yaml — schema

This is the shape of the per-user `config/profile.yaml` that the setup interview
(`js-setup`) produces. Every other skill reads it through `scripts/workspace.py`.
**No personal data lives in this engine file** — only the schema and a generic example.

## Fields

| Field | Type | Meaning | Read by |
|---|---|---|---|
| `target_roles` | list[str] | Job titles the user is targeting (confirmed by the user during intake). | search_planner.py |
| `search_keywords` | list[str] | Query strings derived from `target_roles`, used for web-search sourcing. | search_planner.py |
| `location.city` / `.state` / `.zip` | str | Home location (for onsite/hybrid scoring). Any may be blank. | scoring-rubric Remote/Location and Constraints Gate |
| `location.radius_miles` | int | Acceptable commute radius around the location. | scoring-rubric Remote/Location and Constraints Gate |
| `location.remote` | bool | Whether fully-remote roles are in scope. | scoring-rubric Remote/Location and Constraints Gate |
| `salary.min` / `.target` / `.max` | int | Compensation expectations. | scoring-rubric Salary Fit |
| `salary.currency` | str | ISO currency code, e.g. USD. | scoring-rubric Salary Fit |
| `work_model` | list[str] | Any of `remote`, `hybrid`, `onsite`. | scoring-rubric Remote/Location and Constraints Gate |
| `scoring_weights` | map | Six weights that MUST sum to 100. Derived from the "what matters most" intake round. | scoring-rubric |
| `domain.prefer` / `.avoid` | list[str] | Industries to prefer or avoid. | scoring-rubric Tech & Domain |
| `domain.dealbreakers` | list[str] | Hard requirements that auto-disqualify (feeds the domain-expertise gate). | scoring-rubric Domain-Expertise Gate |
| `work_authorization.needs_sponsorship` | bool | `true` = the user is on a visa and requires the employer to sponsor/transfer. Drives the sponsorship gate in `scoring-rubric.md`. **The whole `work_authorization` block is optional; an absent block is treated as `needs_sponsorship: false`** — existing profiles keep working unchanged. | scoring-rubric Sponsorship Gate |
| `work_authorization.visa_type` | str | Optional, informational, e.g. `"F-1 OPT"`, `"H-1B"`, `"TN"`. | context only |
| `work_authorization.notes` | str | Optional free-text, e.g. `"OPT expires 2027-06"`. | context only |
| `travel.max_pct` / `.relocation` | int / bool | Optional. Highest acceptable travel % (integer 0-100) and whether the user would relocate. Absent block = Constraints Gate dormant. | scoring-rubric Constraints Gate, js-find-jobs pre-filter, workspace.py validate |

The six `scoring_weights` keys are fixed (they map 1:1 to the rubric in
`scoring-rubric.md`): `role_title_match`, `salary_fit`, `remote_location`,
`tech_alignment`, `company_stability`, `career_trajectory`.

## Example (generic — not a real user)

```yaml
target_roles:
  - Senior Product Manager
  - Technical Product Manager
  - Platform Product Manager

search_keywords:
  - "Senior Product Manager"
  - "Technical Product Manager"
  - "Platform Product Manager"

location:
  city: ""
  state: ""
  zip: ""
  radius_miles: 25
  remote: true

salary:
  min: 0
  target: 0
  max: 0
  currency: USD

work_model:
  - remote
  - hybrid
  - onsite

# Must sum to 100. Default starting point shown; tuned during intake.
scoring_weights:
  role_title_match: 25
  salary_fit: 20
  remote_location: 20
  tech_alignment: 15
  company_stability: 10
  career_trajectory: 10

domain:
  prefer: []
  avoid: []
  dealbreakers: []

# Optional. Omit the whole block (or set needs_sponsorship: false) for users who are
# already authorized to work without sponsorship — the sponsorship gate stays dormant.
work_authorization:
  needs_sponsorship: false   # true = on a visa, requires employer sponsorship/transfer
  visa_type: ""              # optional, e.g. "F-1 OPT", "H-1B", "TN"
  notes: ""                  # optional, e.g. "OPT expires 2027-06"

# Optional. Omit the whole block and the Constraints Gate stays dormant.
travel:
  max_pct: 25                # highest acceptable travel, integer 0-100
  relocation: false          # would the user relocate
```
