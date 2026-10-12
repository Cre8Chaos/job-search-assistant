# Cover Letter Rules

Draft a concise, job-specific cover letter for an A/B grade job. Same honesty bar
as the resume: **every claim must trace to `config/resume.md`.** No fabrication.

## Structure (≈250–350 words, 3–4 short paragraphs)
1. **Opening (2–3 sentences):** name the exact role and company; state the single
   strongest reason the user fits, grounded in a real accomplishment.
2. **Body (1–2 paragraphs):** address the JD's **director-written Key Requirements**
   (from the evaluation) directly — one concrete, true example per requirement,
   ideally with a metric that already exists in the master resume. Mirror 1–2 of
   the company's stated values/principles naturally if the JD lists them.
3. **Fit & logistics (optional sentence):** if the evaluation's Timezone/Travel
   field is set, address it plainly ("Available for Eastern Time hours", "open to
   up to 10% travel").
4. **Close (1–2 sentences):** forward-looking, specific to the company's mission;
   thank the reader; no generic filler.

## Rules
- Address a real requirement, not a generic pitch. If you can't ground a claim in
  the master resume, leave it out.
- No clichés ("hard-working team player"), no restating the whole resume.
- Match the company's tone from the JD (formal vs. casual) where discernible.
- Write to `## Cover Letter` in the job file.
- `resume_qa.py` checks the cover letter only for PRIVATE career-profile text (drains, weaknesses); re-run it after writing the letter (js-tailor step 5). Its other checks are resume-shaped, so the no-fabrication rule still applies: self-check every claim against the master.
