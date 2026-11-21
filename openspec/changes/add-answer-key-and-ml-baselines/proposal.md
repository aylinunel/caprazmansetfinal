## Why

The narrative map and the behavioural review (BiasGuard) are coded by AI, but nothing measures that AI against a human
answer key, and no model can be trained or adopted without one. The owner is the only expert and reviews in the AI
denetim masası; the answer key has to come from blind coding there, with the owner's own consistency checked.

## What Changes

- An append-only answer-key record (`validation/answerkey/`): coder slots by person and pass, Krippendorff's alpha,
  gold, and an agreement report that names same-coder consistency as such.
- Blind packets shipped in core key `BLIND` (no AI verdicts; the private key stays in the repository) and a blind mode
  in the AI denetim masası; the desk's export is imported back into the record.
- The narrative agent scored against the hand-coded weeks (leak-free examples); blind precision and estimated recall
  for the behavioural review; human examples for the BiasGuard reviewers; grouped cross-validated baselines (majority,
  TF-IDF) as the bar every later model must beat.
- The narrative page states how well the AI coding matches the human coding.

## Capabilities

### New Capabilities
- `answer-key`: human gold for the narrative and behavioural coding, how it is collected blind, and how the AI and
  trained baselines are measured against it.

### Modified Capabilities
<!-- none -->

## Impact

- New: `validation/answerkey/`, `validation/mlbench/`, `data/reference/narrative_codebook.json`,
  `data/reference/blind-packets.json`, `data/reference/narrative-quality.json`; core keys `BLIND`, `NQ`.
- Changed: `narratives.py` (tasks, merge), `biasguard/news.py` (review examples), `site/js/v7/desk.js`, `logic.js`,
  `anlati.js`, `app.js` (`rev7Save`).
- No new dependencies.
- Plan: `docs/superpowers/plans/2026-11-17-ml-narrative-and-behavioural.md`.
