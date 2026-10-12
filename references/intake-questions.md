# Intake Interview Script

The setup skill (`js-setup`) walks these six rounds to produce
`config/profile.yaml`. Ask each round as **one message with its grouped
questions** (not one question at a time, not all at once). Confirm and move
on. Keep it to ~3 minutes.

> Use the AskUserQuestion tool for the multiple-choice parts; use plain prompts
> for open-ended parts. Synthesize answers into the schema in `profile-schema.md`.

## Round 1 — Target roles  (REQUIRED confirmation gate)
Ask: "What roles are you targeting? List 1–5 job titles, or describe the kind of
work you want and I'll propose titles."
- Normalize the user's answer into a `target_roles` list and a derived
  `search_keywords` list (the quoted query strings used for web search).
- **Then explicitly confirm before writing anything:** present the proposed title
  list and ask the user to confirm / add / remove. Do not write `profile.yaml`
  until the user approves the titles. (This confirmation is required.)

## Round 2 — Location & work model
Ask together:
- Acceptable work models? (remote / hybrid / onsite — multi-select)
- Home city/state (and ZIP if they want onsite/hybrid scored by distance)
- Acceptable commute radius in miles (default 25)
- Most travel you will accept, as a percentage, and would you relocate? (optional)
Set `location.*`, `work_model`, and (if answered) `travel.max_pct` / `travel.relocation`. If they only want remote, location may be blank.

## Round 3 — Work authorization
Ask (AskUserQuestion, single choice): "Are you legally authorized to work in your
target country **without** employer sponsorship, or will you need an employer to
**sponsor or transfer** a visa (now or in the future)?"
- "Authorized — no sponsorship needed" → `work_authorization.needs_sponsorship: false`.
- "I need sponsorship (I'm on / will need a work visa)" →
  `work_authorization.needs_sponsorship: true`. Then ask one open follow-up for the
  visa type (e.g. F-1 OPT, H-1B, TN — optional) → `work_authorization.visa_type`, and
  any timing note → `work_authorization.notes`.
When `needs_sponsorship` is true, sourcing avoids/flags non-sponsoring postings and
evaluation hard-gates roles that explicitly refuse sponsorship. When false, all of
that stays dormant. Default to `false` if the user skips.

## Round 4 — Compensation
Ask: minimum acceptable, target, and stretch/max — plus currency (default USD).
Set `salary.min`, `salary.target`, `salary.max`, `salary.currency`. Reassure that
this stays local and is only used for scoring.

## Round 5 — What matters most  (derives scoring_weights)
"Rate how much each of these matters to you, 1 (minor) to 5 (critical):"
- Role/title fit
- Salary
- Location / remote
- Tech & domain alignment
- Company stability
- Career trajectory (step up vs. lateral)
Offer the default split (25/20/20/15/10/10) as a starting point they can accept.
**Normalize the 1–5 ratings to weights that sum to exactly 100** (e.g. weight_i =
round(rating_i / Σ ratings × 100), then adjust the largest to absorb rounding so
the total is 100). Write `scoring_weights` with the six fixed keys.

## Round 6 — Domain & dealbreakers
Ask together:
- Industries/domains you prefer? (→ `domain.prefer`)
- Industries/domains to avoid? (→ `domain.avoid`)
- Any hard dealbreakers that should auto-disqualify a role? (→ `domain.dealbreakers`)

## After the rounds
- Write `config/profile.yaml` (via the resolved workspace path) matching
  `profile-schema.md`. Verify `scoring_weights` sums to 100. Include the
  `work_authorization` block (default `needs_sponsorship: false`).
- Confirm the saved profile back to the user in a short summary, then hand off to
  resume review.
