# Job Scoring Rubric (config-driven)

Adapted from a proven 6-dimension A–F rubric. **All thresholds come from the
user's `config/profile.yaml`** (resolved via `scripts/workspace.py`) — nothing
about any specific person or number is baked into this file. Read the profile
first, then apply the rubric.

Tokens used below (fill from profile):
`{{TARGET_ROLES}}`, `{{SALARY_MIN}}`, `{{SALARY_TARGET}}`, `{{SALARY_MAX}}`,
`{{CURRENCY}}`, `{{LOCATION}}`, `{{RADIUS_MILES}}`, `{{REMOTE_OK}}`,
`{{PREFERRED_DOMAINS}}`, `{{AVOIDED_DOMAINS}}`, `{{NEEDS_SPONSORSHIP}}`, and the six
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

### 3. Remote / Location — weight `{{WEIGHT_LOCATION}}`%
- 10: Fully remote, no restriction (only full credit if `{{REMOTE_OK}}` is true)
- 8: Remote-first with occasional travel
- 7: Hybrid AND office within `{{RADIUS_MILES}}` mi of `{{LOCATION}}`
- 4: Onsite within `{{RADIUS_MILES}}` mi of `{{LOCATION}}`
- 0: Requires relocation / outside radius
- **Note only (no score change):** required working hours/timezone and travel %.
  Capture them in the output so tailoring can address them.

### 4. Tech & Domain Alignment — weight `{{WEIGHT_TECH}}`%
Score how well the role's domain/tech matches `{{PREFERRED_DOMAINS}}` (and is not in `{{AVOIDED_DOMAINS}}`):
- 10: Squarely in a preferred domain / tech focus
- 8: Adjacent, tech-forward
- 6: General role in the field, no strong signal
- 3: Legacy/traditional, weak alignment
- 0: In an avoided domain

### 5. Company Stability — weight `{{WEIGHT_STABILITY}}`%
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
**Sponsorship:** [only when the user needs sponsorship — one of: refused | offered | not stated — confirm with recruiter]
**Timezone/Travel:** [e.g. "EST hours required", "up to 10% travel", or "Not specified"]
**Top 5 Missing Keywords:** keyword1, keyword2, keyword3, keyword4, keyword5
**Key Requirements (director-written):** [if any]
**Grade Adjustment:** [if any]

---

**Hiring Manager Interview Prep**
*The 3 hardest questions a hiring manager would ask for this role, with ideal answers grounded in the user's real experience from config/resume.md:*

**Q1: …**
> **Ideal Answer:** …
**Q2: …**
> **Ideal Answer:** …
**Q3: …**
> **Ideal Answer:** …
```

Then append the complete JD under `## Full Job Description`, and update the pipeline grade.
