# Job Scoring Rubric (config-driven)

Adapted from a proven 6-dimension A–F rubric. **All thresholds come from the
user's `config/profile.yaml`** (resolved via `scripts/workspace.py`) — nothing
about any specific person or number is baked into this file. Read the profile
first, then apply the rubric.

Tokens used below (fill from profile):
`{{TARGET_ROLES}}`, `{{SALARY_MIN}}`, `{{SALARY_TARGET}}`, `{{SALARY_MAX}}`,
`{{CURRENCY}}`, `{{LOCATION}}`, `{{RADIUS_MILES}}`, `{{REMOTE_OK}}`,
`{{PREFERRED_DOMAINS}}`, `{{AVOIDED_DOMAINS}}`, `{{NEEDS_SPONSORSHIP}}`, `{{MAX_TRAVEL_PCT}}`, `{{RELOCATION_OK}}`, and the six
`{{WEIGHT_*}}` values.

## Domain-Expertise Gate (run BEFORE scoring)

Scan the JD for explicit, hard domain/industry requirements (specialized degree,
named proprietary systems unique to one industry, regulated-domain knowledge).
Cross-reference against `config/resume.md` **and** `domain.dealbreakers` in the
profile. If the JD explicitly requires expertise the user does not have:

1. **Cap the grade at D** regardless of other dimensions.
2. Skip the full rubric — note the mismatch.
3. Write to the job file's `## Evaluation`:

```
## Evaluation

**Grade: D (Domain Expertise Mismatch)**

This role explicitly requires [specific expertise] which is not present in the user's background.
**Disqualifying requirement:** [quote the exact JD text]
**Recommendation:** Skip. Do not tailor a resume for this role.
```

Then update the pipeline grade (see Output).

## Sponsorship Gate (run BEFORE scoring — only if `{{NEEDS_SPONSORSHIP}}` is true)

**Skip this gate entirely when `work_authorization.needs_sponsorship` is false or
absent.** When the user needs sponsorship, scan the JD for the employer's stance:

- **Explicit refusal** — phrases such as "must be authorized to work without
  sponsorship", "we are unable to / do not sponsor", "no visa sponsorship", "must not
  require sponsorship now or in the future", "US citizens or green-card holders only":
  1. **Cap the grade at F** regardless of other dimensions.
  2. Skip the full rubric — note the mismatch.
  3. Write to the job file's `## Evaluation`:

  ```
  ## Evaluation

  **Grade: F (No Visa Sponsorship)**

  This employer explicitly will not sponsor, and the user requires sponsorship.
  **Disqualifying requirement:** [quote the exact JD text]
  **Sponsorship:** refused
  **Recommendation:** Skip. Do not tailor a resume for this role.
  ```

  Then update the pipeline grade/status (see Output).

- **Explicit offer** — "visa sponsorship available", "we sponsor", "willing to
  sponsor/transfer": record `Sponsorship: offered` as a positive signal and **proceed
  with the normal rubric** below.
- **Silent** (no sponsorship language): record
  `Sponsorship: not stated — confirm with recruiter` and **proceed normally**.

## Constraints Gate (run BEFORE scoring, only if `profile.yaml` has a `travel` block)

**When `travel` is absent, the whole gate is dormant.** Write
`**Constraints Gate:** dormant (no travel block in profile.yaml)` and continue.

Fill `{{MAX_TRAVEL_PCT}}` from `travel.max_pct` and `{{RELOCATION_OK}}` from
`travel.relocation`. Read the JD body, not the location label (see "Score the JD
body, never the location label alone").

**No quote, no F.** A conflict needs an exact line from the JD body. For travel, words without a number never produce an F. Relocation and onsite conflicts are triggered by the phrases listed in checks 2 and 3, and still need the quoted line.

1. **Travel.** A stated percentage above `{{MAX_TRAVEL_PCT}}` is a conflict. For a
   range or an "up to", use the top number: "up to 30%" and "10-30%" both read as 30.
   A figure equal to the cutoff passes.
2. **Relocation.** When `{{RELOCATION_OK}}` is false: "must relocate", "relocation
   required", or "must be based in <city>" for a city outside `{{RADIUS_MILES}}` mi of
   `{{LOCATION}}` is a conflict. "Relocation assistance available" is not.
3. **Onsite outside the radius.** An explicit requirement to work from an office
   beyond `{{RADIUS_MILES}}` mi of `{{LOCATION}}` (days per week, "onsite",
   "in-office", "standard office environment") is a conflict.

**On a conflict:**
1. **Cap the grade at F** regardless of other dimensions, and skip the full rubric.
2. Write to the job file's `## Evaluation`:

  ```
  ## Evaluation

  **Grade: F (Constraint Conflict)**

  **Constraints Gate:** CONFLICT → F: "[exact JD text]" ([travel | relocation | onsite outside radius])
  **Recommendation:** Skip. Do not tailor a resume for this role.
  ```

3. Update the pipeline grade/status (see Output). Do not pass the job to js-tailor.

**Otherwise** write one of these and proceed with the normal rubric:
- `**Constraints Gate:** PASS`
- `**Constraints Gate:** CHECK: [what is unstated or vague]` for silence or wording
  without a number ("travel as required", "frequent travel", "embedded with client
  teams", `#LI-HYBRID`). No penalty.

## Company Intelligence (live, verified — run BEFORE scoring Salary & Stability)

Establish current, verified facts about the company BEFORE scoring. Do not score
company stability or salary from training data. Anything that changes over time
(ownership, funding, headcount, leadership, recent news) must be confirmed by web
search, because the model's training data goes stale and will state old facts with
full confidence.

Run targeted web searches to confirm:

- **Ownership / structure** — public or private? If public, the ticker. If private,
  who owns it (PE firm, founders, parent company) and the most recent ownership event
  (IPO, take-private, acquisition, merger) with its date.
- **Funding / valuation** — the most recent round or transaction, amount, and date.
- **Size** — current employee headcount (Glassdoor, PitchBook, LinkedIn, or the
  company site).
- **Headquarters and footprint.**
- **Recent developments** — 2–4 items from the last 12 months: product launches,
  acquisitions or divestitures, leadership changes, layoffs, funding.
- **Culture and comp read** — Glassdoor rating, recurring pros and cons, and whether
  employees see comp as above or below market.
- **Comp benchmark** — the company's posted ranges on comparable roles, plus the
  market range for the target title.

Rules:

1. Never state ownership, public/private status, ticker, funding, valuation, or
   headcount from memory. Confirm each by search.
2. If a fact cannot be confirmed, label it "unverified" in the output. Do not guess,
   and do not invent a source.
3. Stamp the output with the verification date.

Write the results into the job file as a **Company Snapshot** block (see Output).
These verified facts drive the Salary Fit and Company Stability scores below.

## Dimensions (score each 0–10, multiply by its weight, sum)

### 1. Role Title Match — weight `{{WEIGHT_ROLE}}`%
- 10: Exact match to one of `{{TARGET_ROLES}}`
- 8–9: Very close synonym
- 6–7: Adjacent title needing similar skills
- 3–5: Stretch role, significant gaps
- 0–2: Poor match

### 2. Salary Fit — weight `{{WEIGHT_SALARY}}`%
Score against the user's band (`{{SALARY_MIN}}`–`{{SALARY_MAX}}` `{{CURRENCY}}`, target `{{SALARY_TARGET}}`):
- 10: JD states pay ≥ `{{SALARY_TARGET}}`
- 8: JD states within the band (≥ `{{SALARY_MIN}}`, below target)
- 6: Salary not listed, or company is plausibly within band
- 4: JD states just below `{{SALARY_MIN}}` (within ~10%)
- 0–2: Clearly below band
- When the JD omits pay, score from the **verified comp benchmark** in Company
  Intelligence (the company's posted ranges on comparable roles plus the market range
  for the title) — not from company prestige or memory.

### 3. Remote / Location — weight `{{WEIGHT_LOCATION}}`%
- 10: Fully remote, no restriction (only full credit if `{{REMOTE_OK}}` is true)
- 8: Remote-first with occasional travel
- 7: Hybrid AND office within `{{RADIUS_MILES}}` mi of `{{LOCATION}}`
- 4: Onsite within `{{RADIUS_MILES}}` mi of `{{LOCATION}}`
- 0: Requires relocation / outside radius
- **Note only (no score change):** required working hours/timezone. Capture them in
  the output so tailoring can address them. Travel is not scored here: the
  Constraints Gate (above) decides it.

#### Score the JD body, never the location label alone

A location string is formatting written by an applicant tracking system. It is not
a statement of work model, and several very common labels mean the opposite of how
they read. Never infer remote from a label:

- **A metro-anchored "(Remote)" label caps at 4, not 10.** `New York City Office
  (Remote)`, `San Francisco (Remote)`, `Remote - Chicago, IL`. These name a hub
  office *and* say remote, which at many employers means remote anchored to that
  hub, i.e. hybrid. Score 10 only when the JD body itself says fully remote / 100%
  remote / remote-first / work from anywhere. If the body is silent, score 4 and
  write "remote unconfirmed — hub-anchored label, JD silent" in the Notes column.
  **Do not pass it to `js-tailor`** until the user confirms.
  - Exception: employers who are genuinely remote-first use this shape for a
    pay-band anchor. Treat it as remote only with evidence from the JD or the
    careers page, recorded in the Company Snapshot. Company reputation is not
    evidence.
- **A bare country or nationwide token is not remote.** `United States`, `USA`,
  `US`, or blank is what an ATS shows for hybrid and onsite roles too. Cap at 6
  unless the JD body confirms remote.
- **A hybrid or onsite `work_model` signal beats any remote wording in the
  location.** Cap at 0 unless the office is within `{{RADIUS_MILES}}` mi of
  `{{LOCATION}}`. If that signal came from a loose keyword scan and the body has no
  real hybrid/onsite requirement, say so in the Notes column rather than quietly
  scoring around it.
- **A multi-office placeholder (`4 Locations`, `See posting`) is not a location.**
  Read the offices out of the posting itself. If none is within
  `{{RADIUS_MILES}}` mi of `{{LOCATION}}` and the JD does not say remote, score 0.

> Why this section exists: two roles once scored **10/10, "Explicitly states
> '<Metro> Office (Remote)' — fully remote"**. Neither job description used the word
> remote anywhere, and both turned out to be hybrid roles in that metro. The label
> was the only evidence and it was treated as proof. A tailored resume and an
> application went out before anyone checked. Absence of evidence is not evidence.

### 4. Tech & Domain Alignment — weight `{{WEIGHT_TECH}}`%
Score how well the role's domain/tech matches `{{PREFERRED_DOMAINS}}` (and is not in `{{AVOIDED_DOMAINS}}`):
- 10: Squarely in a preferred domain / tech focus
- 8: Adjacent, tech-forward
- 6: General role in the field, no strong signal
- 3: Legacy/traditional, weak alignment
- 0: In an avoided domain

### 5. Company Stability — weight `{{WEIGHT_STABILITY}}`%
Score from the **verified facts** in Company Intelligence. Do not score ownership,
funding, or headcount from training data.
- 10: Public or large established private (>1000)
- 8: Series C+ (>200)
- 6: Series B
- 4: Series A / seed
- 2: Unknown, no signals

### 6. Career Trajectory — weight `{{WEIGHT_TRAJECTORY}}`%
Compare to the user's current level (from `config/resume.md`):
- 10: Clear step up in scope/title/comp
- 7: Lateral to a stronger company/domain
- 4: Slight title step back, big company/domain upgrade
- 1–2: Step back in both

**Career-profile signals** *(only when the workspace has a real
`config/career-profile.yaml` — resolve via `workspace.py paths`; a missing or
placeholder file means score exactly as above)*: read `trajectory_signals`.
- The role squarely advances a `moving_toward` direction → score this dimension
  **no lower than 8**, and name the matching signal in the Reasoning cell.
- The role centers on a `moving_away_from` direction → score this dimension
  **no higher than 3**, and name the signal in the Reasoning cell.
- If the file exists but is malformed, ignore it (score as if absent) and add
  one line to the evaluation: `Career profile: unreadable — scored without it.`

Weights and grade bands are unchanged — grades stay comparable whether or not a
career profile exists.

## Director-Written Bullet Detection (after scoring, before grading)
Identify JD bullets written specifically for this role (named tools, rare skill
combinations, language hinting at a past gap, unusually specific).
- **Aligns to background:** list under `**Key Requirements (director-written):**`, flag for tailoring, no grade change.
- **Does NOT align:** downgrade one letter (A→B, B→C, C→D) and explain in a `**Grade Adjustment:**` line.

## Grade Scale
Final = Σ(score × weight / 10).
- **A: 80–100** — strong, prioritize
- **B: 65–79** — good with gaps
- **C: 50–64** — borderline, review manually
- **D: 35–49** — weak, skip unless standout
- **F: 0–34** — poor, skip

## Output (write to the job file's `## Evaluation`)

```
## Evaluation

**Grade: B (72/100)**

| Dimension | Score | Weight | Weighted | Reasoning |
|---|---|---|---|---|
| Role title match | 8/10 | {{WEIGHT_ROLE}}% | … | … |
| Salary fit | 7/10 | {{WEIGHT_SALARY}}% | … | … |
| Remote/location | 10/10 | {{WEIGHT_LOCATION}}% | … | … |
| Tech & domain | 8/10 | {{WEIGHT_TECH}}% | … | … |
| Company stability | 7/10 | {{WEIGHT_STABILITY}}% | … | … |
| Career trajectory | 7/10 | {{WEIGHT_TRAJECTORY}}% | … | … |
| **Total** | | | **72.0** | |

**Recommendation:** …

**Company Snapshot** *(facts verified via web search as of YYYY-MM-DD)*
- **Ownership / structure:** [public + ticker | private + owner]; most recent event: [IPO / take-private / acquisition / merger] (date)
- **Funding / valuation:** [most recent transaction + amount + date, or "n/a"]
- **Size:** ~[headcount] employees ([source])
- **Headquarters:** [city, state]
- **What they do:** [one line]
- **Recent developments:** [2–4 items from the last 12 months]
- **Culture read:** [Glassdoor rating + recurring pros/cons + comp sentiment]
- **Comp benchmark:** [company's posted ranges on comparable roles + market range for the title]
- Any fact that could not be confirmed is labeled "unverified."

**Sponsorship:** [only when the user needs sponsorship — one of: refused | offered | not stated — confirm with recruiter]
**Constraints Gate:** [PASS | CHECK: … | dormant (no travel block in profile.yaml)]
**Timezone/Travel:** [e.g. "EST hours required", "up to 10% travel", or "Not specified"]
**Top 5 Missing Keywords:** keyword1, keyword2, keyword3, keyword4, keyword5
**Key Requirements (director-written):** [if any]
**Grade Adjustment:** [if any]

**Fit notes** *(never changes the grade; skip with "Fit notes: skipped, no career profile" when there is none)*
- Why it fits (up to 2): "[JD quote]" ↔ [motivators | work_style | energizers | transferable_skills]: [value]
- Watch out (up to 2, PRIVATE): "[JD quote]" ↔ [drains | weaknesses | work_style]: [value]. Ask: [one interview question]
- A line without both a JD quote and a field name is not written. If no line qualifies: "no JD line matched a profile field".

---

**Interview Prep**

**Stage:** If the user named the interview stage (recruiter screen, hiring-manager round, panel), weight this prep to that stage and say which one it is. If the stage is unknown, include both the recruiter screen and the hiring-manager sets below. A recruiter screen and a technical round need different prep — don't hand someone technical STAR answers for a call that's really about logistics and comp.

**One-line positioning** — a single sentence the candidate leads with when asked "why you." Land domain fit, the strongest differentiator for this role, and why this candidate over a generic one. Ground it only in real experience from config/resume.md.

**Recruiter / HR screen** — the questions a recruiter actually asks, with how to answer each (60–90 seconds, lead with a concrete example), grounded only in config/resume.md and the Company Snapshot:
- "Tell me about yourself." Three beats: where you are now, the through-line of your career, what you're running toward. Not a resume recital.
- "Why are you looking / why leave?" Forward pull, never a complaint about the current employer.
- "Why this company?" Tie domain + the role's focus + something current about the company (from the Company Snapshot — a recent move, the ownership structure, a strategic shift).
- "Walk me through your relevant experience." The screening-checkbox question for the role's headline requirement. Be specific and honest; name the growth edge rather than bluffing it.
- "Compensation expectations." See the comp strategy below.
- "Work arrangement / availability." Clean answers once logistics are confirmed.

**Hiring-manager technical Q&A** — adopt the persona of the hiring manager for this role. Ask the 3 hardest TECHNICAL questions that expose whether the candidate can actually do the job, targeting the toughest JD requirements/differentiators. For each, write the perfect response in STAR format, grounded ONLY in real experience from config/resume.md. If a question targets something the candidate hasn't done directly, translate the closest adjacent experience honestly and signal what they'd ramp on first. Never fabricate.
- **Q1** (hardest — usually the most-cited "must have"): *Why it matters:* one line. *STAR:* Situation (real context from a role in resume.md) / Task / Action (language from a real bullet) / Result (the measured outcome from the source bullet).
- **Q2** (a JD differentiator or domain challenge): *Why it matters* + *STAR* as above.
- **Q3** (often a stretch area or honest gap): *Why it matters* + *STAR* — direct experience if it exists; otherwise translate the closest adjacent experience and name the ramp.

**Questions for the candidate to ask** — two sets:
- For the recruiter: new role vs. backfill, interview process and timeline, work model, budgeted range, how the company thinks about the role's focus area.
- For the hiring manager: how they define success for this role, how the work splits across teams, what the hard problems are, what the first 90 days look like.

**Compensation strategy** — using the comp benchmark from the Company Snapshot: state a defensible target band for this title at this company; coach the get-their-range-first move (ask whether they have a budgeted band before naming a number); give a fallback line if pushed to name a number first, anchored in the upper half of the benchmark.

**Logistics to confirm** — work model (remote/hybrid/onsite and actual cadence), process and timeline, and why the role is open.

**Night-before checklist** — 5–7 concrete items: re-read the JD and the clear-the-bar facts, lock the one-liner, decide the comp band and opening line, have two current company facts ready, pick the questions to ask, and a setup check (quiet room, headset, resume and notes open).
```

Then append the complete JD under `## Full Job Description`, and update the pipeline grade.
