# Human Reference and Publication Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture human review of BiasGuard's labels as a reference set, measure BiasGuard versions against it, and gate which labels the public site may show.

**Architecture:** Reviewers work from exported packets and their answers are imported into an append-only label file. A reference builder turns two blind labels plus adjudication into one reference state per event and card. Real BiasGuard runs are scored through the same adapter, ledger row shape and metrics as the lab. A gate file, agreed in advance, maps each card's measured result to `public`, `review_only` or `hidden`, and the build exports that decision for the site.

**Tech Stack:** Python 3.12 standard library, `unittest`, Node 22 for site logic tests.

**Spec:** `docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md`

## Global Constraints

- Prerequisite: Plan 2 complete (`validation/biaslab/adapter.py`, `metrics.py`, `cases.py`).
- Two review passes exist and are never mixed: `blind` (reviewer does not see AI output) and `verify`
  (reviewer sees and corrects AI output). Only `blind` labels feed accuracy metrics.
- Reference states are exactly `supported`, `reviewed_negative`, `unresolved`, `ineligible`.
- A reference negative requires a human `reviewed_negative`. Detector silence, a missing label or an
  unlabelled card is never a negative.
- Reviewer identity is stored as an opaque id (`r1`, `r2`, …). No names or emails in the repo.
- Label files are append-only. Corrections are new rows; nothing is rewritten.
- The sampling unit is the event. Events sharing syndicated text are one cluster.
- Thresholds in `gates.json` carry `"agreed": false` until the owner sets them; while any threshold is
  not agreed, no card can be `public`.
- Synthetic lab results never enter these metrics or the gate.
- Site text is Turkish and escapes all strings, as the existing modules do.
- Follow the owner's standing instructions: `ponytail` and `anthropic-skills:karpathy-guidelines`.

## Review Focus

1. A reviewer file with a duplicate row, an unknown card id or an event not in the packet → the import
   rejects the whole file and names the row; nothing is appended. (Task 2)
2. A card with zero human-supported cases → recall is "not estimable" and the gate returns
   `review_only`, never `public`. (Tasks 4, 6)
3. Baseline and candidate runs built from different inputs or pack versions → the comparison refuses
   to run. (Task 5)
4. A verification record made against an older data pack → the site shows the label as **YZ**, not as
   human-verified. (Task 7)
5. A packet opened in a spreadsheet and saved with a BOM, CRLF line ends or Turkish characters →
   imports identically to the original. (Task 2)

---

### Task 1: Label records

**Files:**
- Create: `validation/biaslab/reference.py`
- Create: `validation/reference/README.md`, `validation/reference/labels.jsonl` (empty)
- Test: `validation/tests/test_reference_records.py`

**Interfaces:**
- Produces:
  ```python
  STATES = ("supported", "reviewed_negative", "unresolved", "ineligible")
  PASSES = ("blind", "verify", "adjudication")

  @dataclass(frozen=True)
  class Label:
      event: str
      pack_version: str          # core.bin meta build id the reviewer saw
      text_sha256: str           # of the event text shown
      card_id: str
      reviewer: str              # r"r\d+"
      review_pass: str
      state: str
      evidence_adequate: bool | None   # verify pass only: does the AI's quote support the label
      quotes: tuple[dict, ...]         # {"source": "text"|"context", "quote": str}
      note: str
      labelled_at: str                 # UTC ISO-8601

  def validate(label: Label, known_cards: set[str]) -> None       # raises ValueError
  def append(path: Path, labels: Sequence[Label]) -> None         # all-or-nothing
  def read(path: Path) -> list[Label]
  ```
- `validate` rules: enums; `reviewer` pattern; `card_id` known; `evidence_adequate` is `None` unless
  `review_pass == "verify"`; every quote is non-empty.
- README states what each pass means and that only `blind` labels are used for accuracy.

- [ ] **Step 1: Write the failing tests**

```python
def test_round_trip(self): ...
def test_unknown_card_is_rejected(self): ...
def test_reviewer_must_be_opaque_id(self):
    with self.assertRaises(ValueError): validate(label(reviewer="ayse@example.com"), CARDS)
def test_evidence_adequate_only_on_verify_pass(self): ...
def test_append_is_all_or_nothing(self):
    # second label invalid → file unchanged
def test_append_never_truncates(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: append-only human label records"`.

---

### Task 2: Reviewer packets

**Files:**
- Create: `validation/biaslab/packets.py`
- Modify: `validation/biaslab/__main__.py` (subcommands `packet export`, `packet import`)
- Test: `validation/tests/test_packets.py`

**Interfaces:**
- Consumes: `biasguard.news.event_inputs(build, top)`, a BiasGuard results file (`biasguard.json`).
- Produces:
  ```python
  def sample_events(inputs: list[dict], n: int, seed: int, holdout_from: str) -> dict
      # {"dev": [event ids], "holdout": [event ids]}; holdout = events whose first headline time >= holdout_from
  def blind_packet(inputs, results, events, distractors: int, seed: int) -> list[dict]
  def verify_packet(inputs, results, events) -> list[dict]
  def write_csv(rows: list[dict], path: Path) -> None
  def import_csv(path: Path, packet: list[dict], reviewer: str, review_pass: str) -> list[Label]
  ```
- Blind packet: one row per (event, card). Cards = every card the detector selected for that event plus
  `distractors` cards drawn at random from the rest, shuffled together with no column showing which is
  which. Columns: `event`, `text`, `context`, `card_id`, `card_name`, `definition`,
  `necessary_conditions`, then empty `state`, `quote`, `note`. No AI verdict, evidence or status.
- Verify packet: one row per AI finding (supported, uncertain, contextual effect), with the AI's status
  and quotes shown, then empty `state`, `evidence_adequate`, `corrected_quote`, `note`.
- CSV is UTF-8 with BOM on write; `import_csv` accepts BOM or none and CRLF or LF.
- `import_csv` rejects the whole file (ValueError naming the 1-based row) on: a row not in the packet,
  a duplicate (event, card), an empty or unknown `state`, or a changed `text`.
- Stated limit, written into the packet header and the README: recall measured on the blind packet is
  recall *within the shown card list*, not over all 116 cards.

- [ ] **Step 1: Write the failing tests**

```python
def test_blind_packet_contains_no_ai_verdict(self):
    rows = blind_packet(INPUTS, RESULTS, ["e1"], distractors=3, seed=1)
    self.assertFalse({"status", "verdict", "ai_quote", "selected"} & set(rows[0]))
def test_blind_packet_mixes_selected_and_distractor_cards(self): ...   # len == selected + 3, order differs across seeds
def test_holdout_split_is_by_time_and_events_never_straddle(self): ...
def test_sampling_is_deterministic_for_a_seed(self): ...
def test_import_round_trip_with_bom_crlf_and_turkish(self):
    # write, rewrite the file as utf-8-sig with \r\n and "İğdır şöyle", import → labels equal
def test_import_rejects_duplicate_row_and_appends_nothing(self): ...
def test_import_rejects_event_not_in_packet(self): ...
def test_import_rejects_edited_event_text(self): ...
def test_verify_packet_shows_ai_quotes(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: blind and verify reviewer packets"`.

---

### Task 3: Agreement and the adjudicated reference

**Files:**
- Modify: `validation/biaslab/reference.py`
- Test: `validation/tests/test_reference_build.py`

**Interfaces:**
- Produces:
  ```python
  def agreement(labels: Sequence[Label]) -> dict
      # per card and overall: {"pairs", "agree", "kappa"}; kappa None when undefined
  def build_reference(labels: Sequence[Label]) -> dict[tuple[str, str], dict]
      # (event, card_id) → {"state", "basis": "two_blind_agree"|"adjudicated"|"single_blind"|"disagreement",
      #                     "pack_version", "text_sha256"}
  def disagreements(labels) -> list[tuple[str, str]]
  ```
- Rules, using `blind` labels only: two reviewers agree → that state. They disagree → the latest
  `adjudication` label if present, else `unresolved` with basis `disagreement`. One blind label only →
  `unresolved` with basis `single_blind`. Disagreement records are kept and counted, never dropped.
- `verify` labels are ignored here.

- [ ] **Step 1: Write the failing tests**

```python
def test_two_agreeing_blind_labels_make_a_reference(self): ...
def test_disagreement_without_adjudication_is_unresolved(self): ...
def test_adjudication_resolves_and_is_marked(self): ...
def test_single_blind_label_is_unresolved(self): ...
def test_verify_labels_do_not_create_reference_states(self): ...
def test_kappa_is_none_when_one_category_only(self): ...
def test_kappa_known_value(self):
    # 2×2 table [[20,5],[10,15]] → kappa == 0.4
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: inter-reviewer agreement and adjudicated reference"`.

---

### Task 4: Score a real run against the reference

**Files:**
- Create: `validation/biaslab/score_real.py`
- Modify: `validation/biaslab/__main__.py` (subcommand `score-real`)
- Test: `validation/tests/test_score_real.py`

**Interfaces:**
- Consumes: `adapter.normalize`, `metrics.summarize`, `metrics.Row`, `build_reference`,
  per-event BiasGuard results produced by re-running `BiasGuard(reviewer=FileReviewer(run, event))`.
- Produces:
  ```python
  def clusters(inputs: list[dict]) -> dict[str, str]     # event → cluster id (shared lede sha → same cluster)
  def rows(run: Path, reference: dict, split: Literal["dev", "holdout"]) -> list[Row]
  def per_card(rows_: list[Row]) -> dict[str, dict]      # card_id → summarize(...)
  def causes(run: Path, reference: dict) -> dict[str, int]
  ```
- Row mapping: reference `supported` → kind `positive`, acceptable `{supported, contextual_effect}`;
  `reviewed_negative` → kind `boundary_control`, forbidden `{supported, contextual_effect}`;
  `unresolved` and `ineligible` are excluded from semantic rows and reported as counts.
  `Row.family` is the event's cluster id. `span_ok` is true when a `verify`-pass label for that
  (event, card) has `evidence_adequate is True`; absent → `False` and counted under
  `evidence_unreviewed`.
- `causes` assigns each missed reference positive one cause: `incomplete_request` (status `error`),
  `retrieval_miss` (`unassessed`), `needs_context` (`uncertain`), `semantic_miss` (`not_supported`).
- Report file `report-real.json`: overall and per-card summaries for the chosen split, counts of
  unresolved/ineligible/evidence-unreviewed, agreement, causes, manifests, and the fixed line
  `"scope": "human-reference subset; recall is within the shown card list"`.

- [ ] **Step 1: Write the failing tests** (small fixture run directory with reviewer JSON files)

```python
def test_unresolved_reference_is_excluded_and_counted(self): ...
def test_detector_silence_on_unlabelled_card_adds_no_row(self): ...
def test_error_on_reference_positive_counts_as_end_to_end_miss_with_cause(self):
    self.assertEqual(causes(run, ref)["incomplete_request"], 1)
def test_supported_without_adequate_evidence_is_not_strict_true_positive(self): ...
def test_card_with_no_reference_positive_has_none_recall(self):
    self.assertIsNone(per_card(rows_)["halo-effect"]["end_to_end_recall"]["value"])
def test_events_sharing_a_lede_share_a_cluster(self): ...
def test_holdout_rows_never_appear_in_dev(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: score real BiasGuard runs against the human reference"`.

---

### Task 5: Compare two detector versions

**Files:**
- Create: `validation/biaslab/compare.py`
- Modify: `validation/biaslab/__main__.py` (subcommand `compare`)
- Create: `docs/validation/CHANGE_PROTOCOL.md`
- Test: `validation/tests/test_compare.py`

**Interfaces:**
- Produces:
  ```python
  class NotComparable(ValueError): ...
  def compare(baseline_run: Path, candidate_run: Path, reference: dict, split: str,
              primary: tuple[str, ...] = ("strict_precision", "end_to_end_recall")) -> dict
  ```
- Raises `NotComparable` unless both runs have the same event set, the same `text_sha256` and
  `context_sha256` per event, and the same pack version.
- Output: both summaries, `paired_bootstrap` per primary metric over clusters, per-card deltas with
  support counts, regressions listed first (any card whose point estimate fell), both manifests
  (`card_hash`, `prompts_version`), and the completion and decision-coverage change.
- `CHANGE_PROTOCOL.md` (one page): pick one measured cause from `causes`; change one component; freeze
  the manifest; compare on `dev`; touch `holdout` once per candidate, after the change is final; record
  the result whether or not it improved; never tune on `holdout`.

- [ ] **Step 1: Write the failing tests**

```python
def test_different_inputs_are_not_comparable(self): ...
def test_different_pack_versions_are_not_comparable(self): ...
def test_candidate_that_only_abstains_more_shows_lower_coverage(self):
    out = compare(base, cand, ref, "dev")
    self.assertLess(out["candidate"]["decision_coverage"]["value"], out["baseline"]["decision_coverage"]["value"])
def test_regressed_cards_are_listed_first(self): ...
def test_interval_is_none_with_fewer_than_ten_clusters(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement and write the protocol page.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: paired comparison of detector versions"`.

---

### Task 6: Publication gate

**Files:**
- Create: `validation/biaslab/gate.py`
- Create: `validation/reference/gates.json`
- Modify: `validation/biaslab/__main__.py` (subcommand `gate`)
- Test: `validation/tests/test_gate.py`

**Interfaces:**
- Produces:
  ```python
  def wilson_lower(successes: int, n: int, z: float = 1.6449) -> float | None   # one-sided 95%
  def decide(card_summary: dict, run_summary: dict, gates: dict) -> dict
      # {"decision": "public"|"review_only"|"hidden", "reasons": [str, …]}
  def decide_all(per_card: dict, run_summary: dict, gates: dict) -> dict[str, dict]
  ```
- `gates.json` initial content (placeholders from the guide, not agreed):
  ```json
  {"agreed": false,
   "min_completion": 0.99,
   "min_decision_coverage": 0.80,
   "min_strict_precision_lower_bound": 0.90,
   "min_reference_positives": 20,
   "min_reference_negatives": 20,
   "min_end_to_end_recall": 0.50,
   "hide_below_strict_precision": 0.50}
  ```
- Rules, in order: `agreed` false → `review_only` with reason "thresholds not agreed"; run completion or
  coverage below minimum → `review_only`; support below either minimum → `review_only`; any required
  metric `None` → `review_only`; strict precision point estimate below `hide_below_strict_precision`
  → `hidden`; Wilson lower bound of strict precision and end-to-end recall both meet their minimum →
  `public`; otherwise `review_only`. Cards with `review_policy` `effect_context_only` can be `public`
  only as a contextual effect, recorded as `"display": "context"`.
- `gate` command writes `validation/reference/label_status.json`:
  `{"pack_version", "generated_at", "cards": {card_id: {"decision", "display", "reasons"}}}`.

- [ ] **Step 1: Write the failing tests**

```python
def test_nothing_is_public_while_thresholds_are_not_agreed(self): ...
def test_undefined_metric_is_review_only_never_public(self): ...
def test_low_support_is_review_only(self): ...
def test_low_precision_is_hidden(self): ...
def test_card_meeting_every_threshold_is_public(self): ...
def test_wilson_known_values(self):
    self.assertIsNone(wilson_lower(0, 0))
    self.assertAlmostEqual(wilson_lower(100, 100), 0.9737, places=3)
def test_context_only_card_is_displayed_as_context(self): ...
def test_every_decision_carries_a_reason(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: pre-registered publication gate per card"`.

---

### Task 7: Carry gate and verification status to the site

**Files:**
- Modify: `pipeline/capraz_pipeline/build.py` (near the existing `BG`/`BGS` block, line ~211)
- Modify: `site/js/v7/logic.js`, `site/js/v7/olay.js`
- Test: `pipeline/tests/test_build.py`, `site/tests/logic.test.cjs`

**Interfaces:**
- `build.py` adds two optional keys to `core.bin`, each only when its file exists:
  `BGG` ← `validation/reference/label_status.json`; `BGV` ← a file
  `<out>/biasguard-verified.json` produced by
  `python -m validation.biaslab verified --labels validation/reference/labels.jsonl --out <file>`:
  `{pack_version, items: {"<event>|<card_id>": "verified"|"corrected"|"rejected"}}` from the latest
  `verify` label per pair (`supported` + adequate → `verified`; `supported` + not adequate, or a
  corrected quote → `corrected`; `reviewed_negative` → `rejected`).
  `build.py` reads files only; it does not import `validation`.
- `logic.js` adds a pure function:
  ```js
  // returns "hidden" | "yz" | "dogrulandi" | "duzeltildi"
  function bgLabelState(eventId, cardId, BGG, BGV, packVersion)
  ```
  Rules: gate decision `hidden`, or verification `rejected` → `hidden`. No `BGG` at all → `yz`
  (today's behaviour). Verification present and `BGV.pack_version === packVersion` → `dogrulandi` or
  `duzeltildi`. Otherwise `yz`. Gate `review_only` → `hidden` on public pages.
- `olay.js` uses the function to skip hidden findings and to show `İnsan doğrulamalı` or
  `İnsan düzeltmeli` next to the existing **YZ** mark. No other layout change.

- [ ] **Step 1: Write the failing tests**

```js
test('no gate file keeps today behaviour', () => assert.equal(bgLabelState('e1','halo-effect',null,null,'p1'),'yz'));
test('review_only card is hidden', ...);
test('rejected finding is hidden', ...);
test('verified on the current pack shows dogrulandi', ...);
test('verification from an older pack falls back to yz', ...);
test('corrected finding shows duzeltildi', ...);
```

```python
def test_build_includes_bgg_only_when_file_exists(self): ...
def test_build_does_not_import_validation(self):
    self.assertNotIn("validation", Path("capraz_pipeline/build.py").read_text().split("import", 1)[1].split("\n\n")[0])
```

- [ ] **Step 2: Run and confirm failure** — `node --test site/tests/logic.test.cjs`; `cd pipeline && python -m unittest tests.test_build -v`.
- [ ] **Step 3: Implement the `verified` subcommand (with its own unit test in `validation/tests/test_verified.py`), the build keys, the logic function and the `olay.js` use.**
- [ ] **Step 4: Regenerate the page and run the smoke test**

Run: `cd pipeline && python3 -c "from pathlib import Path; from capraz_pipeline import site; site.assemble(Path('../public/data'), Path('../public'))"`
Run: `node site/tests/smoke.cjs public /tmp/smoke-out`
Expected: no console errors; event pages render as before when no gate file exists.

- [ ] **Step 5: Run every suite**

Run: `python -m unittest discover -s validation/tests -t . -v`
Run: `python -m unittest discover -s tests_repo -t . -v`
Run: `cd pipeline && python -m unittest discover -s tests -v`
Run: `python -m unittest biasguard.test_news -v`
Run: `node --test site/tests/logic.test.cjs`
Expected: every suite passes.

- [ ] **Step 6: Commit and push**

```bash
git commit -am "feat: gate and human-verification status on event pages"
git push -u origin claude/zen-ptolemy-7bvru2
```

---

## Work in this plan that is not code

These steps belong to the owner and the reviewers; the tooling above only supports them.

| Step | Who | Output |
|---|---|---|
| Write the annotation guide (per card: what counts, what does not, quoted versus endorsed speech, Turkish examples) | Owner with reviewers | `docs/validation/ANNOTATION_GUIDE.md` |
| Calibration round: both reviewers label the same 20 events, compare, revise the guide | Reviewers | agreement report |
| Blind pass on the sampled events | Two reviewers | `labels.jsonl` rows, pass `blind` |
| Adjudicate disagreements | A third person or the owner | rows, pass `adjudication` |
| Agree the gate thresholds and set `"agreed": true` | Owner | `gates.json` |
| Verify-and-correct pass over every label intended for the public site | Reviewers | rows, pass `verify` |
| Decide go-live from the gate report | Owner | recorded decision |

## What can honestly be said after each plan

| After | Permitted statement |
|---|---|
| Plan 1 | "The project is reproduced from 8.1 and all its test suites run in CI." |
| Plan 2 | "A simulation-based behavioural test harness exists and has been exercised on two pilot concepts. It is not an accuracy measurement." |
| Plan 3, tooling only | "Human review can be captured and scored." |
| Plan 3, after blind review and a comparison | Per-card precision and within-list recall on the sampled events, with intervals, sample period and reviewer agreement stated next to each number. |
