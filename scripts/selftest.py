#!/usr/bin/env python3
"""
selftest.py — deterministic engine self-tests.

Reuses the same declarative test() harness as resume_qa.py to verify the engine
in isolation (no network, no LLM). Run from the engine root:

    python scripts/selftest.py

Exit 0 = all green, 1 = a failure. Covers:
  - workspace resolution + ensure/validate against a temp workspace
  - resume_qa fabrication detection (the critical safety gate)
  - resume_qa clean-pass path
  - jobfile extraction (markers + Top-5 keyword parsing)
  - no-personal-data audit of the engine
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
SCRIPTS = ENGINE / "scripts"

_results = []


def test(name, fn):
    try:
        passed, detail = fn()
        status = "PASS" if passed else "FAIL"
    except Exception as ex:
        passed, status, detail = False, "ERROR", repr(ex)
    _results.append((status, name, detail or ""))
    icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "ERROR": "[ERR ]"}[status]
    print(f"  {icon} {name}" + (f"  ->  {detail}" if status != "PASS" and detail else ""))
    return passed


def run_qa(workspace, job=None, mode="tailored"):
    env = dict(os.environ, JOB_SEARCH_WORKSPACE=str(workspace))
    cmd = [sys.executable, str(SCRIPTS / "resume_qa.py"), "--mode", mode]
    if job:
        cmd += ["--job", str(job)]
    return subprocess.run(cmd, env=env, capture_output=True, text=True)


PROFILE = """target_roles:
  - Senior Product Manager
search_keywords:
  - "Senior Product Manager"
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
"""

MASTER = """# Jane Doe
jane.doe@example.com | 555-123-4567 | Remote, USA

## Summary
Product manager with 8 years building SaaS platforms across billing, analytics, and
onboarding domains for both self-serve and enterprise customers.

## Skills
Roadmapping, Agile, Scrum, Jira, SQL, OKRs, product discovery, user research, data analysis

## Experience

### Senior Product Manager
Globex Corp | 2020-2025
- Grew activation rate by 35% by redesigning the onboarding flow with the growth team
- Led a team of 6 engineers delivering a usage-based billing platform end to end
- Shipped 12 major releases using Agile and OKRs across three quarters
- Partnered with sales and support to prioritize a quarterly roadmap from customer signals
- Ran weekly product discovery interviews to validate problems before committing engineering

### Product Manager
Initech | 2017-2020
- Launched a self-serve analytics dashboard adopted by 400 customers in the first year
- Reduced churn by 15% through lifecycle messaging and targeted in-app prompts
- Defined success metrics and instrumented event tracking with the data team
- Collaborated with design on a reusable component library that cut delivery time

## Education
MBA, State University
BS Computer Science, City College

## Certifications
Certified Scrum Master (CSM)
"""

RESUME_BODY = """# Jane Doe
jane.doe@example.com | 555-123-4567 | Remote, USA

## Summary
Senior Product Manager with 8 years building SaaS platforms, driving experimentation and
A/B testing to improve retention and inform pricing strategy and GTM decisions across billing,
analytics, and onboarding domains for self-serve and enterprise customers.

## Skills
Roadmapping, Agile, Scrum, Jira, SQL, OKRs, product discovery, user research, data analysis, experimentation, A/B testing

## Experience

### Senior Product Manager
Globex Corp | 2020-2025
- Grew activation rate by 35% by redesigning the onboarding flow, validated through A/B testing
- Led a team of 6 engineers delivering a usage-based billing platform with pricing strategy inputs
- Shipped 12 major releases using Agile and OKRs across three quarters
- Partnered with sales and support to prioritize a quarterly roadmap from customer signals
- Ran weekly product discovery interviews to validate problems before committing engineering

### Product Manager
Initech | 2017-2020
- Launched a self-serve analytics dashboard adopted by 400 customers as part of GTM
- Reduced churn by 15% through lifecycle messaging and retention experimentation
- Defined success metrics and instrumented event tracking with the data team
- Collaborated with design on a reusable component library that cut delivery time

## Education
MBA, State University
BS Computer Science, City College

## Certifications
Certified Scrum Master (CSM)
"""


def job_file(resume_body):
    return f"""---
company: "Northwind"
role: "Senior Product Manager"
---

# Northwind — Senior Product Manager

## Evaluation
**Grade: A (84/100)**
**Top 5 Missing Keywords:** experimentation, A/B testing, pricing strategy, GTM, retention

## Tailored Resume
<!-- RESUME:START -->
{resume_body}
<!-- RESUME:END -->

## Cover Letter
Dear Hiring Manager, ...
"""


def main():
    print("Engine self-test\n")
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"

        # workspace ensure + paths
        env = dict(os.environ, JOB_SEARCH_WORKSPACE=str(ws))
        subprocess.run([sys.executable, str(SCRIPTS / "workspace.py"), "ensure"],
                       env=env, capture_output=True, text=True)
        test("workspace ensure creates config/profile.yaml",
             lambda: ((ws / "config" / "profile.yaml").exists(), None))
        val = subprocess.run([sys.executable, str(SCRIPTS / "workspace.py"), "validate"],
                             env=env, capture_output=True, text=True)
        test("validate fails on a fresh (placeholder) workspace",
             lambda: (val.returncode == 1, f"exit={val.returncode}"))

        # populate profile + master + job files
        (ws / "config" / "profile.yaml").write_text(PROFILE, encoding="utf-8")
        (ws / "config" / "resume.md").write_text(MASTER, encoding="utf-8")
        clean = ws / "data" / "jobs" / "clean.md"
        clean.write_text(job_file(RESUME_BODY), encoding="utf-8")
        fab = ws / "data" / "jobs" / "fab.md"
        fab.write_text(job_file(
            RESUME_BODY.replace("Globex Corp | 2020-2025", "Stark Industries | 2019-2025")
                       .replace("activation rate by 35%", "activation rate by 99%")
        ), encoding="utf-8")

        # validate now passes
        val2 = subprocess.run([sys.executable, str(SCRIPTS / "workspace.py"), "validate"],
                              env=env, capture_output=True, text=True)
        test("validate passes once profile+resume are real",
             lambda: (val2.returncode == 0, f"exit={val2.returncode}"))

        # clean tailored resume passes
        r_clean = run_qa(ws, clean)
        test("QA passes a faithful tailored resume (exit 0)",
             lambda: (r_clean.returncode == 0, f"exit={r_clean.returncode}"))

        # regression: a pipe-delimited Skills line must NOT be mistaken for
        # company/date lines, and a custom (but valid) resume section must NOT
        # be flagged as a non-resume header. Both surfaced on a real resume.
        pipe_body = RESUME_BODY.replace(
            "Roadmapping, Agile, Scrum, Jira, SQL, OKRs, product discovery, user research, data analysis, experimentation, A/B testing",
            "Roadmapping | Agile | Scrum | Jira | SQL | OKRs | product discovery | data analysis | experimentation | A/B testing",
        ) + "\n\n## Technical Projects\n- Built data analysis tooling with the data team\n"
        pipe = ws / "data" / "jobs" / "pipe.md"
        pipe.write_text(job_file(pipe_body), encoding="utf-8")
        r_pipe = run_qa(ws, pipe)
        test("QA tolerates pipe-delimited skills + a custom section (exit 0)",
             lambda: (r_pipe.returncode == 0, f"exit={r_pipe.returncode}\n{r_pipe.stdout}"))

        # fabricated resume is blocked
        r_fab = run_qa(ws, fab)
        test("QA blocks a fabricated employer+metric (exit 1)",
             lambda: (r_fab.returncode == 1, f"exit={r_fab.returncode}"))
        test("QA names the fabricated company in its output",
             lambda: ("Stark Industries" in r_fab.stdout, None))

        # master health is advisory (exit 0)
        r_master = run_qa(ws, mode="master")
        test("master-mode QA is advisory (exit 0)",
             lambda: (r_master.returncode == 0, f"exit={r_master.returncode}"))

    # jobfile keyword parsing (no markdown bleakage)
    sys.path.insert(0, str(SCRIPTS))
    import jobfile
    kws = jobfile.top5_missing_keywords(job_file(RESUME_BODY))
    test("Top-5 keyword parser strips markdown bold",
         lambda: (kws[:2] == ["experimentation", "A/B testing"], str(kws)))
    test("jobfile extracts resume between markers",
         lambda: (jobfile.tailored_resume(job_file(RESUME_BODY)).startswith("# Jane Doe"), None))

    # search_planner: deterministic, deduped, ToS-safe query planning
    import search_planner
    planner_profile = {
        "search_keywords": ["Senior Product Manager", "AI Product Manager"],
        "location": {"city": "Austin", "state": "TX", "remote": True},
        "work_model": ["remote", "hybrid"],
    }
    q1 = search_planner.build_queries(planner_profile)
    q2 = search_planner.build_queries(planner_profile)
    test("search_planner is deterministic across runs",
         lambda: ([q.query for q in q1] == [q.query for q in q2], None))
    test("search_planner produces no duplicate queries",
         lambda: (len({q.query for q in q1}) == len(q1), f"{len(q1)} queries"))
    # Per-intent coverage: every default board must appear within the remote intent
    # alone (a subset check across all intents could mask a per-intent regression).
    _default_boards = {b[0] for b in search_planner.DEFAULT_BOARDS}
    _remote_boards = {q.board for q in q1 if q.kind == "remote"}
    test("search_planner covers all default ATS boards within a single intent",
         lambda: (_default_boards <= _remote_boards, str(sorted(_remote_boards))))
    test("search_planner emits remote-intent queries when remote is true",
         lambda: (any(q.kind == "remote" for q in q1), None))
    # No query may contain a bare ` OR ` (unparenthesized OR breaks site: scoping)
    test("search_planner emits no unparenthesized OR queries",
         lambda: (all(" OR " not in q.query for q in q1), None))
    # A non-string keyword (e.g. an all-digit token coerced to int) must not crash
    test("search_planner tolerates non-string keywords",
         lambda: (len(search_planner.build_queries({"search_keywords": [2024, "PM"]})) > 0, None))
    # fallback YAML-subset parser reads the fixed schema without PyYAML
    parsed = search_planner._parse_profile_subset(PROFILE)
    test("search_planner fallback parser extracts search_keywords",
         lambda: (parsed.get("search_keywords") == ["Senior Product Manager"], str(parsed.get("search_keywords"))))
    test("search_planner fallback parser reads nested location.remote bool",
         lambda: (parsed.get("location", {}).get("remote") is True, str(parsed.get("location"))))
    # nested lists under a map key (domain.*) must survive, and quoted numerics
    # (e.g. a ZIP with a leading zero) must stay strings — both regressions fixed.
    nested = search_planner._parse_profile_subset(
        'domain:\n  prefer:\n    - AI\n    - SaaS\n  avoid:\n    - Adtech\n'
        'location:\n  zip: "00501"\n  remote: true\n')
    test("search_planner fallback parser keeps nested lists under a map",
         lambda: (nested.get("domain", {}).get("prefer") == ["AI", "SaaS"], str(nested.get("domain"))))
    test("search_planner fallback parser keeps quoted numerics as strings",
         lambda: (nested.get("location", {}).get("zip") == "00501", str(nested.get("location"))))
    # sponsorship intent only appears when needs_sponsorship is true
    sponsored = search_planner.build_queries(
        {**planner_profile, "work_authorization": {"needs_sponsorship": True}})
    test("search_planner adds visa-sponsorship intent only when needed",
         lambda: (all("visa sponsorship" not in q.query for q in q1) and
                  any("visa sponsorship" in q.query for q in sponsored), None))

    # no-personal-data audit of the engine. The shippable engine must contain no
    # real user data, so we scan for generic PII shapes (an email address, an
    # absolute home path) rather than any one person's specifics. A private fork
    # can add its own via JOB_SEARCH_PII_NEEDLES (comma-separated regexes).
    leaks = []
    default_needles = [
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # any email address
        r"/Users/[A-Za-z0-9._-]+/",                          # an absolute home path
    ]
    extra = os.environ.get("JOB_SEARCH_PII_NEEDLES", "")
    needles = default_needles + [n for n in (s.strip() for s in extra.split(",")) if n]
    scanned = list((ENGINE / "skills").rglob("*.md")) + \
        list((ENGINE / "references").rglob("*.md")) + \
        [p for p in (ENGINE / "scripts").glob("*.py") if p.name != "selftest.py"]
    for path in scanned:
        text = path.read_text(encoding="utf-8")
        for n in needles:
            if re.search(n, text, re.IGNORECASE):
                leaks.append(f"{path.name}:{n}")
    test("no personal data leaked into the engine",
         lambda: (not leaks, "; ".join(leaks)))

    failed = [r for r in _results if r[0] != "PASS"]
    print("\n" + "=" * 56)
    print(f"  {'ALL PASS' if not failed else 'FAILURES'}: "
          f"{len(_results) - len(failed)}/{len(_results)} passed")
    print("=" * 56)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
