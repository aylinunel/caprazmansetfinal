## Context

The approved design is `docs/superpowers/specs/2026-11-21-single-source-lens-design.md` (approach A: precomputed lens).
This file keeps only the technical decisions OpenSpec tracks; the full reasoning, goals and anti-goals are in that document.

## Decisions

- Precomputed in the build (`pipeline/capraz_pipeline/lens.py`), shipped as core key `LENS`; the site only draws.
- Same-story comparison: Mantel–Haenszel risk ratio stratified by story, Greenland–Robins interval, CMH test, BH across
  outlet × measure (shared `stats.py`, also used by the AI-vs-rules analysis).
- Comparison group and lens holders: active general-news outlets; exclusions are data (`data/reference/lens-groups.json`).
- Skips: complete-looking feeds only, confirmed by a 48-hour text match (`cluster.vectors`, cosine ≥ 0.33).
- Notices: the browser's rule reproduced in Python (URL bit `nu & 1` plus all-capitals keyword titles), keywords kept
  equal by a test.

## Risks / Trade-offs

- Slices are fixed at build time (no free date ranges) → approach C can be added later on top of the same tables.
- Party tone and blame are not in the score (non-goals of this version).
