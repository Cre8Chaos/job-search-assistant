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
