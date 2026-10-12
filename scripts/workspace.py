"""
workspace.py — the single seam between the ENGINE (this bundle) and a user's
per-user WORKSPACE (their resume, profile, job pipeline).

Every script and SKILL.md locates files ONLY through this module. No script or
skill ever hardcodes a path or any personal value. This is the one place that
would be wrapped to point at a per-user object store in a hosted deployment.

Workspace resolution order:
  1. $JOB_SEARCH_WORKSPACE                       (the hosting injection point)
  2. pointer file ~/.config/job-search/workspace (a user-chosen path, one line)
  3. default ~/Projects/job-search

CLI:
  python scripts/workspace.py resolve     # print the resolved workspace root
  python scripts/workspace.py paths        # print canonical sub-paths as JSON
  python scripts/workspace.py ensure       # create the workspace from the template if missing
  python scripts/workspace.py validate     # exit 0 if ready, 1 if setup still needed
"""
import json
import os
import shutil
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ENGINE_ROOT / "workspace-template"

POINTER_FILE = Path.home() / ".config" / "job-search" / "workspace"
DEFAULT_WORKSPACE = Path.home() / "Projects" / "job-search"

# Sentinels written into the template — their presence means "not set up yet".
PLACEHOLDER_MARKER = "<!-- PLACEHOLDER"


def resolve() -> Path:
    """Return the workspace root (not guaranteed to exist yet)."""
    env = os.environ.get("JOB_SEARCH_WORKSPACE")
    if env:
        return Path(env).expanduser()
    try:
        pointer = POINTER_FILE.read_text(encoding="utf-8").strip()
        if pointer:
            return Path(pointer).expanduser()
    except FileNotFoundError:
        pass
    return DEFAULT_WORKSPACE


def paths(root: Path | None = None) -> dict:
    """Canonical sub-paths inside the workspace. Single source of layout truth."""
    root = root or resolve()
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


def ensure(root: Path | None = None) -> Path:
    """Create the workspace by copying the template if it does not exist yet."""
    root = root or resolve()
    if not root.exists():
        if not TEMPLATE_DIR.exists():
            raise FileNotFoundError(f"workspace template missing: {TEMPLATE_DIR}")
        shutil.copytree(TEMPLATE_DIR, root)
    else:
        # Backfill any missing canonical dirs without clobbering user data.
        for sub in ("config", "data/jobs", "output/pdfs", "output/reports"):
            (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def _is_placeholder(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return True
    return PLACEHOLDER_MARKER in text or not text.strip()


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


# NOTE: config/career-profile.yaml is intentionally NOT validated here — it is
# optional (js-assess). Consumers treat placeholder/missing as absent.
def validate(root: Path | None = None) -> tuple[bool, list[str]]:
    """Return (ready, problems). Ready means profile + resume exist and are real."""
    root = root or resolve()
    p = paths(root)
    problems: list[str] = []
    if not root.exists():
        problems.append(f"workspace does not exist: {root}")
        return False, problems
    profile_path = Path(p["profile"])
    if _is_placeholder(profile_path):
        problems.append("profile.yaml missing or still a placeholder — run setup interview")
    else:
        import search_planner  # local import: keeps workspace.py import-light
        try:
            problems.extend(travel_problems(search_planner.load_profile(profile_path)))
        except Exception as ex:
            problems.append(f"profile.yaml unreadable ({ex})")
    if _is_placeholder(Path(p["resume"])):
        problems.append("resume.md missing or still a placeholder — run resume review")
    return (len(problems) == 0), problems


def _main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "paths"
    if cmd == "resolve":
        print(resolve())
        return 0
    if cmd == "paths":
        print(json.dumps(paths(), indent=2))
        return 0
    if cmd == "ensure":
        root = ensure()
        print(f"workspace ready: {root}")
        return 0
    if cmd == "validate":
        ready, problems = validate()
        if ready:
            print("workspace ready")
            return 0
        for prob in problems:
            print(f"  - {prob}", file=sys.stderr)
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
