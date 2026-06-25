# Per-Job File Template

One file per opportunity, saved to the workspace `data/jobs/` as
`<company-slug>-<role-slug>-<YYYY-MM-DD>.md`. Skills fill sections in over time.
The tailored resume MUST be wrapped in the RESUME markers so `resume_qa.py` and
`render_pdf.py` can extract it unambiguously (the resume's own `##` headers would
otherwise collide with the job file's `##` sections).

```markdown
---
company: "Company Name"
role: "Role Title"
grade: ""          # filled by evaluation: A|B|C|D|F
status: "New"      # New | Evaluated | Tailored | Ready | Applied | Skip
date_found: "YYYY-MM-DD"
source: ""         # where it was found (search query / board / pasted)
url: ""
sponsorship: ""    # only when the user needs sponsorship: offered | not-stated | refused
---

# Company Name — Role Title

## Metadata
- **Company:**
- **Role:**
- **Location:**
- **Salary:**
- **Work model:**
- **Sponsorship:** [only if the user needs sponsorship: offered | not-stated | refused]
- **Posted:**
- **URL:**
- **Source:**
- **Found:** YYYY-MM-DD

## Full Job Description
[The COMPLETE job description, VERBATIM — every responsibility, requirement,
qualification, benefit, and section header, exactly as fetched or pasted. Do NOT
summarize, paraphrase, or truncate it; this full text is what evaluation and
tailoring rely on. If only part of the posting could be retrieved, save everything
you have and add a line: "JD incomplete — paste the full text to improve scoring."]

## Evaluation
[Filled by js-evaluate — score table, recommendation, the web-verified Company
Snapshot, Top 5 Missing Keywords, director-written key requirements, and the
Interview Prep pack (recruiter screen, one-liner, hiring-manager technical Q&A,
questions to ask, comp strategy, logistics, night-before checklist).]

## Tailored Resume
<!-- RESUME:START -->
[Filled by js-tailor — the full tailored resume in ATS-safe markdown:
# Name / contact line / ## Summary / ## Skills / ## Experience / ## Education /
## Certifications. Nothing here may contradict config/resume.md.]
<!-- RESUME:END -->

## Cover Letter
[Filled by js-tailor — job-specific cover letter.]

## Application Status
- **Applied:**
- **Recruiter / contact:**
- **Last contact:**
- **Next step:**

## Notes
[Free-form.]
```
