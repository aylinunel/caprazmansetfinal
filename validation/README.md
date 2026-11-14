# validation/

Offline tooling for testing BiasGuard. Nothing here is imported by `pipeline/`, `biasguard/` or `site/`.

| Folder | What it is |
|---|---|
| `mesa_bias_expanded/` | The vendored Mesa simulator: 138 authored toy mechanisms. Read-only; checksums are tested. |
| `biaslab/` | The lab: turns simulations into answer-free cases, runs BiasGuard on them, records every attempt. |
| `reference_adapter/` | The integration guide's mock demo, kept for comparison only. |
| `tests/` | `python -m unittest discover -s validation/tests -t . -v` |

## What the lab is, and is not

The lab checks behaviour: does the detector change its answer when a relevant fact changes, hold it
when an irrelevant one does, and decline when the evidence is missing? Its cases are synthetic and
written by the same people who wrote the code.

**A lab result is not detector accuracy.** The sentence that is safe to say publicly:

> We built and tested a simulation-based behavioural evaluation framework that covers 138 supplied
> concepts. Its synthetic scenarios help test our detector's evidence requirements and failure
> handling. Real-world detector validity remains to be demonstrated on independently reviewed data.

## Running it

```bash
python -m pip install -r pipeline/requirements.txt -r validation/requirements.txt
```

```bash
python -m validation.biaslab build --run runs/lab/pilot-1
```

```bash
python -m validation.biaslab tasks --run runs/lab/pilot-1 --config candidate --stage select
```

Run the selector agents on `runs/lab/pilot-1/candidate/tasks/select/` exactly as described in
`biasguard/AGENT_REVIEW.md`, then write and run the review stage the same way (`--stage review`).
Repeat for `--config baseline`. Then:

```bash
python -m validation.biaslab score --run runs/lab/pilot-1
```

`score` exits 0 only when every case completed under both configurations. `--mode offline` checks the
plumbing without any reviewer output; it reports every eligible case as unassessed.

## What is in a run folder

| Path | Who may read it |
|---|---|
| `inputs.jsonl`, `<config>/tasks/**` | Reviewer agents. Only `text`, `context` and an opaque case id. |
| `<config>/selections/`, `<config>/reviews/` | Written by reviewer agents. |
| `private/cases.jsonl`, `private/salt.txt`, `private/manifest.json` | The evaluator only. Never give `private/` to a reviewer agent. |
| `ledger.jsonl` | Append-only record of every attempt. The first attempt per case is the one scored. |
| `report.json` | Metrics for baseline and candidate, with counts beside every rate. |

## How to read the report

- **baseline** is the production catalogue. **candidate** adds the lab-only cards in
  `biaslab/proposed_cards/`. Those cards are proposals; none is in `biasguard/data/cards.json`.
- `ineligible` means no reviewed card exists for the concept. `unassessed` means the card exists but was
  not reviewed. `error` means the review failed. None of the three is a negative.
- "not estimable" means the denominator was zero. It is never a pass.
- The pilot has 5 case families, so no interval is reported: the comparison needs at least 10.
- Two labelled cases with identical visible text are stored once (for selective statistics, the
  boundary control and the inactive control render the same input).

## The crosswalk

`biaslab/crosswalk.json` lists all 138 simulation concepts. 112 share an id with a BiasGuard card and
are marked `needs_domain_review`: a shared id is a proposal, not a match. Only entries marked `pilot` or
`approved` are used. To approve one, edit its `review_status` by hand after reading both definitions;
do not re-run `build_crosswalk.py`, which resets every status.
