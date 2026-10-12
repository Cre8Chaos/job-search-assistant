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
  (cd "$OUT" && claude -p --tools "" --setting-sources "" --strict-mcp-config --model sonnet "$prompt") > "$OUT/$name.out"
  echo "== $name"; grep -m2 -E 'Constraints Gate|Grade:' "$OUT/$name.out" || echo "NO GATE LINE"
done
echo "Raw outputs: $OUT"
