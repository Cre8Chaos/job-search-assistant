# js-assess Career Assessment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional career-assessment module (`js-assess`) that writes a validated `config/career-profile.yaml` + adjacent-paths report, and wire it additively into sourcing, scoring, and tailoring.

**Architecture:** Engine/workspace split is preserved: skill + question guide + schema reference + validator live in the engine (zero personal data); the profile and report live in the workspace. All consumers treat a missing/placeholder/malformed profile as absent. The deterministic test harness is `scripts/selftest.py` (the project's convention — not pytest).

**Tech Stack:** Python 3 stdlib only (PyYAML optional, via `search_planner.load_profile`), Claude Code skills (markdown).

**Spec:** `docs/superpowers/specs/2026-07-23-js-assess-career-assessment-design.md`

## Global Constraints

- Stdlib only; PyYAML is optional. **The YAML schema must stay inside the fallback parser's subset** (`search_planner._parse_profile_subset`): top-level scalars/lists, one level of nested map, lists nested under a map key. **No lists of maps** — the spec's example is updated in Task 1 to map-shaped `strengths`/`transferable_skills`.
- Never auto-apply; never fabricate. The career profile is NEVER a source of resume facts (resume_qa L1 gate still applies).
- Engine contains zero personal data (selftest PII audit scans all new files automatically).
- All user files resolved via `scripts/workspace.py` — never hardcode a path.
- Career profile is OPTIONAL: absent/placeholder/malformed must never break or change existing behavior; rubric weights and A–F bands unchanged.
- Validator exit codes follow `resume_qa.py`: 0 = ok, 1 = blocking fail, 2 = config error.
- Run all commands from the engine root: `/Users/michaelgrapentin/Projects/Cre8-Your-Life/job-search-assistant`.
- Commit format `<type>: <description>` (feat/fix/refactor/docs/test/chore); no attribution footer.

---

### Task 1: Workspace seam + template placeholder + schema reference

**Files:**
- Modify: `scripts/workspace.py:50-74` (paths + ensure)
- Create: `workspace-template/config/career-profile.yaml`
- Create: `references/career-profile-schema.md`
- Modify: `scripts/selftest.py` (two tests in the first temp-workspace block)
- Modify: `docs/superpowers/specs/2026-07-23-js-assess-career-assessment-design.md` (sync YAML example)

**Interfaces:**
- Produces: `workspace.paths()` keys `"career_profile"` (→ `<ws>/config/career-profile.yaml`) and `"reports_dir"` (→ `<ws>/output/reports`); `ensure()` backfills `output/reports`. Task 2's validator and Task 3's planner read the `career_profile` path; Task 4's skill writes the report into `reports_dir`.

- [ ] **Step 1: Add failing selftest checks**

In `scripts/selftest.py`, inside the first `tempfile.TemporaryDirectory()` block, directly after the `test("workspace ensure creates config/profile.yaml", ...)` call, insert:

```python
        pj = subprocess.run([sys.executable, str(SCRIPTS / "workspace.py"), "paths"],
                            env=env, capture_output=True, text=True)
        test("workspace paths exposes career_profile and reports_dir",
             lambda: ("career_profile" in pj.stdout and "reports_dir" in pj.stdout, None))
        test("workspace ensure creates the career-profile placeholder",
             lambda: ((ws / "config" / "career-profile.yaml").exists(), None))
```

- [ ] **Step 2: Run selftest to verify the new checks fail**

Run: `python3 scripts/selftest.py`
Expected: the two new checks print `[FAIL]`; exit code 1. All pre-existing checks still PASS.

- [ ] **Step 3: Implement workspace changes**

In `scripts/workspace.py`, `paths()` — replace the return dict with:

```python
    return {
        "root": str(root),
        "profile": str(root / "config" / "profile.yaml"),
        "career_profile": str(root / "config" / "career-profile.yaml"),
        "resume": str(root / "config" / "resume.md"),
        "pipeline": str(root / "data" / "pipeline.md"),
        "jobs_dir": str(root / "data" / "jobs"),
        "pdf_dir": str(root / "output" / "pdfs"),
        "reports_dir": str(root / "output" / "reports"),
    }
```

In `ensure()`, extend the backfill tuple:

```python
        for sub in ("config", "data/jobs", "output/pdfs", "output/reports"):
```

Do NOT change `validate()` — the career profile is optional and must not gate setup. Add this comment above `validate()`:

```python
# NOTE: config/career-profile.yaml is intentionally NOT validated here — it is
# optional (js-assess). Consumers treat placeholder/missing as absent.
```

- [ ] **Step 4: Create the template placeholder**

Create `workspace-template/config/career-profile.yaml`:

```yaml
<!-- PLACEHOLDER: this file is filled in by the career assessment (js-assess skill).
     Optional — every other skill works without it. Say "assess my career" to create it.
     The schema and an example live in references/career-profile-schema.md. -->
```

- [ ] **Step 5: Create the schema reference**

Create `references/career-profile-schema.md`:

````markdown
# career-profile.yaml — Schema

Written by the `js-assess` skill into the workspace at the `career_profile` path
from `scripts/workspace.py paths`. **Optional** — every skill and script treats a
missing or placeholder file as absent. Validated by `scripts/career_profile_qa.py`
(blocking for js-assess; soft/no-op for consumers).

**Parser constraint (hard):** the file must stay inside the engine's no-PyYAML
fallback parser subset — top-level scalars and lists, one level of nested map,
lists nested under a map key. **No lists of maps.** That is why `strengths` and
`transferable_skills` are maps (name → text), not lists of objects. Quote dates
and any free text containing `:` or `#`.

## Example

```yaml
version: 1                       # schema version — must be 1
assessed: "2026-07-23"           # date of this assessment, quoted YYYY-MM-DD
history:                         # every assessment date, append-only
  - "2026-07-23"
strengths:                       # 3-6 entries: kebab-case name -> one-line evidence story
  systems-thinking: "Mapped the whole claims intake flow before rebuilding it"
  cross-team-translation: "Bridged engineering and underwriting on the pricing rollout"
work_style:
  autonomy: high                 # high | medium | low
  depth_vs_breadth: breadth      # depth | breadth | both
  collaboration: cross-functional  # solo | small-team | cross-functional
motivators:                      # ranked, from the fixed vocabulary below
  - mastery
  - income
  - mission
transferable_skills:             # skill -> where it comes from
  stakeholder management: "insurance product delivery"
risk:
  appetite: medium               # low | medium | high
  notes: "open to Series B+, not pre-seed"
adjacent_titles:                 # real, searchable job titles — feeds js-find-jobs
  - "Solutions Consultant"
  - "Technical Program Manager"
trajectory_signals:              # feeds the Career Trajectory dimension in scoring
  moving_toward:
    - "AI-adjacent delivery leadership"
  moving_away_from:
    - "pure people management"
```

## Field rules

| Field | Required | Rule |
|---|---|---|
| `version` | yes | Integer `1`. |
| `assessed` | yes | Quoted `YYYY-MM-DD`. |
| `history` | no | List of quoted dates, append-only across re-runs. |
| `strengths` | yes | Map, 3–6 entries; each value is a one-line evidence story (warn if empty). |
| `work_style` | yes | All three keys, values from the enums above. |
| `motivators` | yes | Non-empty ranked list; vocabulary: `mastery`, `income`, `mission`, `autonomy`, `status`, `stability`, `impact`, `learning`. No duplicates. |
| `transferable_skills` | no | Map: skill → origin. |
| `risk` | no | `appetite` from `low`/`medium`/`high` (warn otherwise); `notes` free text. |
| `adjacent_titles` | yes | Non-empty list of non-empty strings; concrete searchable titles. |
| `trajectory_signals` | yes | `moving_toward` non-empty list of strings; `moving_away_from` a list (may be empty). |

Free text lives only in strength/skill values and `risk.notes`. A future web quiz
(Phase 3) emits this same file — the file format is the seam, not the interview.
````

- [ ] **Step 6: Sync the spec's YAML example**

In `docs/superpowers/specs/2026-07-23-js-assess-career-assessment-design.md`, replace the fenced YAML example under `## Data: career-profile.yaml` with the example from Step 5 (map-shaped `strengths`/`transferable_skills`, quoted dates), and add below the fence:

```markdown
> Shape note (locked at implementation): `strengths` and `transferable_skills` are
> maps (name → text), not lists of objects, so the file stays inside the engine's
> no-PyYAML fallback-parser subset. See `references/career-profile-schema.md`.
```

- [ ] **Step 7: Run selftest to verify all checks pass**

Run: `python3 scripts/selftest.py`
Expected: `ALL PASS`, exit 0 (the PII audit also scans the two new files — generic content, must pass).

- [ ] **Step 8: Commit**

```bash
git add scripts/workspace.py workspace-template/config/career-profile.yaml references/career-profile-schema.md scripts/selftest.py docs/superpowers/specs/2026-07-23-js-assess-career-assessment-design.md
git commit -m "feat: workspace seam + schema for optional career profile"
```

---

### Task 2: career_profile_qa.py validator + soft consumer

**Files:**
- Create: `scripts/career_profile_qa.py`
- Modify: `scripts/selftest.py` (helper + new test block)

**Interfaces:**
- Consumes: `workspace.paths()["career_profile"]`, `workspace._is_placeholder(Path)`, `search_planner.load_profile(Path) -> dict` (all existing).
- Produces: CLI `python scripts/career_profile_qa.py [--profile PATH]` with exit codes 0/1/2; function `consume_adjacent_titles(path: Path | str) -> tuple[list[str], str | None]` — `(titles, warning)`, never raises; returns `([], None)` for missing/placeholder, `([], "<warning>")` for malformed. Task 3's planner CLI calls it.

- [ ] **Step 1: Add failing selftest block**

In `scripts/selftest.py`, add this helper directly after the `run_qa` function:

```python
def run_cp_qa(workspace_dir, profile=None):
    env = dict(os.environ, JOB_SEARCH_WORKSPACE=str(workspace_dir))
    cmd = [sys.executable, str(SCRIPTS / "career_profile_qa.py")]
    if profile:
        cmd += ["--profile", str(profile)]
    return subprocess.run(cmd, env=env, capture_output=True, text=True)
```

Add this module-level constant directly after the `RESUME_BODY` string:

```python
VALID_CAREER = """version: 1
assessed: "2026-07-23"
history:
  - "2026-07-23"
strengths:
  systems-thinking: "Mapped the whole claims intake flow before rebuilding it"
work_style:
  autonomy: high
  depth_vs_breadth: breadth
  collaboration: cross-functional
motivators:
  - mastery
  - income
transferable_skills:
  stakeholder management: "insurance product delivery"
risk:
  appetite: medium
adjacent_titles:
  - "Solutions Consultant"
  - "Technical Program Manager"
trajectory_signals:
  moving_toward:
    - "AI-adjacent delivery leadership"
  moving_away_from:
    - "pure people management"
"""
```

In `main()`, insert after the sponsorship test (`"search_planner adds visa-sponsorship intent only when needed"`) and before the no-personal-data audit:

```python
    # career profile: strict validator gate + soft consumption
    import career_profile_qa
    with tempfile.TemporaryDirectory() as tmp2:
        ws2 = Path(tmp2) / "ws"
        env2 = dict(os.environ, JOB_SEARCH_WORKSPACE=str(ws2))
        subprocess.run([sys.executable, str(SCRIPTS / "workspace.py"), "ensure"],
                       env=env2, capture_output=True, text=True)
        cp = ws2 / "config" / "career-profile.yaml"

        r_ph = run_cp_qa(ws2)
        test("career QA exits 2 on a placeholder profile",
             lambda: (r_ph.returncode == 2, f"exit={r_ph.returncode}"))

        cp.write_text(VALID_CAREER, encoding="utf-8")
        r_ok = run_cp_qa(ws2)
        test("career QA passes a valid profile (exit 0)",
             lambda: (r_ok.returncode == 0, f"exit={r_ok.returncode}\n{r_ok.stdout}"))

        cp.write_text(VALID_CAREER.replace("- mastery", "- fame"), encoding="utf-8")
        r_voc = run_cp_qa(ws2)
        test("career QA blocks an unknown motivator (exit 1)",
             lambda: (r_voc.returncode == 1, f"exit={r_voc.returncode}"))

        cp.write_text(VALID_CAREER.replace("autonomy: high", "autonomy: extreme"),
                      encoding="utf-8")
        r_enum = run_cp_qa(ws2)
        test("career QA blocks an invalid work_style enum (exit 1)",
             lambda: (r_enum.returncode == 1, f"exit={r_enum.returncode}"))

        cp.write_text("version: 1\n", encoding="utf-8")
        r_missing = run_cp_qa(ws2)
        test("career QA blocks missing required keys (exit 1)",
             lambda: (r_missing.returncode == 1, f"exit={r_missing.returncode}"))

        # soft consumption — must never raise, never block the pipeline
        cp.write_text(VALID_CAREER, encoding="utf-8")
        t_ok, w_ok = career_profile_qa.consume_adjacent_titles(cp)
        test("consume_adjacent_titles returns titles from a valid profile",
             lambda: (t_ok == ["Solutions Consultant", "Technical Program Manager"]
                      and w_ok is None, str((t_ok, w_ok))))
        cp.write_text("adjacent_titles: {}\n", encoding="utf-8")
        t_bad, w_bad = career_profile_qa.consume_adjacent_titles(cp)
        test("consume_adjacent_titles degrades to [] + warning on a bad profile",
             lambda: (t_bad == [] and w_bad is not None, str((t_bad, w_bad))))
        t_no, w_no = career_profile_qa.consume_adjacent_titles(ws2 / "config" / "nope.yaml")
        test("consume_adjacent_titles is a clean no-op when the file is missing",
             lambda: (t_no == [] and w_no is None, None))
```

- [ ] **Step 2: Run selftest to verify the block fails**

Run: `python3 scripts/selftest.py`
Expected: `ModuleNotFoundError`-style `[ERR ]`/failures for the new career-profile checks (the module doesn't exist); pre-existing checks unaffected. Exit 1.

- [ ] **Step 3: Implement the validator**

Create `scripts/career_profile_qa.py`:

```python
#!/usr/bin/env python3
"""
career_profile_qa.py — Career profile QA gate
=============================================
Validates a workspace's config/career-profile.yaml (written by the js-assess
skill) the way resume_qa.py gates a tailored resume: declarative test() checks
and an exit code a calling skill can branch on.

The career profile is OPTIONAL. Pipeline consumers (search_planner, js-evaluate,
js-tailor) must treat a missing, placeholder, or malformed profile as absent —
that soft path is consume_adjacent_titles(). This CLI is the STRICT path that
js-assess runs immediately after writing the file.

Usage:
  python scripts/career_profile_qa.py                  # resolved workspace profile
  python scripts/career_profile_qa.py --profile path/to/career-profile.yaml

Exit codes:
  0 = no blocking failures
  1 = one or more BLOCKING checks failed (js-assess must fix before done)
  2 = configuration error (file missing or still a placeholder)
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search_planner
import workspace

SCHEMA_VERSION = 1
REQUIRED_KEYS = ("version", "assessed", "strengths", "work_style",
                 "motivators", "adjacent_titles", "trajectory_signals")
WORK_STYLE_ENUMS = {
    "autonomy": {"high", "medium", "low"},
    "depth_vs_breadth": {"depth", "breadth", "both"},
    "collaboration": {"solo", "small-team", "cross-functional"},
}
MOTIVATOR_VOCAB = {"mastery", "income", "mission", "autonomy",
                   "status", "stability", "impact", "learning"}
RISK_APPETITES = {"low", "medium", "high"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STALE_DAYS = 365

_results = []


def test(name, fn, blocking=True):
    """Run fn() -> (passed, detail). Same harness shape as resume_qa.py."""
    try:
        passed, detail = fn()
        status = "PASS" if passed else ("FAIL" if blocking else "WARN")
    except Exception as ex:
        passed, status, detail = False, "ERROR", str(ex)
    _results.append({"name": name, "status": status,
                     "detail": detail or "", "blocking": blocking})
    icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[warn]", "ERROR": "[ERR ]"}[status]
    suffix = f"  ->  {detail}" if (status != "PASS" and detail) else ""
    print(f"  {icon} {name}{suffix}")
    return passed


# ─── Soft consumer (for search_planner and skills — never raises) ──────────────

def consume_adjacent_titles(path) -> tuple[list[str], str | None]:
    """Best-effort (titles, warning) for pipeline consumers.

    Missing/placeholder file -> ([], None): a clean no-op, not worth a warning.
    Malformed file           -> ([], "<warning>"): warn once, proceed as absent.
    A bad career profile must NEVER break sourcing.
    """
    p = Path(path)
    try:
        if not p.exists() or workspace._is_placeholder(p):
            return [], None
        prof = search_planner.load_profile(p)
    except Exception as ex:
        return [], f"career-profile.yaml unreadable ({ex}) — continuing without it"
    titles = prof.get("adjacent_titles") if isinstance(prof, dict) else None
    if not isinstance(titles, list):
        return [], "career-profile.yaml has no adjacent_titles list — continuing without it"
    clean = [s for s in (str(t).strip() for t in titles) if s]
    if not clean:
        return [], "career-profile.yaml adjacent_titles is empty — continuing without it"
    return clean, None


# ─── Blocking checks ───────────────────────────────────────────────────────────

def check_blocking(profile: dict):
    def required_keys():
        missing = [k for k in REQUIRED_KEYS if k not in profile]
        if missing:
            return False, "missing required key(s): " + ", ".join(missing)
        return True, None

    def version_ok():
        if profile.get("version") != SCHEMA_VERSION:
            return False, f"version must be {SCHEMA_VERSION}, got {profile.get('version')!r}"
        return True, None

    def assessed_date():
        raw = str(profile.get("assessed", ""))
        if not DATE_RE.match(raw):
            return False, f'assessed must be a quoted YYYY-MM-DD date, got {raw!r}'
        return True, raw

    def work_style_enums():
        ws_block = profile.get("work_style")
        if not isinstance(ws_block, dict):
            return False, "work_style must be a map"
        bad = []
        for key, allowed in WORK_STYLE_ENUMS.items():
            val = ws_block.get(key)
            if val not in allowed:
                bad.append(f"{key}={val!r} (allowed: {', '.join(sorted(allowed))})")
        if bad:
            return False, "; ".join(bad)
        return True, None

    def motivators_vocab():
        mots = profile.get("motivators")
        if not isinstance(mots, list) or not mots:
            return False, "motivators must be a non-empty ranked list"
        unknown = [str(m) for m in mots if m not in MOTIVATOR_VOCAB]
        if unknown:
            return False, ("unknown motivator(s): " + ", ".join(unknown) +
                           " (vocabulary: " + ", ".join(sorted(MOTIVATOR_VOCAB)) + ")")
        if len(set(mots)) != len(mots):
            return False, "motivators contains duplicates"
        return True, None

    def adjacent_titles_ok():
        titles = profile.get("adjacent_titles")
        if not isinstance(titles, list) or not titles:
            return False, "adjacent_titles must be a non-empty list of job titles"
        empty = [t for t in titles if not str(t).strip()]
        if empty:
            return False, "adjacent_titles contains empty entries"
        return True, f"{len(titles)} title(s)"

    def trajectory_ok():
        sig = profile.get("trajectory_signals")
        if not isinstance(sig, dict):
            return False, "trajectory_signals must be a map"
        toward = sig.get("moving_toward")
        away = sig.get("moving_away_from")
        if not isinstance(toward, list) or not any(str(t).strip() for t in (toward or [])):
            return False, "trajectory_signals.moving_toward must be a non-empty list"
        if away is not None and not isinstance(away, list):
            return False, "trajectory_signals.moving_away_from must be a list when present"
        return True, None

    test("Required top-level keys present", required_keys)
    test("Schema version is supported", version_ok)
    test("Assessment date is YYYY-MM-DD", assessed_date)
    test("work_style values are from the fixed enums", work_style_enums)
    test("Motivators are from the fixed vocabulary", motivators_vocab)
    test("adjacent_titles is a non-empty title list", adjacent_titles_ok)
    test("trajectory_signals has a moving_toward direction", trajectory_ok)


# ─── Advisory checks (WARN-only) ───────────────────────────────────────────────

def check_advisory(profile: dict):
    def strengths_evidence():
        strengths = profile.get("strengths")
        if not isinstance(strengths, dict) or not strengths:
            return False, "strengths should be a map of 3-6 name -> evidence entries"
        thin = [k for k, v in strengths.items() if not str(v or "").strip()]
        if thin:
            return False, "strength(s) missing an evidence story: " + ", ".join(thin)
        return True, f"{len(strengths)} strength(s) with evidence"

    def risk_enum():
        risk = profile.get("risk")
        if not isinstance(risk, dict) or "appetite" not in risk:
            return True, "risk.appetite not set — optional"
        if risk.get("appetite") not in RISK_APPETITES:
            return False, f"risk.appetite {risk.get('appetite')!r} not in {sorted(RISK_APPETITES)}"
        return True, None

    def freshness():
        raw = str(profile.get("assessed", ""))
        if not DATE_RE.match(raw):
            return True, "skipped (assessed invalid — caught by the blocking check)"
        age = (datetime.date.today() - datetime.date.fromisoformat(raw)).days
        if age > STALE_DAYS:
            return False, f"assessment is {age} days old — consider re-running js-assess"
        return True, f"{age} day(s) old"

    test("Strengths carry evidence stories", strengths_evidence, blocking=False)
    test("risk.appetite uses a known value", risk_enum, blocking=False)
    test("Assessment is fresh (<= 12 months)", freshness, blocking=False)


# ─── Runner ────────────────────────────────────────────────────────────────────

def run(profile_path: str | None) -> int:
    path = Path(profile_path).expanduser() if profile_path \
        else Path(workspace.paths()["career_profile"])
    if not path.exists() or workspace._is_placeholder(path):
        print(f"Config error: no career profile at {path} — run the js-assess "
              "skill first", file=sys.stderr)
        return 2
    try:
        profile = search_planner.load_profile(path)
    except Exception as ex:
        print(f"Career profile QA  |  {path}")
        print(f"  [FAIL] File parses as YAML  ->  {ex}")
        return 1
    if not isinstance(profile, dict):
        print(f"Career profile QA  |  {path}")
        print("  [FAIL] File parses to a mapping  ->  top level is not a map")
        return 1

    print(f"\nCareer profile QA  |  {path}")
    print("\nBlocking checks")
    check_blocking(profile)
    print("\nAdvisory checks")
    check_advisory(profile)

    passed = sum(1 for r in _results if r["status"] == "PASS")
    warns = sum(1 for r in _results if r["status"] == "WARN")
    blocking_fail = [r for r in _results if r["status"] in ("FAIL", "ERROR") and r["blocking"]]
    total = len(_results)
    print("\n" + "=" * 60)
    if blocking_fail:
        print(f"  RESULT: BLOCKED — {len(blocking_fail)} blocking failure(s) "
              f"({passed}/{total} passed, {warns} warning(s))")
        print("  Fix the failures above, rewrite the profile, and re-run.")
        print("=" * 60)
        return 1
    print(f"  RESULT: OK — {passed}/{total} passed, {warns} warning(s), 0 blocking failures")
    print("=" * 60)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Career profile QA gate")
    ap.add_argument("--profile", help="path to career-profile.yaml "
                                      "(default: resolved workspace)")
    args = ap.parse_args()
    sys.exit(run(args.profile))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run selftest to verify all checks pass**

Run: `python3 scripts/selftest.py`
Expected: `ALL PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add scripts/career_profile_qa.py scripts/selftest.py
git commit -m "feat: career profile QA gate + soft consumer"
```

---

### Task 3: search_planner adjacent-titles integration

**Files:**
- Modify: `scripts/search_planner.py:63-79` (`build_queries`) and `:235-252` (`_main`)
- Modify: `scripts/selftest.py` (planner tests)

**Interfaces:**
- Consumes: `career_profile_qa.consume_adjacent_titles(path) -> (list[str], str | None)` (Task 2).
- Produces: `build_queries(profile, *, max_keywords=8, boards=DEFAULT_BOARDS, extra_titles=())` — adjacent titles appended after profile keywords, deduped, then the combined list is truncated to `max_keywords` (fills remaining budget, never extends it). CLI gains `--career-profile PATH` and prints any consumption warning to stderr.

- [ ] **Step 1: Add failing selftest checks**

In `scripts/selftest.py`, directly after the career-profile block added in Task 2, insert:

```python
    # planner honors adjacent titles, within the existing keyword cap
    qx = search_planner.build_queries(planner_profile, extra_titles=["Solutions Consultant"])
    test("search_planner includes adjacent titles in the plan",
         lambda: (any(q.keyword == "Solutions Consultant" for q in qx), None))
    qcap = search_planner.build_queries(
        {"search_keywords": [f"Role {i}" for i in range(8)], "location": {"remote": True}},
        extra_titles=["Extra Title"])
    test("search_planner never exceeds the keyword cap with adjacent titles",
         lambda: (all(q.keyword != "Extra Title" for q in qcap)
                  and len({q.keyword for q in qcap}) == 8, None))
    test("search_planner dedupes an adjacent title already in the keywords",
         lambda: (len({q.keyword for q in search_planner.build_queries(
             planner_profile, extra_titles=["Senior Product Manager"])}) == 2, None))
    test("search_planner without extra titles is byte-identical to before",
         lambda: ([q.query for q in search_planner.build_queries(planner_profile)] ==
                  [q.query for q in q1], None))
```

- [ ] **Step 2: Run selftest to verify the new checks fail**

Run: `python3 scripts/selftest.py`
Expected: the four new checks `[ERR ]` (unexpected keyword argument `extra_titles`); exit 1.

- [ ] **Step 3: Implement**

In `scripts/search_planner.py`, change the `build_queries` signature and keyword assembly:

```python
def build_queries(
    profile: dict,
    *,
    max_keywords: int = MAX_KEYWORDS_DEFAULT,
    boards: tuple[tuple[str, str], ...] = DEFAULT_BOARDS,
    extra_titles: tuple[str, ...] | list[str] = (),
) -> list[SearchQuery]:
```

Replace the keyword-list line

```python
    keywords = [s for s in (str(kw).strip() for kw in raw_keywords) if s][:max_keywords]
```

with:

```python
    keywords = [s for s in (str(kw).strip() for kw in raw_keywords) if s]
    # Adjacent titles (career profile) fill any remaining keyword budget — they
    # never extend the cap, so the search-count ceiling is unchanged.
    for title in extra_titles:
        t = str(title).strip()
        if t and t not in keywords:
            keywords.append(t)
    keywords = keywords[:max_keywords]
```

In `_main`, add the CLI flag after the existing `--max-keywords` argument:

```python
    parser.add_argument("--career-profile",
                        help="path to career-profile.yaml (default: resolved workspace; "
                             "missing/placeholder is a clean no-op)")
```

and replace the two lines

```python
    profile = load_profile(profile_path)
    queries = build_queries(profile, max_keywords=args.max_keywords)
```

with:

```python
    profile = load_profile(profile_path)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import career_profile_qa
    import workspace
    career_path = Path(args.career_profile).expanduser() if args.career_profile \
        else Path(workspace.paths()["career_profile"])
    extra_titles, warning = career_profile_qa.consume_adjacent_titles(career_path)
    if warning:
        print(f"warning: {warning}", file=sys.stderr)

    queries = build_queries(profile, max_keywords=args.max_keywords,
                            extra_titles=extra_titles)
```

- [ ] **Step 4: Run selftest to verify all checks pass**

Run: `python3 scripts/selftest.py`
Expected: `ALL PASS`, exit 0 (including the pre-existing determinism/dedup/cap checks, proving no behavior change without a profile).

- [ ] **Step 5: Smoke-test the CLI no-op path**

Run: `JOB_SEARCH_WORKSPACE=/tmp/js-assess-smoke python3 scripts/workspace.py ensure && JOB_SEARCH_WORKSPACE=/tmp/js-assess-smoke python3 scripts/search_planner.py --profile workspace-template/config/profile.yaml; rm -rf /tmp/js-assess-smoke`
Expected: queries print (or `0 queries planned` for the placeholder profile), **no warning line**, exit 0.

- [ ] **Step 6: Commit**

```bash
git add scripts/search_planner.py scripts/selftest.py
git commit -m "feat: search planner widens sourcing with career-profile adjacent titles"
```

---

### Task 4: Interview guide + js-assess skill

**Files:**
- Create: `references/assessment-questions.md`
- Create: `skills/js-assess/SKILL.md`

**Interfaces:**
- Consumes: `workspace.paths()` keys `career_profile`/`reports_dir` (Task 1); `career_profile_qa.py` CLI (Task 2); schema at `references/career-profile-schema.md` (Task 1).
- Produces: the `js-assess` skill that Task 5's router references by name.

- [ ] **Step 1: Create the interview guide**

Create `references/assessment-questions.md`:

```markdown
# Career Assessment Interview (js-assess)

Six rounds, ONE question at a time. Prefer concrete stories over self-ratings —
the skill synthesizes profile attributes FROM the stories; never ask the user to
label themselves with a score or an enum. Target 10–15 minutes total. Enums and
the motivator vocabulary are fixed in `references/career-profile-schema.md`.

## Round 1 — Strengths & energizers → `strengths`
- "Tell me about a piece of work from the last few years you're genuinely proud
  of. What was it, and what did YOU specifically do?"
- Follow-up: "What kind of task makes a workday fly by? What kind drains you
  even when it goes well?"
- Synthesize 3–6 kebab-case strengths, each with a one-line evidence story taken
  from their answer (their words, compressed).

## Round 2 — Work-style → `work_style`
- "Describe the best-run team or project you've been part of. What made it work
  for you — the structure, the people, the autonomy?"
- Probe until you can place all three enums (autonomy, depth_vs_breadth,
  collaboration). Infer from the story; confirm your inference in one line.

## Round 3 — Motivators & values → `motivators`
- "Imagine two offers: one pays 20% more, the other is work you'd brag about.
  Which wins, and why?" Then: "What would make you leave a good job?"
- Rank 3–5 motivators from the fixed vocabulary. Read the ranking back for
  confirmation before moving on.

## Round 4 — Transferable skills → `transferable_skills`
- If a real master resume exists, pre-seed: "From your resume I see X, Y, Z —
  which of these would transfer anywhere, and what's missing from that list?"
- Otherwise: "What skills would follow you to a completely different industry?"
- Capture skill → origin pairs, including skills NOT on the resume.

## Round 5 — Risk & constraints → `risk`
- "Would you join a 10-person startup for the right role? What about a
  slower-moving enterprise? Where's your line?"
- Set `appetite` (low/medium/high) + a notes line. Cross-check hard constraints
  against `config/profile.yaml` — this round does not replace intake; flag any
  contradiction to the user rather than silently overwriting either file.

## Round 6 — Growth direction → `trajectory_signals` + `adjacent_titles`
- "Three years from now, what are you doing more of — and what have you managed
  to stop doing?"
- Synthesize `moving_toward` / `moving_away_from`, then propose 2–5
  `adjacent_titles`: REAL, searchable job titles the user likely hasn't been
  searching, each justified by a strength or signal from earlier rounds.
  Confirm the title list explicitly — these directly widen job sourcing.
```

- [ ] **Step 2: Create the skill**

Create `skills/js-assess/SKILL.md`:

````markdown
---
name: js-assess
description: >
  Career assessment interview for the Job Search & Resume Assistant. Use when
  the user says "assess my career", "career assessment", "what else could I do",
  "help me figure out my direction", or asks for adjacent career paths. Runs a
  10-15 minute conversational assessment and writes config/career-profile.yaml
  plus an adjacent-paths report. Optional — every other skill works without it.
---

# Career Assessment

Produces the optional `config/career-profile.yaml` — it widens sourcing
(adjacent titles feed the search planner automatically), sharpens Career
Trajectory scoring, and gives tailoring honest strengths language. Interview
script: `references/assessment-questions.md`. Schema + fixed enums:
`references/career-profile-schema.md`.

## Steps
1. **Ensure the workspace exists** and learn its paths:
   ```bash
   python scripts/workspace.py ensure
   python scripts/workspace.py paths     # note career_profile and reports_dir
   ```
2. **Check for an existing real profile** at the `career_profile` path (real =
   exists and contains no `<!-- PLACEHOLDER` marker).
   - **Exists → re-assessment mode:** read it, run an abbreviated interview
     focused on what changed since `assessed`, then present a field-level diff
     (old → new) and get explicit approval before writing. Append today's date
     to `history` — never drop prior dates.
   - **Absent/placeholder → full interview.**
3. **Run the six rounds** from `references/assessment-questions.md`, one
   question at a time. Synthesize attributes from the user's stories — never
   ask them to self-label with a score or enum. If a real master resume exists
   (`config/resume.md`, not a placeholder), pre-seed Round 4 from it and
   confirm rather than re-collect.
4. **Present the draft profile** conversationally (strengths, work style,
   motivator ranking, adjacent titles, trajectory) and get approval.
   **Nothing is written before approval** — an abandoned interview must leave
   no partial file on disk.
5. **Write the profile** to the `career_profile` path, matching
   `references/career-profile-schema.md` exactly (quoted dates, fixed enums,
   maps — not lists of maps).
6. **Validate (blocking):**
   ```bash
   python scripts/career_profile_qa.py
   ```
   - **Exit 1** → fix the flagged fields, rewrite, re-run. Do not declare the
     assessment done until exit 0.
   - **Exit 2** → the file isn't where expected; re-check the path from step 1.
7. **Write the adjacent-paths report** to
   `<reports_dir>/adjacent-paths-<YYYY-MM-DD>.md`: 3–5 non-obvious career
   directions. For each: why it fits (grounded in the user's own interview
   answers), 2–3 concrete example job titles, and what would have to be true to
   pursue it. Honest, not flattering — a direction with a real gap names the gap.
8. **Confirm and hand off:** where both files are; that `js-find-jobs` now
   automatically includes the adjacent titles in sourcing; and offer to
   re-evaluate borderline (C-grade) jobs with `js-evaluate`, since trajectory
   scoring now has signals.

## Rules
- The career profile informs **framing and search only**. It is NEVER a source
  of resume facts — `config/resume.md` stays the only source of truth, and the
  resume QA gate still enforces that on every tailored resume.
- Don't invent preferences. Synthesize from answers, confirm before writing.
- Write only to workspace paths from `workspace.py paths`. Never touch the
  engine, never hardcode a path.
````

- [ ] **Step 3: Verify engine hygiene**

Run: `python3 scripts/selftest.py`
Expected: `ALL PASS` — specifically the `no personal data leaked into the engine` check, which now scans both new markdown files.

- [ ] **Step 4: Commit**

```bash
git add references/assessment-questions.md skills/js-assess/SKILL.md
git commit -m "feat: js-assess career assessment skill + interview guide"
```

---

### Task 5: Pipeline integration edits (rubric, sourcing, tailoring, router, docs)

**Files:**
- Modify: `references/scoring-rubric.md:149-154` (dimension 6)
- Modify: `skills/js-find-jobs/SKILL.md` (steps 1 and 3)
- Modify: `skills/js-tailor/SKILL.md` (step 2)
- Modify: `skills/job-search/SKILL.md` (menu + routing table)
- Modify: `CLAUDE.md` (engine skill/script tables + typical flow)

**Interfaces:**
- Consumes: skill name `js-assess` (Task 4), `career_profile_qa.py` (Task 2), planner behavior (Task 3).
- Produces: user-visible routing and scoring behavior; no code.

- [ ] **Step 1: Extend the Career Trajectory dimension**

In `references/scoring-rubric.md`, after the dimension-6 block ending `- 1–2: Step back in both`, append:

```markdown

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
```

- [ ] **Step 2: Surface adjacent titles in js-find-jobs**

In `skills/js-find-jobs/SKILL.md` step 1, after the sentence ending `when false/absent, sourcing is unchanged).`, append:

```markdown
   Also check for a career profile (`career_profile` path): when one exists, the
   query plan below automatically includes its `adjacent_titles`.
```

In step 3, after the sponsorship bullet (ending `verify each posting in step 6.`), add:

```markdown
   - The planner also appends `adjacent_titles` from `config/career-profile.yaml`
     when a real one exists (run the `js-assess` skill to create it). They fill
     remaining keyword budget — the ~15–20 searches/run cap is unchanged. A
     `warning:` line on stderr means the career profile was unreadable and was
     skipped; surface that to the user once, then proceed normally.
```

- [ ] **Step 3: Allow strengths framing in js-tailor**

In `skills/js-tailor/SKILL.md` step 2, after `No fabrication.`, append:

```markdown
   If the workspace has a real `config/career-profile.yaml`, you may draw
   phrasing from its strengths evidence for the summary and cover-letter voice —
   **framing only, never new facts**: every employer, date, metric, and claim
   must still trace to the master resume (the QA gate enforces this).
```

- [ ] **Step 4: Route from the umbrella skill**

In `skills/job-search/SKILL.md`, add to the menu block after the `review resume` line:

```
  • assess         — career assessment → adjacent paths & titles     (js-assess)
```

Add to the routing table after the `js-resume-review` row:

```markdown
| assess my career / career direction / what else could I do | `js-assess` |
```

- [ ] **Step 5: Update the engine CLAUDE.md**

In `CLAUDE.md` (engine root): add to the skills table after the `js-resume-review` row:

```markdown
| `js-assess` | Optional career assessment → `config/career-profile.yaml` + adjacent-paths report. |
```

Add to the scripts table after the `resume_qa.py` row:

```markdown
| `career_profile_qa.py` | QA gate for the optional career profile (strict for js-assess; soft consumer for the planner). |
```

Replace the Typical flow line with:

```markdown
`job-search` → (first run: `js-setup` → `js-resume-review`) → optional `js-assess` →
`js-find-jobs` → `js-evaluate` → `js-tailor` (A/B jobs) → `js-pipeline`.
```

- [ ] **Step 6: Verify + commit**

Run: `python3 scripts/selftest.py`
Expected: `ALL PASS` (PII audit covers the edited markdown).

```bash
git add references/scoring-rubric.md skills/js-find-jobs/SKILL.md skills/js-tailor/SKILL.md skills/job-search/SKILL.md CLAUDE.md
git commit -m "feat: wire career profile into scoring, sourcing, tailoring, and routing"
```

---

### Task 6: Release gate (lifecycle rule — MANDATORY)

**Files:**
- Modify: `/Users/michaelgrapentin/Projects/CLAUDE.md` (Current skills list — job-search-assistant entry)
- External: SkillSpector scan, umbrella `.skill` repackage, Notion SOP update

**Interfaces:**
- Consumes: everything above, committed.

- [ ] **Step 1: Full verification**

Run: `python3 scripts/selftest.py`
Expected: `ALL PASS`, exit 0. Paste the summary line as evidence.

- [ ] **Step 2: SkillSpector scan**

Run: `~/.local/bin/skillspector scan /Users/michaelgrapentin/Projects/Cre8-Your-Life/job-search-assistant/skills/js-assess --no-llm`
Expected: no CRITICAL/HIGH findings (persona-markdown false positives: read the flagged lines before dismissing).

- [ ] **Step 3: Repackage the umbrella skill**

First check how the packaged copy is laid out: `ls /Users/michaelgrapentin/Projects/skills/ | grep -i job`. Sync the engine's `skills/`, `references/`, `scripts/`, `workspace-template/` into that folder the same way the existing copy was made (diff first — do not clobber anything newer), then:

Run: `cd /Users/michaelgrapentin/Projects && python3 -m scripts.package_skill skills/<job-search folder name> skills/`
Expected: a rebuilt `.skill` file; note its path.

- [ ] **Step 4: Update the master CLAUDE.md skills list**

In `/Users/michaelgrapentin/Projects/CLAUDE.md`, extend the `job-search-assistant` bullet: after "tailors a resume + drafts a **cover letter** per job", insert:

```markdown
Includes an optional **career assessment** (`js-assess`): a 10-15 min interview → validated `career-profile.yaml` (adjacent titles auto-widen sourcing, trajectory signals sharpen scoring, strengths inform framing only) + an adjacent-paths report. Triggers add: "assess my career", "what else could I do".
```

- [ ] **Step 5: Update the Notion SOP entry**

In the SOPs & Build Library (https://www.notion.so/5357247630a24e3c897873bd573d2a4c), find the existing **job-search-assistant** row (do NOT create a duplicate). Update the description with the js-assess capability and triggers, and extend the page's **## Tool Integrations** section with how `career_profile_qa.py` gates the assessment and how the planner consumes adjacent titles. Requires the live Notion MCP session.

- [ ] **Step 6: Final commit**

```bash
cd /Users/michaelgrapentin/Projects/Cre8-Your-Life/job-search-assistant
git status   # confirm clean; commit any stragglers with type: chore
```
