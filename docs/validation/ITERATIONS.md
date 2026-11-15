# Detector iterations

One change per iteration. Before the change, fill in an Iteration Compact. After it, add an Observation
Ledger entry, whether or not anything improved. No model is trained here: an iteration changes card
wording, prompts, retrieval settings or thresholds.

## The loop

| When | Command | Who acts |
|---|---|---|
| Every data pack | `python -m validation.learning snapshot` | automatic |
| After reviewing on the site | download with "İncelemeleri indir", then `python -m validation.feedback import <file> --results runs/bg/biasguard.json` and `python -m validation.feedback status --pack <pack>` | owner |
| Weekly, or after 50 new reviews | `python -m validation.learning errors`, `replay-build`, `insights` | owner reads the two reports in `docs/validation/reports/` |
| Before changing cards or prompts | write the Iteration Compact below | owner / builder |
| After the change | `replay-inputs --out runs/replay/<name>`, reviewer run as in `biasguard/AGENT_REVIEW.md`, lab run (`validation/README.md`), then `promote-check` | owner starts the reviewer runs |
| After the decision | Observation Ledger entry; `versions.jsonl` gets its row from `promote-check` | builder |

## Promotion gate

A candidate replaces the current detector only if all of these hold (`validation/learning/promotion.py`).
A metric that is missing or not estimable is a failure.

| Metric | Limit |
|---|---|
| Findings a person rejected that both AI reviews now confirm | 0 |
| Rejected findings still raised, compared with the current version | no more than now |
| Verified or corrected findings no longer raised | at most 5% |
| Replay cases whose review failed | at most 5% |
| Forbidden answers on the lab's control cases | 0 |
| Events reviewed in the run | at least 95% |
| Any card with 10 or more replay cases whose kept rate fell | none |

## Rollback

`python -m biasguard.news apply` keeps the results it replaces as `biasguard.prev.json`.
`validation/reference/versions.jsonl` names the last promoted version. To roll back: check out that
version's `biasguard/data/` and `biasguard/providers.py`, copy `biasguard.prev.json` over `biasguard.json`,
run `python -m biasguard.news pack --build <dir> --run runs/bg`, and reassemble the site. No retraining
is involved, because nothing was trained.

## Iteration Compact (template)

```text
Goal:
Who cares:
Decision owner:
Action changed by the detector:
Success metric:
Guardrail metrics:
Mistake budget:
Unacceptable mistakes:
Acceptable mistakes:
Assumptions:
Constraints:
Labels and data snapshot:
Baseline:
Candidate signals:
Threshold or config plan:
Eval slices:
Known risks:
Next experiment:
Rollback or fallback:
```

## Iteration 1 — compact

```text
Goal: publish bias and media-technique findings whose status is honest and whose precision rises with review
Who cares: readers (trust), outlets named in findings (fair treatment), the owner (credibility)
Decision owner: Aylin Unel
Action changed by the detector: which findings appear on an event page, and under which status badge
Success metric: verify-pass precision per card, with one-sided 95% lower bound
Guardrail metrics: run completion; findings awaiting review; reviewer workload per pack;
  audit-sample precision of the AI onaylı tier; lab forbidden-rate on controls
Mistake budget: AI onaylı tier — at most 1 rejection in 15 reviewed findings per card
Unacceptable mistakes: a finding that states intent, mental state or affiliation; a failed review shown
  as "no bias"; an unreviewed finding shown as human-verified; a quote that is not in the source
Acceptable mistakes: missed findings (partial recall); findings parked as "İnsan kontrolü bekliyor"
Assumptions: reviewers are available for the verify pass; headlines and ledes only
Constraints: no provider calls from CI; reviewer agents run as in biasguard/AGENT_REVIEW.md
Labels and data snapshot: 2026-11-14_behavioural_627740d135b3; no labels yet
Baseline: 8.1 BiasGuard, 116 cards, prompts biasguard-review-v1.1-explicit-schema
Candidate signals: reviewer disagreement, unsatisfied conditions, missing context, per-card history,
  outlet and topic slices
Threshold or config plan: validation/reference/gates.json (agreed 2026-11-14)
Eval slices: card, catalogue, bloc of quoted outlets, month, event size, tier
Known risks: verify-pass anchoring; same-model reviewer correlation; small counts per card;
  feedback loop if only waiting findings are reviewed (hence the 5% audit)
Next experiment: media-technique cards as lab candidates (Plan 4), because the behavioural cards'
  later conditions are never satisfied from headlines
Rollback or fallback: biasguard.prev.json and the previous card hash
```

## Observation Ledger

```text
Iteration: 0 (baseline measurement, no change)
Change: none; first snapshot and error report
Why this mattered: establishes what the detector does before anything is tuned
Metric movement: none to compare
Slice movement: none
False positives: unknown; no finding has been reviewed
False negatives: not measurable from the verify pass
Unexpected errors: none; 150 of 150 events reviewed
Decision: keep the 8.1 detector as the baseline
Tradeoff accepted: "AI onaylı" currently means "left standing", since no reviewer said "supported"
Lesson captured: for the most-used cards the second necessary condition was never satisfied
  (framing effect 0/250, salience bias 0/230, leveling and sharpening 0/178 assessments). Those
  conditions ask for evidence a headline and lede do not contain.
Regression added: none yet (the replay set is empty until reviews exist)
Debt created: 430 AI-written explanations now ship with findings and are unreviewed
Next iteration: test media-technique cards in the lab
```
