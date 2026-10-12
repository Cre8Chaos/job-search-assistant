#!/usr/bin/env bash
# Blind known-answer run: each fixture is graded in a fresh claude -p session that
# sees only the skill, the rubric, the profile and one JD. EXPECTED.md never goes in.
set -euo pipefail
ENGINE="$(cd "$(dirname "$0")/.." && pwd)"
FIX="$ENGINE/tests/fixtures/constraints"
OUT="$(mktemp -d)"
for jd in "$FIX"/0*.md; do
  name="$(basename "$jd" .md)"
  prompt="You are running the js-evaluate skill below. Run its gates in the order the skill gives them, and stop where the skill says to stop. Do not score the six dimensions and do not do company research. Print the '**Constraints Gate:**' line and the final '**Grade:**' line (write 'Grade: not capped by a gate' if no gate capped it).

=== SKILL ===
$(cat "$ENGINE/skills/js-evaluate/SKILL.md")
=== RUBRIC ===
$(cat "$ENGINE/references/scoring-rubric.md")
=== profile.yaml ===
$(cat "$FIX/profile.yaml")
=== JOB DESCRIPTION ===
$(cat "$jd")"
  (cd "$OUT" && claude -p --tools "" --setting-sources "" --strict-mcp-config --model sonnet "$prompt") > "$OUT/$name.out"
  echo "== $name"
  grep -m1 -F '**Constraints Gate:**' "$OUT/$name.out" || echo "NO GATE LINE"
  grep -E 'Grade:' "$OUT/$name.out" | tail -n1 | grep . || echo "NO GRADE LINE"
done
echo "Raw outputs: $OUT"
