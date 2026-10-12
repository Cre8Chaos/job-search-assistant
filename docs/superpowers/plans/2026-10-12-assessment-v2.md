# Assessment v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Constraints Gate (travel, relocation, onsite outside the radius) that caps a quoted conflict at F, give every career-profile field a named reader, and block drains or weaknesses from ever reaching a tailored resume or cover letter.

**Architecture:** Hard constraints live in `profile.yaml` (`travel` block), validated by `workspace.py validate` and applied by an instruction-driven gate in `references/scoring-rubric.md`. Soft fields live in `career-profile.yaml`, validated warn-only by `career_profile_qa.py`, and read by js-evaluate (Fit notes) and js-tailor (framing). Privacy is enforced in code by a new Layer 1 check in `resume_qa.py`.

**Tech Stack:** Python 3 standard library only (no PyYAML on this machine; `search_planner.load_profile` falls back to `_parse_profile_subset`). Markdown skills and references. Tests in `scripts/selftest.py` (its own `test(name, fn)` harness, not pytest).

**Spec:** `docs/superpowers/specs/2026-10-12-assessment-v2-design.md` (approved, commit `b2f133e`). Read it before starting any task.

## Global Constraints

- Engine holds zero personal data. No real names, towns, employers, or a real user's words in `skills/`, `references/`, `scripts/`, or `tests/`. Fixture location is Springfield, IL.
- Stdlib only. Do not add PyYAML or any dependency.
- Any profile without a `travel` block, and any career profile without the four new keys, must behave exactly as today. `selftest.py` must stay green with its existing assertions unchanged.
- Travel cutoff is per user (`travel.max_pct`). The example value everywhere is `25`. A figure equal to the cutoff passes; only a figure above it is a conflict.
- A Constraints Gate CONFLICT requires a quoted JD line. No quote, no F. Words without a number never produce an F.
- `drains` and `weaknesses` are PRIVATE: js-evaluate Fit notes and Interview Prep only.
- `career-profile.yaml` stays `version: 1`. New keys are optional and never blocking.
- No em dashes in any new text (house style).
- Run everything from the engine root: `cd /Users/michaelgrapentin/Projects/Cre8-Your-Life/job-search-assistant`.
- Commit after each task on `master`, conventional-commit messages, no attribution lines. Do not push.

## Review Focus

1. **A one-word weakness name** (e.g. `delegation`) would make the leak check fail any resume using that ordinary word. Expected: phrases shorter than two words are skipped and listed in a warning, never matched. Pinned in Task 3.
2. **A leak with different punctuation or casing** ("Long stretches of status-reporting.") must still be caught. Pinned in Task 3.
3. **A career profile that exists but has neither key**, or is malformed, must not crash resume QA or block a resume. Pinned in Task 3.
4. **`max_pct` written as a string** (`"25"`) or as `25.5`, or `relocation: "no"`: validate must name the problem, not crash and not pass silently. Pinned in Task 1.
5. **An old instruction left in place**: the rubric's "note only ... travel %" bullet would let a model skip the gate. Expected: that phrase is gone and a text check proves it. Pinned in Task 4.

---

### Task 1: `travel` block validation in `workspace.py`

**Files:**
- Modify: `scripts/workspace.py` (function `validate`, lines 89-101)
- Test: `scripts/selftest.py` (inside the first `with tempfile.TemporaryDirectory()` block, directly after the `"validate passes once profile+resume are real"` test)

**Interfaces:**
- Produces: `workspace.travel_problems(profile: dict) -> list[str]` (empty list = valid or absent). `validate()` appends these to its `problems`.

- [ ] **Step 1: Write the failing tests**

Add to `scripts/selftest.py`, directly after the `test("validate passes once profile+resume are real", ...)` call:

```python
        # travel block (assessment v2): absent = valid; malformed = validate exits 1
        def _validate_with(extra: str):
            (ws / "config" / "profile.yaml").write_text(PROFILE + extra, encoding="utf-8")
            return subprocess.run([sys.executable, str(SCRIPTS / "workspace.py"), "validate"],
                                  env=env, capture_output=True, text=True)

        v_ok = _validate_with("travel:\n  max_pct: 25\n  relocation: false\n")
        test("validate accepts a well-formed travel block",
             lambda: (v_ok.returncode == 0, f"exit={v_ok.returncode} {v_ok.stderr}"))
        v_hi = _validate_with("travel:\n  max_pct: 140\n  relocation: false\n")
        test("validate rejects travel.max_pct above 100",
             lambda: (v_hi.returncode == 1 and "max_pct" in v_hi.stderr,
                      f"exit={v_hi.returncode} {v_hi.stderr}"))
        v_str = _validate_with('travel:\n  max_pct: "25"\n  relocation: false\n')
        test("validate rejects a quoted (string) travel.max_pct",
             lambda: (v_str.returncode == 1 and "max_pct" in v_str.stderr,
                      f"exit={v_str.returncode} {v_str.stderr}"))
        v_flt = _validate_with("travel:\n  max_pct: 25.5\n  relocation: false\n")
        test("validate rejects a non-integer travel.max_pct",
             lambda: (v_flt.returncode == 1 and "max_pct" in v_flt.stderr,
                      f"exit={v_flt.returncode} {v_flt.stderr}"))
        v_rel = _validate_with('travel:\n  max_pct: 25\n  relocation: "no"\n')
        test("validate rejects a non-boolean travel.relocation",
             lambda: (v_rel.returncode == 1 and "relocation" in v_rel.stderr,
                      f"exit={v_rel.returncode} {v_rel.stderr}"))
        (ws / "config" / "profile.yaml").write_text(PROFILE, encoding="utf-8")  # restore
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 scripts/selftest.py 2>&1 | grep -E "travel|ALL PASS|FAILURES"`
Expected: the four "rejects" tests FAIL (validate currently ignores `travel`), "accepts" PASSES, summary shows `FAILURES`.

- [ ] **Step 3: Implement**

In `scripts/workspace.py`, add above `def validate`:

```python
def travel_problems(profile: dict) -> list[str]:
    """Problems with an optional travel block. Absent block = no problems."""
    if not isinstance(profile, dict) or "travel" not in profile:
        return []
    travel = profile.get("travel")
    if not isinstance(travel, dict):
        return ["travel must be a map with max_pct and relocation"]
    problems: list[str] = []
    pct = travel.get("max_pct")
    if isinstance(pct, bool) or not isinstance(pct, int) or not 0 <= pct <= 100:
        problems.append(f"travel.max_pct must be an unquoted integer 0-100, got {pct!r}")
    if not isinstance(travel.get("relocation"), bool):
        problems.append(f"travel.relocation must be true or false, got {travel.get('relocation')!r}")
    return problems
```

In `validate`, replace the profile-placeholder check with:

```python
    profile_path = Path(p["profile"])
    if _is_placeholder(profile_path):
        problems.append("profile.yaml missing or still a placeholder — run setup interview")
    else:
        import search_planner  # local import: keeps workspace.py import-light
        try:
            problems.extend(travel_problems(search_planner.load_profile(profile_path)))
        except Exception as ex:
            problems.append(f"profile.yaml unreadable ({ex})")
```

(The existing message string keeps its existing dash; do not edit unrelated text.)

- [ ] **Step 4: Run to verify they pass**

Run: `python3 scripts/selftest.py 2>&1 | tail -3`
Expected: `ALL PASS: 42/42 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/workspace.py scripts/selftest.py
git commit -m "feat: validate the optional travel block in workspace.py"
```

---

### Task 2: Warn-only validation of the four new career-profile keys

**Files:**
- Modify: `scripts/career_profile_qa.py` (`check_advisory`, lines 167-190)
- Test: `scripts/selftest.py` (inside the `tmp2` block, after `"career QA blocks missing required keys (exit 1)"`)

**Interfaces:**
- Consumes: nothing new.
- Produces: four advisory `test()` names, each starting `"New key"` (used by the selftest assertions below).

- [ ] **Step 1: Write the failing tests**

Add after `test("career QA blocks missing required keys (exit 1)", ...)`:

```python
        V2_KEYS = ('energizers:\n  - "untangling a messy process"\n'
                   'drains:\n  - "long stretches of status reporting"\n'
                   'weaknesses:\n  over-scoping: "says yes to too much at the start"\n'
                   'interests:\n  - "trail running"\n')
        cp.write_text(VALID_CAREER + V2_KEYS, encoding="utf-8")
        r_v2 = run_cp_qa(ws2)
        test("career QA passes a profile with all four v2 keys (exit 0)",
             lambda: (r_v2.returncode == 0 and r_v2.stdout.count("[PASS] New key") == 4,
                      f"exit={r_v2.returncode}\n{r_v2.stdout}"))
        cp.write_text(VALID_CAREER + 'drains: "not a list"\nweaknesses:\n  BadName: ""\n',
                      encoding="utf-8")
        r_v2bad = run_cp_qa(ws2)
        test("career QA only WARNS on malformed v2 keys (exit 0, 2 warnings)",
             lambda: (r_v2bad.returncode == 0 and r_v2bad.stdout.count("[warn] New key") == 2,
                      f"exit={r_v2bad.returncode}\n{r_v2bad.stdout}"))
        cp.write_text(VALID_CAREER, encoding="utf-8")
        r_v1 = run_cp_qa(ws2)
        test("career QA treats absent v2 keys as fine (v1 profile unchanged)",
             lambda: (r_v1.returncode == 0 and "[warn] New key" not in r_v1.stdout,
                      f"exit={r_v1.returncode}\n{r_v1.stdout}"))
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 scripts/selftest.py 2>&1 | grep -E "v2|ALL PASS|FAILURES"`
Expected: the first two FAIL (no "New key" lines yet), the v1 test PASSES.

- [ ] **Step 3: Implement**

In `scripts/career_profile_qa.py` add near the other constants:

```python
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
```

Inside `check_advisory`, before the three existing `test(...)` calls, add:

```python
    def string_list(key):
        def check():
            if key not in profile:
                return True, f"{key} not set (optional)"
            val = profile.get(key)
            if not isinstance(val, list) or not all(str(v or "").strip() for v in val):
                return False, f"{key} should be a list of non-empty strings"
            return True, f"{len(val)} entr(y/ies)"
        return check

    def weaknesses_map():
        if "weaknesses" not in profile:
            return True, "weaknesses not set (optional)"
        val = profile.get("weaknesses")
        if not isinstance(val, dict):
            return False, "weaknesses should be a map: kebab-case name -> description"
        bad = [k for k, v in val.items()
               if not KEBAB_RE.match(str(k)) or not str(v or "").strip()]
        if bad:
            return False, "weakness(es) need a kebab-case name and a description: " + ", ".join(map(str, bad))
        return True, f"{len(val)} weakness(es)"

    test("New key energizers is a string list", string_list("energizers"), blocking=False)
    test("New key drains is a string list (PRIVATE)", string_list("drains"), blocking=False)
    test("New key weaknesses is a kebab-name map (PRIVATE)", weaknesses_map, blocking=False)
    test("New key interests is a string list (context only)", string_list("interests"), blocking=False)
```

- [ ] **Step 4: Run to verify they pass**

Run: `python3 scripts/selftest.py 2>&1 | tail -3`
Expected: `ALL PASS: 45/45 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/career_profile_qa.py scripts/selftest.py
git commit -m "feat: warn-only validation of energizers, drains, weaknesses, interests"
```

---

### Task 3: Private-leak check in `resume_qa.py`

**Files:**
- Modify: `scripts/resume_qa.py` (imports; new functions after `layer1_fabrication`; `run()` tailored branch)
- Test: `scripts/selftest.py` (inside the first temp block, after the existing tailored-QA tests, before `master-mode QA is advisory`)

**Interfaces:**
- Consumes: `workspace.paths()["career_profile"]`, `search_planner.load_profile(Path) -> dict`, `jobfile.section(content, "Cover Letter") -> str | None`.
- Produces: `resume_qa.private_phrases(path) -> tuple[list[str], list[str]] | None` (None = skipped; else `(checkable_phrases, too_short_phrases)`), and blocking test name `"No private profile text (drains, weaknesses)"`.

- [ ] **Step 1: Write the failing tests**

Add in the first temp block after the fabricated-resume tests:

```python
        # private-leak check (assessment v2)
        cpath = ws / "config" / "career-profile.yaml"
        cpath.write_text(VALID_CAREER +
                         'drains:\n  - "long stretches of status reporting"\n'
                         'weaknesses:\n  over-scoping: "says yes to too much at the start"\n'
                         '  delegation: "holds onto work"\n', encoding="utf-8")
        anchor = "for self-serve and enterprise customers."
        leak_cases = {
            "drain phrase in the summary": job_file(RESUME_BODY.replace(
                anchor, anchor + " Avoids long stretches of status reporting.")),
            "weakness kebab name in the summary": job_file(RESUME_BODY.replace(
                anchor, anchor + " Known for over scoping.")),
            "punctuation/case near-miss": job_file(RESUME_BODY.replace(
                anchor, anchor + " LONG stretches of status-reporting!")),
            "drain phrase in the cover letter": job_file(RESUME_BODY).replace(
                "Dear Hiring Manager, ...", "Dear Hiring Manager, I avoid long stretches of status reporting."),
        }
        for label, body in leak_cases.items():
            jf = ws / "data" / "jobs" / f"leak-{abs(hash(label))}.md"
            jf.write_text(body, encoding="utf-8")
            r = run_qa(ws, jf)
            test(f"QA blocks a private-text leak: {label} (exit 1)",
                 lambda r=r: (r.returncode == 1 and "No private profile text" in r.stdout,
                              f"exit={r.returncode}\n{r.stdout[-400:]}"))
        r_short = run_qa(ws, clean)
        test("QA skips one-word weakness names instead of matching them (warns, exit 0)",
             lambda: (r_short.returncode == 0 and "too short to check: delegation" in r_short.stdout,
                      f"exit={r_short.returncode}\n{r_short.stdout[-400:]}"))
        cpath.write_text(VALID_CAREER, encoding="utf-8")
        r_nokeys = run_qa(ws, clean)
        test("QA skips the leak check when the profile has no private keys (exit 0)",
             lambda: (r_nokeys.returncode == 0 and "[skip] No private profile text" in r_nokeys.stdout,
                      f"exit={r_nokeys.returncode}"))
        cpath.write_text("this: [is: not: yaml\n", encoding="utf-8")
        r_bad = run_qa(ws, clean)
        test("QA does not crash or block on a malformed career profile (exit 0)",
             lambda: (r_bad.returncode == 0, f"exit={r_bad.returncode}\n{r_bad.stderr[-300:]}"))
        cpath.unlink()
        r_none = run_qa(ws, clean)
        test("QA skips the leak check when there is no career profile (exit 0)",
             lambda: (r_none.returncode == 0 and "[skip] No private profile text" in r_none.stdout,
                      f"exit={r_none.returncode}"))
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 scripts/selftest.py 2>&1 | grep -E "private|ALL PASS|FAILURES"`
Expected: the four leak tests, the one-word test and both skip tests FAIL. The malformed-profile test PASSES (the check doesn't exist yet).

- [ ] **Step 3: Implement**

In `scripts/resume_qa.py`, add `import search_planner` after `import jobfile`. After `layer1_fabrication`, add:

```python
# ─── Layer 1b — Private profile text (BLOCKING) ────────────────────────────────

MIN_PRIVATE_WORDS = 2  # a one-word phrase would match ordinary resume words


def _phrase_norm(s: str) -> str:
    s = str(s).lower().replace("-", " ")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def private_phrases(path) -> tuple[list[str], list[str]] | None:
    """(checkable, too_short) phrases from drains + weaknesses, or None to skip."""
    try:
        p = Path(path)
        if not p.exists() or workspace._is_placeholder(p):
            return None
        prof = search_planner.load_profile(p)
    except Exception:
        return None
    if not isinstance(prof, dict):
        return None
    raw: list[str] = []
    drains = prof.get("drains")
    if isinstance(drains, list):
        raw += [str(d) for d in drains]
    weak = prof.get("weaknesses")
    if isinstance(weak, dict):
        for name, desc in weak.items():
            raw += [str(name), str(desc)]
    phrases = [n for n in (_phrase_norm(r) for r in raw) if n]
    if not phrases:
        return None
    checkable = [ph for ph in phrases if len(ph.split()) >= MIN_PRIVATE_WORDS]
    too_short = [ph for ph in phrases if len(ph.split()) < MIN_PRIVATE_WORDS]
    return checkable, too_short


def layer1_private(texts: dict[str, str], phrases) -> None:
    name = "No private profile text (drains, weaknesses)"
    if phrases is None:
        print(f"  [skip] {name}  ->  no career profile drains or weaknesses")
        return
    checkable, too_short = phrases

    def no_leak():
        hits = []
        for label, text in texts.items():
            hay = f" {_phrase_norm(text or '')} "
            hits += [f"{label}: '{ph}'" for ph in checkable if f" {ph} " in hay]
        if hits:
            return False, "private profile text found in " + "; ".join(hits)
        return True, None

    test(name, 1, no_leak)
    if too_short:
        test("Private phrases long enough to check", 1,
             lambda: (False, "too short to check: " + ", ".join(too_short)), blocking=False)
```

In `run()`, tailored branch, inside `if only_layer in (None, 1):` right after `layer1_fabrication(tailored, master)`:

```python
            layer1_private(
                {"resume": tailored,
                 "cover letter": jobfile.section(content, "Cover Letter") or ""},
                private_phrases(p["career_profile"]))
```

- [ ] **Step 4: Run to verify they pass**

Run: `python3 scripts/selftest.py 2>&1 | tail -3`
Expected: `ALL PASS: 53/53 passed`

- [ ] **Step 5: Mutation proof**

Run:
```bash
cp scripts/resume_qa.py /tmp/resume_qa.py.keep
python3 - <<'EOF'
from pathlib import Path
p = Path("scripts/resume_qa.py"); t = p.read_text()
old = 'hits += [f"{label}: \'{ph}\'" for ph in checkable if f" {ph} " in hay]'
assert t.count(old) == 1, "mutant target not found exactly once"
p.write_text(t.replace(old, "pass"))
EOF
python3 scripts/selftest.py 2>&1 | grep -c "\[FAIL\] QA blocks a private-text leak"
cp /tmp/resume_qa.py.keep scripts/resume_qa.py
python3 scripts/selftest.py 2>&1 | tail -2
```
Expected: the count is `4` (every leak case goes red when the match is disabled), then the restored file is back to `ALL PASS: 53/53 passed`.

- [ ] **Step 6: Commit**

```bash
git add scripts/resume_qa.py scripts/selftest.py
git commit -m "feat: block drains and weaknesses from tailored resumes and cover letters"
```

---

### Task 4: Constraints Gate and Fit notes in the scoring rubric

**Files:**
- Modify: `references/scoring-rubric.md` (token list lines 8-12; new section after the Sponsorship Gate, before `## Company Intelligence`; Remote/Location note-only bullet at line 129; Output block)
- Test: `scripts/selftest.py` (new text checks, just before the no-personal-data audit)

**Interfaces:**
- Produces: rubric tokens `{{MAX_TRAVEL_PCT}}`, `{{RELOCATION_OK}}`; output lines starting `**Constraints Gate:**` and a `**Fit notes**` block. Task 5 refers to both by these exact names.

- [ ] **Step 1: Write the failing text checks**

Add before the `# no-personal-data audit` comment:

```python
    rubric = (ENGINE / "references" / "scoring-rubric.md").read_text(encoding="utf-8")
    gate = rubric.split("## Constraints Gate", 1)[1].split("\n## ", 1)[0] \
        if "## Constraints Gate" in rubric else ""
    test("rubric has a Constraints Gate section",
         lambda: (bool(gate), None))
    test("Constraints Gate states 'No quote, no F'",
         lambda: ("No quote, no F" in gate, None))
    test("Constraints Gate has travel, relocation and onsite-outside-radius checks",
         lambda: (all(s in gate for s in ("1. **Travel.**", "2. **Relocation.**",
                                          "3. **Onsite outside the radius.**")), None))
    test("Constraints Gate is dormant without a travel block",
         lambda: ("dormant" in gate and "travel" in gate, None))
    test("old 'note only ... travel %' instruction is gone from Remote/Location",
         lambda: ("and travel %" not in rubric, None))
    test("rubric Output carries the Constraints Gate line and Fit notes block",
         lambda: ("**Constraints Gate:**" in rubric and "**Fit notes**" in rubric, None))
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 scripts/selftest.py 2>&1 | grep -E "rubric|Constraints|ALL PASS|FAILURES"`
Expected: all six FAIL.

- [ ] **Step 3: Edit the rubric**

3a. Token list: change `` `{{NEEDS_SPONSORSHIP}}`, and the six `` to `` `{{NEEDS_SPONSORSHIP}}`, `{{MAX_TRAVEL_PCT}}`, `{{RELOCATION_OK}}`, and the six ``.

3b. Insert this section immediately before `## Company Intelligence`:

````markdown
## Constraints Gate (run BEFORE scoring, only if `profile.yaml` has a `travel` block)

**When `travel` is absent, the whole gate is dormant.** Write
`**Constraints Gate:** dormant (no travel block in profile.yaml)` and continue.

Fill `{{MAX_TRAVEL_PCT}}` from `travel.max_pct` and `{{RELOCATION_OK}}` from
`travel.relocation`. Read the JD body, not the location label (see "Score the JD
body, never the location label alone").

**No quote, no F.** A conflict needs an exact line from the JD body. Words without a
number never produce an F.

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
````

3c. In "3. Remote / Location", replace:

```
- **Note only (no score change):** required working hours/timezone and travel %.
  Capture them in the output so tailoring can address them.
```

with:

```
- **Note only (no score change):** required working hours/timezone. Capture them in
  the output so tailoring can address them. Travel is not scored here: the
  Constraints Gate (above) decides it.
```

3d. In the Output block, directly after the `**Sponsorship:**` line, add:

```
**Constraints Gate:** [PASS | CHECK: … | dormant (no travel block in profile.yaml)]
```

and directly before the `---` that precedes `**Interview Prep**`, add:

```
**Fit notes** *(never changes the grade; skip with "Fit notes: skipped, no career profile" when there is none)*
- Why it fits (up to 2): "[JD quote]" ↔ [motivators | work_style | energizers | transferable_skills]: [value]
- Watch out (up to 2, PRIVATE): "[JD quote]" ↔ [drains | weaknesses | work_style]: [value]. Ask: [one interview question]
- A line without both a JD quote and a field name is not written. If no line qualifies: "no JD line matched a profile field".
```

- [ ] **Step 4: Run to verify they pass**

Run: `python3 scripts/selftest.py 2>&1 | tail -3`
Expected: `ALL PASS: 59/59 passed`

- [ ] **Step 5: Commit**

```bash
git add references/scoring-rubric.md scripts/selftest.py
git commit -m "feat: Constraints Gate and Fit notes in the scoring rubric"
```

---

### Task 5: Skills and schema docs

**Files:**
- Modify: `skills/js-evaluate/SKILL.md` (Steps 1, 3, 6), `skills/js-tailor/SKILL.md` (around line 27), `skills/js-find-jobs/SKILL.md` (step 6), `skills/js-setup/SKILL.md` (intake list near line 28), `skills/js-assess/SKILL.md` (write step + re-assessment), `references/profile-schema.md`, `references/career-profile-schema.md`, `references/assessment-questions.md`
- Test: `scripts/selftest.py` (text checks, after Task 4's)

**Interfaces:**
- Consumes: rubric names from Task 4 (`Constraints Gate`, `Fit notes`, `{{MAX_TRAVEL_PCT}}`).

- [ ] **Step 1: Write the failing text checks**

```python
    sk = {n: (ENGINE / "skills" / n / "SKILL.md").read_text(encoding="utf-8")
          for n in ("js-evaluate", "js-tailor", "js-find-jobs", "js-setup", "js-assess")}
    cps = (ENGINE / "references" / "career-profile-schema.md").read_text(encoding="utf-8")
    pfs = (ENGINE / "references" / "profile-schema.md").read_text(encoding="utf-8")
    test("js-evaluate runs the Constraints Gate and writes Fit notes",
         lambda: ("Constraints Gate" in sk["js-evaluate"] and "Fit notes" in sk["js-evaluate"], None))
    test("js-tailor never reads drains, weaknesses or interests",
         lambda: ("Never read `drains`, `weaknesses`, or `interests`" in sk["js-tailor"], None))
    test("js-find-jobs pre-filter mirrors the Constraints Gate",
         lambda: ("constraints: conflict" in sk["js-find-jobs"], None))
    test("js-setup asks the travel question",
         lambda: ("travel.max_pct" in sk["js-setup"], None))
    test("js-assess writes the four v2 keys",
         lambda: (all(k in sk["js-assess"] for k in ("energizers", "drains", "weaknesses", "interests")), None))
    test("every schema row names its reader (Read by column)",
         lambda: ("| Read by |" in cps and "| Read by |" in pfs, None))
    test("schema marks drains and weaknesses PRIVATE",
         lambda: (cps.count("PRIVATE") >= 2, None))
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 scripts/selftest.py 2>&1 | grep -E "js-|schema|ALL PASS|FAILURES"`
Expected: all seven FAIL.

- [ ] **Step 3: Edit the skills**

3a. `skills/js-evaluate/SKILL.md`:
- Step 1: after reading `config/profile.yaml`, add: "Also read `config/career-profile.yaml` if present (optional; a missing or placeholder file means Fit notes are skipped)."
- Insert a new step after step 3:

```markdown
3.2. **Constraints Gate** (only if `profile.yaml` has a `travel` block; otherwise write
   `**Constraints Gate:** dormant (no travel block in profile.yaml)`): per
   `references/scoring-rubric.md` → "Constraints Gate". A travel figure above
   `travel.max_pct`, a relocation requirement when `travel.relocation` is false, or an
   explicit onsite requirement outside the radius **caps at F**, quoting the exact JD
   line. No quote, no F. Silence or vague wording is `CHECK: ...` with no penalty.
```

- Step 6: append to the list of what the Evaluation block contains: "the `**Constraints Gate:**` line, and the **Fit notes** block (Why it fits / Watch out, each line pairing a JD quote with a named career-profile field). Add each Watch-out question to Interview Prep's questions to ask. `drains` and `weaknesses` appear ONLY in Fit notes and Interview Prep."

3b. `skills/js-tailor/SKILL.md`, after the sentence about strengths evidence (line 27 area), add:

```markdown
   It may also use `transferable_skills` and `energizers` from the career profile for
   framing in the summary and cover letter: framing only, never a new fact, the same
   rule as `strengths`. Never read `drains`, `weaknesses`, or `interests`.
   `resume_qa.py` fails any resume or cover letter that contains them.
```

3c. `skills/js-find-jobs/SKILL.md` step 6, after the location-fit bullet, add:

```markdown
   - **If `profile.yaml` has a `travel` block:** apply the Constraints Gate's three
     checks (`references/scoring-rubric.md`). Drop a role with a quoted explicit
     conflict, or keep it flagged `constraints: conflict`. When unsure, keep and flag.
```

3d. `skills/js-setup/SKILL.md`, after the work-authorization intake item, add:

```markdown
   4. Travel and relocation → `travel.max_pct` (an integer percentage, e.g. 25) and
      `travel.relocation` (true/false). Ask: "What is the most travel you will accept,
      as a percentage, and would you relocate?" If the user skips it, omit the block
      (the Constraints Gate stays dormant).
```

(Renumber any following items in that list.)

3e. `skills/js-assess/SKILL.md`: in the step that writes the profile, add: "Write `energizers` and `drains` (round 1), `weaknesses` (round 5), and `interests` (round 6) when the user gave them, in the user's words. `drains` and `weaknesses` are PRIVATE." In the re-assessment section, add: "If `risk.notes` holds hard constraints (travel, relocation, commute), propose moving them to `profile.yaml`'s `travel` block one line at a time, and write only what the user approves."

- [ ] **Step 4: Edit the schema docs**

4a. `references/profile-schema.md`: add a `| Read by |` column to the field table, and a row:
`| travel.max_pct / .relocation | int / bool | Optional. Highest acceptable travel % and whether the user would relocate. Absent block = Constraints Gate dormant. | scoring-rubric Constraints Gate, js-find-jobs pre-filter, workspace.py validate |`
Fill Read by for every existing row (location/work_model → scoring-rubric Remote/Location and Constraints Gate; salary → Salary Fit; scoring_weights → scoring-rubric; domain → Tech & Domain and Domain-Expertise Gate; work_authorization → Sponsorship Gate; target_roles/search_keywords → search_planner.py). Add the `travel` block to the example YAML with `max_pct: 25` and `relocation: false`.

4b. `references/career-profile-schema.md`: add the four keys to the example (use the spec's generic values: "untangling a messy process", "long stretches of status reporting", `over-scoping`, "trail running"), add four rows to Field rules, and add a `| Read by |` column filled exactly as the spec's Read-by table. Replace the closing line "Free text lives only in strength/skill values and `risk.notes`." with "Free text lives in strength/skill values, `risk.notes`, and the four v2 keys. `drains` and `weaknesses` are PRIVATE: js-evaluate Fit notes and Interview Prep only."

4c. `references/assessment-questions.md`: in Round 1 add "Also capture `energizers` (what gives you energy) and `drains` (what takes it away, PRIVATE)". In Round 5 add "Also capture one or two `weaknesses` as kebab-name → description (PRIVATE), and route hard constraints to `profile.yaml`'s `travel` block, not `risk.notes`". In Round 6 add "Optionally capture `interests` outside work (context only)".

- [ ] **Step 5: Run to verify everything passes**

Run: `python3 scripts/selftest.py 2>&1 | tail -3`
Expected: `ALL PASS: 66/66 passed` (the no-personal-data audit is among them and must stay green).

- [ ] **Step 6: Commit**

```bash
git add skills references scripts/selftest.py
git commit -m "feat: wire the Constraints Gate, Fit notes and v2 keys into the skills and schemas"
```

---

### Task 6: Known-answer fixtures and a blind run of js-evaluate

**Files:**
- Create: `tests/fixtures/constraints/01-travel-30.md`, `02-relocation.md`, `03-onsite-outside-radius.md`, `04-travel-vague.md`, `05-remote-10.md`, `profile.yaml`, `EXPECTED.md`
- Create: `tests/run_constraints_blind.sh`

**Interfaces:**
- Consumes: `skills/js-evaluate/SKILL.md`, `references/scoring-rubric.md` from Tasks 4-5.

- [ ] **Step 1: Write the fixture profile** `tests/fixtures/constraints/profile.yaml`:

```yaml
target_roles:
  - Senior Product Manager
location:
  city: "Springfield"
  state: "IL"
  zip: ""
  radius_miles: 35
  remote: true
work_model:
  - remote
  - hybrid
travel:
  max_pct: 25
  relocation: false
```

- [ ] **Step 2: Write the five JDs.** Each is a short job description (title, company "Acme Analytics", 4-6 responsibility lines) containing exactly one deciding line:
  - `01-travel-30.md`: "Travel up to 30% for onsite customer workshops."
  - `02-relocation.md`: "Relocation to Chicago, IL is required within 60 days of start."
  - `03-onsite-outside-radius.md`: "This role works 3 days a week from our Chicago, IL office."
  - `04-travel-vague.md`: "Travel as required." (and nothing else about location beyond "Remote, US")
  - `05-remote-10.md`: "This is a fully remote role. Travel: up to 10%."

- [ ] **Step 3: Write `EXPECTED.md`** (never copied into the blind run):

```markdown
| Fixture | Constraints Gate | Grade capped at F? |
|---|---|---|
| 01-travel-30 | CONFLICT (travel), quotes "Travel up to 30%" | yes |
| 02-relocation | CONFLICT (relocation), quotes "Relocation to Chicago" | yes |
| 03-onsite-outside-radius | CONFLICT (onsite outside radius), quotes "3 days a week from our Chicago" | yes |
| 04-travel-vague | CHECK | no |
| 05-remote-10 | PASS | no |
```

- [ ] **Step 4: Write `tests/run_constraints_blind.sh`:**

```bash
#!/usr/bin/env bash
# Blind known-answer run: each fixture is graded in a fresh claude -p session that
# sees only the skill, the rubric, the profile and one JD. EXPECTED.md never goes in.
set -euo pipefail
ENGINE="$(cd "$(dirname "$0")/.." && pwd)"
FIX="$ENGINE/tests/fixtures/constraints"
OUT="$(mktemp -d)"
for jd in "$FIX"/0*.md; do
  name="$(basename "$jd" .md)"
  prompt="You are running the js-evaluate skill below. Apply ONLY its Constraints Gate step to the job description, using the profile. Print exactly one line starting with '**Constraints Gate:**' and, if it is a conflict, the grade line.

=== SKILL ===
$(cat "$ENGINE/skills/js-evaluate/SKILL.md")
=== RUBRIC ===
$(cat "$ENGINE/references/scoring-rubric.md")
=== profile.yaml ===
$(cat "$FIX/profile.yaml")
=== JOB DESCRIPTION ===
$(cat "$jd")"
  (cd "$OUT" && claude -p --tools "" "$prompt") > "$OUT/$name.out"
  echo "== $name"; grep -m2 -E 'Constraints Gate|Grade:' "$OUT/$name.out" || echo "NO GATE LINE"
done
echo "Raw outputs: $OUT"
```

Run `chmod +x tests/run_constraints_blind.sh`. If `claude -p` rejects `--tools ""` on this CLI version, drop the flag (the session still has no files besides the prompt, since it runs from an empty temp dir).

- [ ] **Step 5: Run it and grade by hand against EXPECTED.md**

Run: `bash tests/run_constraints_blind.sh`
Expected: 01-03 print `CONFLICT → F` with the quoted line, 04 prints `CHECK`, 05 prints `PASS`. Record the five lines verbatim in the commit body. Any mismatch is a rubric wording defect: fix the rubric text in Task 4's section, rerun all five, and do not change `EXPECTED.md` to match the output.

- [ ] **Step 6: Commit**

```bash
git add tests/
git commit -m "test: known-answer fixtures and blind run for the Constraints Gate"
```

---

### Task 7: Degradation proof, judge, lifecycle

**Files:** none new in the engine. Outputs: `Projects/skills/` packages, `Projects/CLAUDE.md`, Notion SOP row.

- [ ] **Step 1: Degradation proof** (read-only; changes nothing)

Run:
```bash
git diff --stat b2f133e..HEAD -- scripts/search_planner.py
python3 scripts/selftest.py 2>&1 | grep -E "byte-identical|ALL PASS|FAILURES"
```
Expected: the diff prints nothing (this plan never edits `search_planner.py`), then
`[PASS] search_planner without extra titles is byte-identical to before` and
`ALL PASS: 66/66 passed`. All 37 original test names are still present and passing,
because no task edits an existing assertion.

- [ ] **Step 2: Codex cross-check**

Run `/cross-check` and route Codex through `Projects/skills/cross-check/scripts/codex_judge.py` (never a hand-run `codex exec`). Bundle: the spec, this plan, and `git diff b2f133e..HEAD`. Fix any `block`/`revise` findings, re-run selftest, re-judge until `pass` or Michael calls it.

- [ ] **Step 3: Skill lifecycle (per Projects/CLAUDE.md)**

The engine ships as one umbrella package built from the copy at
`/Users/michaelgrapentin/Projects/skills/job-search-assistant/` (the same recipe the
2026-07-23 js-assess plan used):

```bash
~/.local/bin/skillspector scan /Users/michaelgrapentin/Projects/Cre8-Your-Life/job-search-assistant/skills --no-llm
diff -rq /Users/michaelgrapentin/Projects/Cre8-Your-Life/job-search-assistant/skills /Users/michaelgrapentin/Projects/skills/job-search-assistant/skills 2>&1 | head -40
```

Read every CRITICAL/HIGH finding's flagged lines before going on. Read the diff: if
the packaged copy has anything NEWER than the engine, stop and ask Michael. Otherwise
sync the engine's `skills/`, `references/`, `scripts/` and `workspace-template/` into
that folder with `rsync -a --exclude __pycache__` (one directory at a time, no
`--delete`), then:

```bash
cd /Users/michaelgrapentin/Projects && python3 -m scripts.package_skill skills/job-search-assistant skills/
ls -la skills/job-search-assistant.skill
```

Expected: a rebuilt `.skill` with today's timestamp. Then update the
`job-search-assistant` entry in `Projects/CLAUDE.md` Current skills (Constraints Gate,
Fit notes, Read-by schema, private-leak check), and update its existing Notion SOPs &
Build Library row (do not create a duplicate), including its Tool Integrations
section.

- [ ] **Step 4: Report** the final selftest count, the blind-run lines, the judge verdict, and what was not done (the Daily Driver port, by design).
