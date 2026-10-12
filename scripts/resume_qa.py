#!/usr/bin/env python3
"""
resume_qa.py — Resume QA gate (pre-delivery validator)
======================================================
A zero-dependency, local-file-only adaptation of the ScholarPath QA-agent
harness. It validates a resume the same way ScholarPath's qa_agent gated a
deploy: layered, declarative tests, an exit code a calling skill can branch on.

Two modes:
  --mode tailored  (default)  Validate a job file's tailored resume before it is
                              turned into a PDF or marked "ready to apply".
                              Layers: L1 fabrication, L2 ATS safety, L3 structure,
                              L4 keyword coverage (warn-only).
  --mode master               Health-check the master resume (config/resume.md).
                              Layer: L5 — all checks are advisory (never block).

Usage:
  python scripts/resume_qa.py --mode tailored --job data/jobs/<file>.md
  python scripts/resume_qa.py --mode master
  python scripts/resume_qa.py --mode tailored --job <file> --layer 1
  python scripts/resume_qa.py --mode tailored --job <file> --dry-run

Exit codes:
  0 = no blocking failures
  1 = one or more BLOCKING tests failed (do not deliver / do not render PDF)
  2 = configuration error (missing files, no resume found, etc.)

Resolves the master resume through workspace.py — never hardcodes a path.
"""
import argparse
import re
import sys
from pathlib import Path

import jobfile
import search_planner
import workspace

# ─── Harness (mirrors qa_agent.py: declarative test(), accumulating _results) ──

_results = []  # each: {layer, name, status, detail, blocking}


def test(name, layer, fn, blocking=True):
    """Run fn() -> (passed: bool, detail: str|None). Record + print the result."""
    try:
        passed, detail = fn()
        status = "PASS" if passed else ("FAIL" if blocking else "WARN")
    except Exception as ex:  # a check that errors is treated as a (blocking) error
        passed, status, detail = False, "ERROR", str(ex)
    _results.append({"layer": layer, "name": name, "status": status,
                     "detail": detail or "", "blocking": blocking})
    icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[warn]", "ERROR": "[ERR ]"}[status]
    suffix = f"  ->  {detail}" if (status != "PASS" and detail) else ""
    print(f"  {icon} {name}{suffix}")
    return passed


# ─── Text utilities ────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    """Lowercase, collapse whitespace, strip thousands separators for matching."""
    s = s.lower().replace(",", "")
    return re.sub(r"\s+", " ", s).strip()


def _headers(md: str) -> list[str]:
    return [m.strip() for m in re.findall(r"^##\s+(.+)$", md, re.MULTILINE)]


def _bullets(md: str) -> list[str]:
    return [m.strip() for m in re.findall(r"^\s*-\s+(.+)$", md, re.MULTILINE)]


# METRIC_RE — strict: only $ / % / multiplier tokens. Used by the Layer 1
# fabrication gate, where matching bare numbers (dates, team sizes) would cause
# false positives. A fabricated "99%" must trace to the master; a "2024" need not.
METRIC_RE = re.compile(r"\$\s?[\d,]+(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?%|\b\d+(?:\.\d+)?x\b")
# QUANT_RE — broad: any number counts a bullet as "quantified". Used only by the
# Layer 5 master-health quantification COUNT (e.g. "200 vendor hours", "9 contributors").
QUANT_RE = re.compile(r"\$\s?[\d,]+|\b\d[\d,]*%|\b\d+x\b|\b\d+\+?\b")
REQUIRED_RESUME_HEADERS = {"summary", "skills", "experience", "education"}
# Headers that belong to the JOB FILE, not a resume. If one of these shows up
# inside the extracted resume, the extraction or the markers are wrong. (Custom
# but legitimate resume sections like "Technical Projects" are NOT flagged —
# ATS parsers handle them fine; only tables/columns/images are real ATS risks.)
NON_RESUME_HEADERS = {
    "evaluation", "cover letter", "metadata", "full job description",
    "job description", "application status", "notes", "tailored resume",
    "interview prep", "hiring manager interview prep",
}


# ─── Layer 1 — Fabrication / fidelity (BLOCKING) ────────────────────────────────

def layer1_fabrication(tailored: str, master: str):
    nmaster = _norm(master)

    def titles_in_master():
        titles = re.findall(r"^###\s+(.+)$", tailored, re.MULTILINE)
        missing = [t for t in titles if _norm(t) not in nmaster]
        if missing:
            return False, "job titles not found in master resume: " + "; ".join(missing)
        return True, f"{len(titles)} job title(s) all trace to master"

    def companies_dates_in_master():
        # A company/date meta line is the first non-empty line AFTER a '### ' title
        # (format: '### Title' then 'Company | Dates'). This avoids mistaking a
        # pipe-delimited Skills line for employer/date text.
        lines = tailored.splitlines()
        metas = []
        for i, line in enumerate(lines):
            if line.strip().startswith("### "):
                for nxt in lines[i + 1:]:
                    if nxt.strip():
                        if "|" in nxt and "@" not in nxt:
                            metas.append(nxt.strip())
                        break
        problems = []
        for meta in metas:
            for piece in meta.split("|"):
                piece = piece.strip()
                if piece and _norm(piece) not in nmaster:
                    problems.append(piece)
        if problems:
            return False, "company/date text not found in master: " + "; ".join(problems[:6])
        return True, f"{len(metas)} company/date line(s) trace to master"

    def metrics_trace_to_master():
        bullet_text = " ".join(_bullets(tailored))
        bad = []
        for tok in METRIC_RE.findall(bullet_text):
            if _norm(tok) not in nmaster:
                bad.append(tok.strip())
        if bad:
            return False, "metrics not present in master (possible fabrication): " + ", ".join(sorted(set(bad)))
        return True, "all quantified metrics trace to master"

    test("Job titles trace to master resume", 1, titles_in_master)
    test("Company/date lines trace to master", 1, companies_dates_in_master)
    test("Quantified metrics trace to master", 1, metrics_trace_to_master)


# ─── Layer 1b — Private profile text (BLOCKING) ────────────────────────────────

MIN_PRIVATE_WORDS = 2  # a one-word phrase would match ordinary resume words


def _phrase_norm(s: str) -> str:
    s = str(s).lower().replace("-", " ")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class PrivateProfileError(Exception):
    """The career profile exists but could not be inspected for private text."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def private_phrases(path) -> tuple[list[str], list[str]] | None:
    """(checkable, too_short) phrases from drains + weaknesses.

    Returns None only for legitimate absence (no file, a placeholder, or neither
    key present). Raises PrivateProfileError when the profile is present but
    cannot be inspected, so the caller can fail closed.
    """
    p = Path(path)
    try:
        if not p.exists() or workspace._is_placeholder(p):
            return None
        prof = search_planner.load_profile(p)
    except Exception as ex:
        raise PrivateProfileError(f"could not read it: {type(ex).__name__}") from ex
    if not isinstance(prof, dict):
        raise PrivateProfileError("top level is not a map")
    if "drains" not in prof and "weaknesses" not in prof:
        return None
    raw: list[str] = []
    drains = prof.get("drains")
    if "drains" in prof:
        if not isinstance(drains, list):
            raise PrivateProfileError("drains is not a list")
        raw += [str(d) for d in drains]
    weak = prof.get("weaknesses")
    if "weaknesses" in prof:
        if not isinstance(weak, dict):
            raise PrivateProfileError("weaknesses is not a map")
        for name, desc in weak.items():
            raw += [str(name), str(desc)]
    phrases = [n for n in (_phrase_norm(r) for r in raw) if n]
    if not phrases:
        return None
    checkable = [ph for ph in phrases if len(ph.split()) >= MIN_PRIVATE_WORDS]
    too_short = [ph for ph in phrases if len(ph.split()) < MIN_PRIVATE_WORDS]
    return checkable, too_short


def layer1_private(texts: dict[str, str], phrases, master: str = "") -> None:
    name = "No private profile text (drains, weaknesses)"
    if isinstance(phrases, PrivateProfileError):
        reason = phrases.reason
        test(name, 1, lambda: (False, (
            f"career profile present but could not be checked for private text "
            f"({reason}); fix it with scripts/career_profile_qa.py before delivering")))
        return
    if phrases is None:
        print(f"  [skip] {name}  ->  no career profile drains or weaknesses")
        return
    candidates, too_short = phrases
    master_hay = f" {_phrase_norm(master or '')} "
    in_master = [ph for ph in candidates if f" {ph} " in master_hay]
    checkable = [ph for ph in candidates if ph not in in_master]

    def no_leak():
        hits = []
        for label, text in texts.items():
            hay = f" {_phrase_norm(text or '')} "
            hits += [f"{label}: '{ph}'" for ph in checkable if f" {ph} " in hay]
        if hits:
            return False, "private profile text found in " + "; ".join(hits)
        return True, None

    test(name, 1, no_leak)
    if in_master:
        test("Private phrases already in the master resume (not checked)", 1,
             lambda: (False, "already in master: " + ", ".join(in_master)), blocking=False)
    if too_short:
        test("Private phrases long enough to check", 1,
             lambda: (False, "too short to check: " + ", ".join(too_short)), blocking=False)


# ─── Layer 2 — ATS safety (BLOCKING) ────────────────────────────────────────────

def layer2_ats(tailored: str):
    def no_tables():
        if re.search(r"^\s*\|.*\|\s*$", tailored, re.MULTILINE) or "|---" in tailored:
            return False, "markdown table detected — ATS parsers mishandle tables"
        return True, None

    def no_images_or_html():
        if "![" in tailored:
            return False, "image syntax detected"
        if re.search(r"<[a-zA-Z/][^>]*>", tailored):
            return False, "raw HTML tag detected"
        return True, None

    def contact_line_parseable():
        if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", tailored):
            return True, None
        return False, "no parseable email/contact line found"

    def no_jobfile_sections():
        leaked = [h for h in _headers(tailored) if h.lower() in NON_RESUME_HEADERS]
        if leaked:
            return False, "job-file section leaked into the resume body: " + ", ".join(leaked)
        return True, None

    test("No markdown tables", 2, no_tables)
    test("No images or raw HTML", 2, no_images_or_html)
    test("Parseable contact line", 2, contact_line_parseable)
    test("No job-file sections leaked into resume", 2, no_jobfile_sections)


# ─── Layer 3 — Structure & length (BLOCKING) ────────────────────────────────────

def layer3_structure(tailored: str):
    headers_lower = {h.lower() for h in _headers(tailored)}

    def required_sections():
        missing = [h for h in REQUIRED_RESUME_HEADERS
                   if not any(h in hl for hl in headers_lower)]
        if missing:
            return False, "missing required section(s): " + ", ".join(sorted(missing))
        return True, None

    def word_count_band():
        words = len(re.findall(r"\b\w+\b", tailored))
        if words < 200:
            return False, f"resume is very short ({words} words) — likely incomplete"
        if words > 1100:
            return False, f"resume is very long ({words} words) — trim for a 1-2 page ATS resume"
        return True, f"{words} words"

    def no_empty_sections():
        chunks = re.split(r"^##\s+.+$", tailored, flags=re.MULTILINE)[1:]
        empties = sum(1 for c in chunks if not c.strip())
        if empties:
            return False, f"{empties} section(s) have no content"
        return True, None

    test("Required sections present", 3, required_sections)
    test("Word count within ATS band", 3, word_count_band)
    test("No empty sections", 3, no_empty_sections)


# ─── Layer 4 — Keyword coverage (WARN-ONLY) ─────────────────────────────────────

def layer4_keywords(tailored: str, keywords: list[str]):
    if not keywords:
        test("Top-5 missing keywords woven in", 4,
             lambda: (True, "no Top-5 keyword list found in evaluation — skipped"),
             blocking=False)
        return
    ntail = _norm(tailored)
    missing = [k for k in keywords if _norm(k) not in ntail]
    covered = len(keywords) - len(missing)

    def cover():
        if missing:
            return False, f"{covered}/{len(keywords)} covered; still missing: " + ", ".join(missing)
        return True, f"all {len(keywords)} target keywords present"

    test("Top-5 missing keywords woven in", 4, cover, blocking=False)


# ─── Layer 5 — Master resume health (WARN-ONLY) ─────────────────────────────────

def layer5_master(master: str):
    headers_lower = {h.lower() for h in _headers(master)}

    def has_core_sections():
        missing = [h for h in REQUIRED_RESUME_HEADERS
                   if not any(h in hl for hl in headers_lower)]
        if missing:
            return False, "consider adding section(s): " + ", ".join(sorted(missing))
        return True, None

    def quantified_bullets():
        bullets = _bullets(master)
        if not bullets:
            return False, "no bullet points detected"
        quant = sum(1 for b in bullets if QUANT_RE.search(b))
        ratio = quant / len(bullets)
        detail = f"{quant}/{len(bullets)} bullets are quantified ({ratio:.0%})"
        return (ratio >= 0.4), detail

    def ats_safe_source():
        if re.search(r"^\s*\|.*\|\s*$", master, re.MULTILINE) or "|---" in master:
            return False, "master uses a markdown table — may not survive ATS parsing"
        return True, None

    def length_sanity():
        words = len(re.findall(r"\b\w+\b", master))
        if words < 200:
            return False, f"master resume is thin ({words} words)"
        return True, f"{words} words"

    def contact_present():
        if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", master):
            return True, None
        return False, "no email/contact line found in master"

    test("Core sections present", 5, has_core_sections, blocking=False)
    test("Bullets are quantified (>=40%)", 5, quantified_bullets, blocking=False)
    test("Source is ATS-safe (no tables)", 5, ats_safe_source, blocking=False)
    test("Length is reasonable", 5, length_sanity, blocking=False)
    test("Contact line present", 5, contact_present, blocking=False)


# ─── Runner ─────────────────────────────────────────────────────────────────────

def run(mode, job_file, only_layer, dry_run):
    p = workspace.paths()
    master_path = Path(p["resume"])

    if mode == "master":
        if not master_path.exists() or workspace._is_placeholder(master_path):
            print(f"Config error: no master resume at {master_path}", file=sys.stderr)
            return 2
        master = master_path.read_text(encoding="utf-8")
        if dry_run:
            print("DRY RUN — would run Layer 5 (master health) checks.")
            return 0
        print(f"\nResume QA — master health  |  {master_path}")
        layer5_master(master)
    else:  # tailored
        if not job_file:
            print("Config error: --job is required in tailored mode", file=sys.stderr)
            return 2
        if not Path(job_file).exists():
            print(f"Config error: job file not found: {job_file}", file=sys.stderr)
            return 2
        if not master_path.exists() or workspace._is_placeholder(master_path):
            print(f"Config error: no master resume at {master_path}", file=sys.stderr)
            return 2
        content = jobfile.read(job_file)
        tailored = jobfile.tailored_resume(content)
        if not tailored:
            print(f"Config error: no tailored resume found in {job_file} "
                  "(run the tailoring skill first)", file=sys.stderr)
            return 2
        master = master_path.read_text(encoding="utf-8")
        keywords = jobfile.top5_missing_keywords(content)

        if dry_run:
            print("DRY RUN — would run Layers 1-4 against the tailored resume.")
            return 0

        print(f"\nResume QA — tailored gate  |  {job_file}")
        if only_layer in (None, 1):
            print("\nLayer 1 — Fabrication / fidelity (blocking)")
            layer1_fabrication(tailored, master)
            try:
                phrases = private_phrases(p["career_profile"])
            except PrivateProfileError as err:
                phrases = err
            layer1_private(
                {"resume": tailored,
                 "cover letter": jobfile.section(content, "Cover Letter") or ""},
                phrases, master)
        if only_layer in (None, 2):
            print("\nLayer 2 — ATS safety (blocking)")
            layer2_ats(tailored)
        if only_layer in (None, 3):
            print("\nLayer 3 — Structure & length (blocking)")
            layer3_structure(tailored)
        if only_layer in (None, 4):
            print("\nLayer 4 — Keyword coverage (advisory)")
            layer4_keywords(tailored, keywords)

    # Summary + exit code
    passed = sum(1 for r in _results if r["status"] == "PASS")
    warns = sum(1 for r in _results if r["status"] == "WARN")
    blocking_fail = [r for r in _results if r["status"] in ("FAIL", "ERROR") and r["blocking"]]
    total = len(_results)
    print("\n" + "=" * 60)
    if blocking_fail:
        print(f"  RESULT: BLOCKED — {len(blocking_fail)} blocking failure(s) "
              f"({passed}/{total} passed, {warns} warning(s))")
        print("  Do NOT deliver this resume until the failures above are fixed.")
        print("=" * 60)
        return 1
    print(f"  RESULT: OK — {passed}/{total} passed, {warns} warning(s), 0 blocking failures")
    print("=" * 60)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Resume QA gate")
    ap.add_argument("--mode", choices=["tailored", "master"], default="tailored")
    ap.add_argument("--job", help="path to the job file (tailored mode)")
    ap.add_argument("--layer", type=int, choices=[1, 2, 3, 4], default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.exit(run(args.mode, args.job, args.layer, args.dry_run))


if __name__ == "__main__":
    main()
