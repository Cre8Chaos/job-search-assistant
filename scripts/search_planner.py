#!/usr/bin/env python3
"""
search_planner.py — turn a user's profile into a deterministic set of web-search
queries for ToS-safe job sourcing (no scraper, no headless browser).

The `js-find-jobs` skill consumes this so coverage is consistent and testable
instead of improvised per run. Pure stdlib: if PyYAML is installed it is used to
read the profile, otherwise a small YAML-subset parser handles the fixed
`profile.yaml` schema (lists + the `location`/`work_authorization` scalars we need).

CLI (run from the engine root):
    python scripts/search_planner.py            # queries for the resolved workspace
    python scripts/search_planner.py --json      # same, as JSON
    python scripts/search_planner.py --profile path/to/profile.yaml
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# ATS hosts that WebFetch reads reliably (LinkedIn/Indeed are JS-walled and excluded
# on purpose — they belong to the personal scraper tool, not this ToS-safe product).
# Each entry is a SINGLE `site:` filter — never a bare `OR` between two of them,
# because an unparenthesized OR binds loosely on most engines and lets the trailing
# site escape the keyword/intent constraint. Greenhouse moved hosts (boards.* ->
# job-boards.*), so it gets two separate, individually-constrained queries instead.
DEFAULT_BOARDS: tuple[tuple[str, str], ...] = (
    ("greenhouse", "site:boards.greenhouse.io"),
    ("greenhouse", "site:job-boards.greenhouse.io"),
    ("lever", "site:jobs.lever.co"),
    ("ashby", "site:jobs.ashbyhq.com"),
    ("workday", "site:myworkdayjobs.com"),
    ("builtin", "site:builtin.com"),
)

MAX_KEYWORDS_DEFAULT = 8


@dataclass(frozen=True)
class SearchQuery:
    """One planned WebSearch query, tagged so the skill can report coverage."""

    query: str
    keyword: str
    board: str   # ATS board key, or "general"
    kind: str    # "remote" | "location" | "general"


def _quote(keyword: str) -> str:
    return f'"{keyword.strip()}"'


def _location_clause(location: dict) -> str:
    city = str(location.get("city") or "").strip()
    state = str(location.get("state") or "").strip()
    return " ".join(part for part in (city, state) if part)


def build_queries(
    profile: dict,
    *,
    max_keywords: int = MAX_KEYWORDS_DEFAULT,
    boards: tuple[tuple[str, str], ...] = DEFAULT_BOARDS,
    extra_titles: tuple[str, ...] | list[str] = (),
) -> list[SearchQuery]:
    """Build a deterministic, deduped, ordered list of search queries from a profile.

    Order is stable (keyword order × board order × intent), so the same profile
    always yields the same plan — which is what makes sourcing testable.
    """
    raw_keywords = profile.get("search_keywords") or profile.get("target_roles") or []
    if not isinstance(raw_keywords, list):
        raw_keywords = []
    # Coerce to str — a profile may yield a non-string (e.g. an all-digit token
    # parsed as int), and `.strip()` would otherwise crash the whole planner.
    keywords = [s for s in (str(kw).strip() for kw in raw_keywords) if s]
    # Adjacent titles (career profile) fill any remaining keyword budget — they
    # never extend the cap, so the search-count ceiling is unchanged.
    for title in extra_titles:
        t = str(title).strip()
        if t and t not in keywords:
            keywords.append(t)
    keywords = keywords[:max_keywords]

    location = profile.get("location")
    location = location if isinstance(location, dict) else {}
    remote = bool(location.get("remote", False))
    loc_clause = _location_clause(location)
    work_model = profile.get("work_model")
    work_model = work_model if isinstance(work_model, list) else []
    wants_onsite = any(m in ("hybrid", "onsite") for m in work_model)

    auth = profile.get("work_authorization")
    auth = auth if isinstance(auth, dict) else {}
    needs_sponsorship = bool(auth.get("needs_sponsorship", False))

    queries: list[SearchQuery] = []
    seen: set[str] = set()

    def add(query: str, keyword: str, board: str, kind: str) -> None:
        norm = " ".join(query.split()).lower()
        if norm in seen:
            return
        seen.add(norm)
        queries.append(SearchQuery(query=" ".join(query.split()),
                                   keyword=keyword, board=board, kind=kind))

    for kw in keywords:
        q = _quote(kw)
        intents: list[tuple[str, str]] = []
        if remote:
            intents.append((f"{q} remote", "remote"))
        if wants_onsite and loc_clause:
            intents.append((f"{q} {loc_clause}", "location"))
        if not intents:  # neither remote nor a usable location — fall back to bare title
            intents.append((q, "general"))

        for base, kind in intents:
            # ATS-board-scoped queries first (highest-quality, fetchable results)...
            for board_key, site_filter in boards:
                extra = " visa sponsorship" if needs_sponsorship else ""
                add(f"{base} {site_filter}{extra}", kw, board_key, kind)
            # ...then one general query per intent for breadth.
            extra = " visa sponsorship" if needs_sponsorship else ""
            add(f"{base} job{extra}", kw, "general", kind)

    return queries


# --- minimal profile loading (stdlib-first) --------------------------------------

def load_profile(path: Path) -> dict:
    """Load profile.yaml. Uses PyYAML if available, else a schema-scoped fallback."""
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
    except ImportError:
        pass
    return _parse_profile_subset(text)


def _strip_comment(line: str) -> str:
    """Drop a trailing ``#`` comment, but never one inside a quoted value."""
    quote: str | None = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == "#":
            return line[:i]
    return line


def _coerce_scalar(raw: str):
    """Coerce a YAML scalar. Quoted values stay strings (so ``"00501"`` keeps its
    leading zeros and ``"true"`` stays text); only unquoted tokens become bool/int."""
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1]
    if v == "[]":
        return []
    if v == "{}":
        return {}
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _parse_profile_subset(text: str) -> dict:
    """Parse profile.yaml without PyYAML via an indentation stack.

    Supports the shapes the schema uses: top-level scalars and lists, one level of
    nested map (``location``, ``work_authorization``), and lists nested under a map
    key (``domain.prefer``/``avoid``/``dealbreakers``). It is not a full YAML parser
    (no inline flow collections beyond ``[]``/``{}``, no multi-line strings, no lists
    of maps) — just enough for a profile, matching PyYAML on those shapes.
    """
    root: dict = {}
    # Stack of (child_indent, container); container holds children at child_indent.
    stack: list[tuple[int, object]] = [(0, root)]
    # A key whose value was empty, awaiting its first (deeper) child to fix its type.
    pending: tuple[int, object, str] | None = None

    for raw_line in text.splitlines():
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        # Resolve a pending key now that we can see whether its child is deeper.
        if pending is not None:
            key_indent, parent, key = pending
            if indent > key_indent:
                child: object = [] if stripped.startswith("- ") else {}
                parent[key] = child           # type: ignore[index]
                stack.append((indent, child))
                pending = None
            else:
                pending = None  # key had no children -> treat as empty/None, drop it

        # Pop containers we have dedented out of.
        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()
        container = stack[-1][1]

        if stripped.startswith("- "):
            if isinstance(container, list):
                container.append(_coerce_scalar(stripped[2:]))
            continue

        if ":" not in stripped or not isinstance(container, dict):
            continue
        key, _, val = stripped.partition(":")
        key, val = key.strip(), val.strip()
        if val == "":
            pending = (indent, container, key)
        else:
            container[key] = _coerce_scalar(val)

    return root


def _resolve_profile_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import workspace
    return Path(workspace.paths()["profile"])


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Plan job-search queries from a profile.")
    parser.add_argument("--profile", help="path to profile.yaml (default: resolved workspace)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of plain lines")
    parser.add_argument("--max-keywords", type=int, default=MAX_KEYWORDS_DEFAULT)
    parser.add_argument("--career-profile",
                        help="path to career-profile.yaml (default: resolved workspace; "
                             "missing/placeholder is a clean no-op)")
    args = parser.parse_args(argv)

    profile_path = _resolve_profile_path(args.profile)
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

    if args.json:
        print(json.dumps([asdict(q) for q in queries], indent=2))
    else:
        for q in queries:
            print(f"[{q.board:10} {q.kind:8}] {q.query}")
        print(f"\n{len(queries)} queries planned for {profile_path}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
