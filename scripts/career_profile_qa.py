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
