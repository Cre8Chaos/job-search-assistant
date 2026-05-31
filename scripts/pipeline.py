"""
pipeline.py — append/update rows in the workspace job pipeline (data/pipeline.md).

Path is resolved through workspace.py — never hardcoded — so the same script
works for any user and in a hosted per-user workspace.

Usage:
    # Add a new job
    python scripts/pipeline.py add "Acme Corp" "Senior PM" "data/jobs/acme-senior-pm-2026-04-07.md"

    # Update a job's status / grade
    python scripts/pipeline.py update "Acme Corp" "Senior PM" --status Applied --date 2026-04-10
    python scripts/pipeline.py update "Acme Corp" "Senior PM" --grade B
"""
import argparse
import sys
from datetime import date
from pathlib import Path

import workspace

HEADER = """# Job Pipeline

| Company | Role | Grade | Status | Date Found | Job File |
|---|---|---|---|---|---|
"""


def pipeline_path() -> Path:
    return Path(workspace.paths()["pipeline"])


def load_pipeline() -> str:
    p = pipeline_path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(HEADER, encoding="utf-8")
    return p.read_text(encoding="utf-8")


def save_pipeline(content: str) -> None:
    pipeline_path().write_text(content, encoding="utf-8")


def find_row(content: str, company: str, role: str):
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("|") and company.lower() in line.lower() and role.lower() in line.lower():
            return i, line
    return None, None


def cmd_add(company: str, role: str, job_file: str) -> None:
    content = load_pipeline()
    _, existing = find_row(content, company, role)
    if existing:
        print(f"Job already in pipeline: {company} — {role}")
        return
    today = date.today().isoformat()
    new_row = f"| {company} | {role} | — | New | {today} | [{job_file}]({job_file}) |"
    lines = content.rstrip("\n").split("\n")
    lines.append(new_row)
    save_pipeline("\n".join(lines) + "\n")
    print(f"Added: {company} — {role}")


def cmd_update(company: str, role: str, grade: str, status: str, applied_date: str) -> None:
    content = load_pipeline()
    idx, existing = find_row(content, company, role)
    if not existing:
        print(f"Job not found in pipeline: {company} — {role}", file=sys.stderr)
        sys.exit(1)

    parts = [p.strip() for p in existing.split("|")]
    # parts[1]=Company, [2]=Role, [3]=Grade, [4]=Status, [5]=Date, [6]=File
    if grade:
        parts[3] = f" {grade} "
    if status:
        if status == "Applied" and applied_date:
            parts[4] = f" Applied — {applied_date} "
        else:
            parts[4] = f" {status} "

    lines = content.split("\n")
    lines[idx] = "|".join(parts)
    save_pipeline("\n".join(lines))
    print(f"Updated: {company} — {role} | Grade={parts[3].strip()} | Status={parts[4].strip()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    add_p = sub.add_parser("add")
    add_p.add_argument("company")
    add_p.add_argument("role")
    add_p.add_argument("job_file")

    upd_p = sub.add_parser("update")
    upd_p.add_argument("company")
    upd_p.add_argument("role")
    upd_p.add_argument("--grade")
    upd_p.add_argument("--status")
    upd_p.add_argument("--date", dest="applied_date")

    args = parser.parse_args()
    if args.cmd == "add":
        cmd_add(args.company, args.role, args.job_file)
    elif args.cmd == "update":
        cmd_update(args.company, args.role, args.grade, args.status, args.applied_date)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
