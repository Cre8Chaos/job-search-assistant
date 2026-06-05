# profile.yaml — schema

This is the shape of the per-user `config/profile.yaml` that the setup interview
(`js-setup`) produces. Every other skill reads it through `scripts/workspace.py`.
**No personal data lives in this engine file** — only the schema and a generic example.

## Fields

| Field | Type | Meaning |
|---|---|---|
| `target_roles` | list[str] | Job titles the user is targeting (confirmed by the user during intake). |
| `search_keywords` | list[str] | Query strings derived from `target_roles`, used for web-search sourcing. |
| `location.city` / `.state` / `.zip` | str | Home location (for onsite/hybrid scoring). Any may be blank. |
| `location.radius_miles` | int | Acceptable commute radius around the location. |
| `location.remote` | bool | Whether fully-remote roles are in scope. |
| `salary.min` / `.target` / `.max` | int | Compensation expectations. |
| `salary.currency` | str | ISO currency code, e.g. USD. |
| `work_model` | list[str] | Any of `remote`, `hybrid`, `onsite`. |
| `scoring_weights` | map | Six weights that MUST sum to 100. Derived from the "what matters most" intake round. |
| `domain.prefer` / `.avoid` | list[str] | Industries to prefer or avoid. |
| `domain.dealbreakers` | list[str] | Hard requirements that auto-disqualify (feeds the domain-expertise gate). |
| `work_authorization.needs_sponsorship` | bool | `true` = the user is on a visa and requires the employer to sponsor/transfer. Drives the sponsorship gate in `scoring-rubric.md`. **The whole `work_authorization` block is optional; an absent block is treated as `needs_sponsorship: false`** — existing profiles keep working unchanged. |
| `work_authorization.visa_type` | str | Optional, informational, e.g. `"F-1 OPT"`, `"H-1B"`, `"TN"`. |
| `work_authorization.notes` | str | Optional free-text, e.g. `"OPT expires 2027-06"`. |

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
```
