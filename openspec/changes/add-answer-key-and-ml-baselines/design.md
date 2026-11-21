## Context

The full task design is the plan `docs/superpowers/plans/2026-11-17-ml-narrative-and-behavioural.md`; the stage model is
the stakeholder report's "machine-learning part". This file keeps the decisions OpenSpec tracks.

## Decisions

- One expert (owner, 2026-11-21): agreement is between two blind passes of the same coder, the second at least 14 days
  after its packet is made; slots are person letter + pass digit (`A1`, `A2`).
- Blind coding in the desk (owner, 2026-11-21), not spreadsheets: packets in core `BLIND`, key never in core.
- Gold comes from people only; a field is usable at alpha ≥ 0.67 on ≥ 30 items coded twice.
- Cross-validation and few-shot examples never share an event with what they are tested on.

## Risks / Trade-offs

- Same-coder consistency measures reliability of one reader, not agreement between readers → reports name it so.
- The site shows AI findings elsewhere, so blindness holds inside the desk only → the desk links nowhere from a blind item.
- Assumes the hand-coded weeks are the owner's coding (`CORE_SLOT = "A1"`); otherwise one constant changes.
