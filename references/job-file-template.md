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
---

# Company Name — Role Title

## Metadata
- **Company:**
- **Role:**
- **Location:**
- **Salary:**
- **Work model:**
- **Posted:**
- **URL:**
- **Source:**
- **Found:** YYYY-MM-DD

## Full Job Description
[Complete JD text — every bullet/section as fetched or pasted. If extraction was
partial, note "JD incomplete — paste full text to improve scoring."]

## Evaluation
[Filled by js-evaluate — score table, recommendation, Top 5 Missing Keywords,
director-written key requirements, hiring-manager Q&A.]

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
