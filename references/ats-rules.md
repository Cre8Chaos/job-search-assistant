# Resume Tailoring Rules (ATS-first, no fabrication)

These rules govern how a master resume is tailored to a specific job. They are
adapted from a proven tailoring playbook and are intentionally strict — the
`scripts/resume_qa.py` gate enforces the non-negotiables mechanically afterward.

## Non-Negotiable Rules
1. **No fabrication.** Every bullet, skill, certification, employer, title, date,
   and metric must trace to `config/resume.md`. If the JD wants a skill the user
   lacks, do not add it.
2. **Factual reordering only.** Reorder bullets to front-load relevance; rephrase
   using the JD's language ONLY when the meaning is factually identical.
3. **Source of truth.** `config/resume.md` is immutable. Never modify it.
4. **ATS-first.** Write for a machine parser first: single column, no tables, no
   columns, no text boxes, no images. Section headers from the standard set
   (Summary, Skills, Experience, Education, Certifications).

## Grade Gate
Only tailor for **A or B** grade jobs. For C/D/F or a Domain-Expertise Mismatch,
stop and tell the user the grade — do not tailor.

## Steps
1. **Read inputs:** full `config/resume.md`; the job file's `## Full Job Description`
   and `## Evaluation`. Note any company values/principles in the JD. Skip the **Fit notes** block and the **Interview Prep** pack inside `## Evaluation`: they hold PRIVATE career-profile text and are not tailoring inputs.
2. **Extract 15–20 ATS keywords** from the JD (exact title words, required
   tools/methods, core responsibilities, differentiators).
3. **Identify the Top 5 Missing Keywords** — JD keywords that do NOT appear
   anywhere in `config/resume.md`. These drive the experience rewrite and must be
   reported. (The evaluation step usually already lists these — reuse them.)
4. **Named tools:** if a JD tool isn't in the resume but a similar one is, write
   `[User's Tool] (similar to [JD Tool])` so the JD term is present for ATS
   matching without fabricating experience. If neither, omit it.
5. **Write the tailored resume:**
   - **Summary (3–4 sentences):** open with the job's exact title or close variant;
     echo 2–3 JD phrases; mirror 1–2 company values if listed; if the eval's
     Timezone/Travel field is set, address it explicitly; if a rare skill combo is
     a key requirement, name it ("unique blend of X and Y").
   - **Skills:** reorder to front-load JD keywords; list specific tool names.
   - **Experience:** keep all roles/titles/companies/dates exactly as in the master;
     reorder bullets (most JD-relevant first); rephrase with the **Google X-Y-Z
     formula** — "Accomplished [X] as measured by [Y], by doing [Z]" — using only
     facts/metrics already in the master; weave each Top-5 Missing Keyword in at
     least once (truthfully); address each director-written Key Requirement.
   - **Education & Certifications:** exactly as in the master.
6. **Write into the job file** using the structure in `job-file-template.md` —
   the tailored resume body MUST be wrapped in `<!-- RESUME:START -->` /
   `<!-- RESUME:END -->` markers so the QA validator and PDF renderer can find it.
7. **Run the QA gate:** `python scripts/resume_qa.py --mode tailored --job <file>`.
   - Exit 1 (blocking failure) → fix the flagged items before delivering or
     rendering a PDF. Layer 1 (fabrication) failures usually mean a claim doesn't
     trace to the master — correct it.
   - Exit 0 → proceed to optional PDF and cover letter.
