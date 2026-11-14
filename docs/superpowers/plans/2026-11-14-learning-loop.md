# Learning Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the detector get measurably better as reviewed data arrives, and surface patterns no card covers yet.

**Architecture:** Follows the `mle-workflow` skill, using only the lanes that fit: there is no model training, serving endpoint or live traffic. Each build writes a snapshot of what the detector said. Human reviews are joined to snapshots to produce error clusters, a permanent replay set and per-slice trends. A detector version (cards + prompts + settings) is promoted only through a declared gate, with the previous version kept for rollback. Reviewer notes and clusters of rejected findings feed card proposals, which go through the lab.

**Tech Stack:** Python 3.12 standard library, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md` (section "How the detector learns")

## Global Constraints

- Prerequisite: Plan 3 (`validation/feedback/labels.py`, `stats.py`, tiers in `biasguard.json`).
- "Learning" here means: routing statistics, a replay set, gated detector versions and card
  proposals. No weights are trained and no claim of training is made anywhere.
- A detector version is the triple (`card_hash`, `prompts_version`, settings hash). Every snapshot,
  label and report names it.
- Reviews are delayed, partial and anchored labels. Every report that uses them says
  "verify-pass" and gives counts next to every rate.
- A rate with a zero denominator is `None`, shown as "not estimable".
- One change per iteration. Each iteration has an Iteration Compact before it and an Observation
  Ledger entry after it, whether or not it improved anything.
- Replay cases are never deleted. A case that no longer applies is marked `retired` with a reason.
- No provider is called from tests or CI. Re-reviewing replay cases is an owner-started reviewer run.
- Reports contain event ids, card ids, quotes already public on the site and counts. No reviewer
  identity.
- Follow the owner's standing instructions: `ponytail` and `anthropic-skills:karpathy-guidelines`.

## Review Focus

1. Two builds of the same pack with the same detector version → one snapshot, not two; a rebuild must
   not double the data. (Task 1)
2. A card with 3 reviews, all rejected → appears in the cluster report with its count, and is not
   described as "0% precision" without the n. (Task 2)
3. A candidate version that improves overall but regresses one outlet bloc or one card → promotion
   refused, and the regression is named. (Task 4)
4. A replay case whose event text changed in a later pack → not replayed against the new text; marked
   stale. (Task 3)
5. A burst of findings for one card in one week (a news event, not a detector change) → flagged as
   drift to look at, with the detector version shown as unchanged. (Task 5)

---

### Task 1: Data contract and build snapshots

**Files:**
- Create: `docs/validation/DATA_CONTRACT.md`
- Create: `validation/learning/__init__.py`, `validation/learning/snapshot.py`,
  `validation/learning/__main__.py`
- Create: `validation/reference/snapshots/` (with `.gitkeep`)
- Test: `validation/tests/test_snapshot.py`

**Interfaces:**
- `DATA_CONTRACT.md` fixes: entity grain (one row per event × card × detector version × pack);
  primary key; label = editor review outcome; label timing (after publication, no deadline); label
  bias (anchored, partial, audit-sampled); inputs available at prediction time (headlines, ledes,
  outlet placement, event timing — nothing from reviews); split policy (by event; time-ordered:
  replay set = everything reviewed before the candidate was written); sensitive fields (none stored;
  no reviewer identity); snapshot id format.
- Produces:
  ```python
  def detector_version(results: dict) -> str        # 12 hex of sha256(card_hash|prompts_version|settings)
  def snapshot_id(pack_version: str, catalog: str, version: str) -> str
  def rows(results: dict, core_meta: dict, catalog: str) -> list[dict]
      # one per finding and one per (event, selected card) without a finding:
      # {event, card_id, catalog, status, tier, tier_reasons, audit, outlets, bloc_mix, month,
      #  event_size, text_sha256, pack_version, detector_version}
  def write(results_path: Path, core_path: Path, catalog: str, out_dir: Path) -> Path   # idempotent
  ```
- `bloc_mix` is `sol`, `orta`, `sağ` or `karışık`, from the outlets quoted in the finding and the
  registry placements (`< 45`, `> 55`, else centre). `write` produces
  `<out_dir>/<snapshot_id>.jsonl.gz` and returns the existing path if the file is already there with
  the same content hash; it raises if the id exists with different content.
- `apply` in `biasguard/news.py` must put `card_hash`, `prompts_version` and `MAX_CANDIDATES` into
  `summary["detector"]`; add that there with a test in `biasguard/test_news.py`.

- [ ] **Step 1: Write the failing tests**

```python
def test_same_inputs_give_same_snapshot_id_and_no_second_file(self): ...
def test_changed_card_hash_changes_detector_version(self): ...
def test_same_id_with_different_content_raises(self): ...
def test_selected_but_unflagged_cards_get_a_row(self): ...     # status "suppressed"/"none"
def test_bloc_mix_from_quoted_outlets(self): ...
def test_row_has_no_field_derived_from_reviews(self): ...
def test_real_pack_produces_439_finding_rows(self):            # public/data/core.bin, key BG
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Write the contract; implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: data contract and idempotent detector snapshots"`.

---

### Task 2: Error analysis

**Files:**
- Create: `validation/learning/errors.py`; subcommand `errors`
- Test: `validation/tests/test_errors.py`

**Interfaces:**
- Consumes: snapshot rows, `validation.feedback.labels.read`.
- Produces:
  ```python
  def joined(rows: list[dict], labels: list[Label]) -> list[dict]     # row + outcome|None; key event, card, pack, text hash
  def confusion(joined_rows: list[dict]) -> dict
      # by tier: {"kept", "rejected", "corrected", "unreviewed"}; plus system failures count
  def clusters(joined_rows: list[dict], by: Sequence[str], min_n: int = 5) -> list[dict]
      # [{"slice": {...}, "reviewed", "rejected", "reject_rate", "lower", "upper"}], worst first
  def stuck_conditions(run: Path) -> list[dict]
      # per card: which necessary_condition index is most often "unknown" or "contradicted", with counts
  def next_move(cluster: dict, stuck: list[dict]) -> str
  ```
- `clusters` slices: `card_id`, `catalog`, `bloc_mix`, `month`, `event_size` bucket (`5–9`, `10–19`,
  `20+`), `tier`. Slices with fewer than `min_n` reviews are listed separately as "too few to judge".
- `stuck_conditions` reads the reviewer files in the run folder; it explains findings that never
  reach `supported` (today: all 439).
- `next_move` returns one of the skill's four moves, by rule: rejects concentrated in one card →
  `better card wording`; one condition stuck `unknown` for a card in more than half its assessments →
  `better evidence (context the input lacks)`; rejects spread across cards in one slice →
  `better threshold/config`; system failures above 5% → `better product fallback`.
- `errors` command writes `docs/validation/reports/errors-<snapshot_id>.md`: the confusion table,
  worst clusters with counts, stuck conditions, and one proposed move per major cluster.

- [ ] **Step 1: Write the failing tests**

```python
def test_join_ignores_labels_from_another_pack_or_text(self): ...
def test_confusion_counts_unreviewed_separately(self): ...
def test_small_slices_are_reported_as_too_few(self):
    out = clusters(rows_with_3_rejects_of_3, by=["card_id"])
    self.assertEqual(out, []); ...                      # and it appears in the too-few list with n == 3
def test_clusters_sorted_by_lower_bound_of_reject_rate(self): ...
def test_stuck_conditions_counts_unknown_per_condition(self): ...
def test_next_move_for_single_card_cluster(self): ...
def test_report_shows_counts_beside_every_rate(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Run it on the real run folder** — `python -m validation.learning errors --run runs/bg --core public/data/core.bin`. Expected: no reviews yet, so the confusion table is all "unreviewed"; the stuck-conditions table is populated. Commit the report.
- [ ] **Step 6: Commit** — `git commit -m "feat: error clusters and stuck-condition analysis"`.

---

### Task 3: Replay set

**Files:**
- Create: `validation/learning/replay.py`; subcommands `replay build`, `replay score`
- Create: `validation/reference/replay.jsonl`
- Test: `validation/tests/test_replay.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class ReplayCase:
      case_id: str               # sha256(event|card|text_sha256)[:12]
      event: str; card_id: str; text: str; context: str; text_sha256: str
      expect: str                # "present" (verified/corrected) | "absent" (rejected)
      note: str; added_from_pack: str; retired: str | None

  def build(labels: list[Label], inputs: list[dict], existing: list[ReplayCase]) -> list[ReplayCase]
  def write_inputs(cases: list[ReplayCase], run: Path) -> None      # inputs.jsonl for biasguard.news tasks
  def score(cases: list[ReplayCase], run: Path, cards: list[dict]) -> dict
      # {"kept_present", "lost_present", "kept_absent", "reintroduced_absent", "errors", "by_card": {...}}
  ```
- `build` appends new cases, never rewrites existing ones, and stores the event text so the case
  survives later packs. A case whose label was superseded by a later review of the same key is
  retired with reason `superseded`.
- `score` runs the engine over replayed reviewer files for the candidate version: a `present` case
  must not be `suppressed`; an `absent` case must not be `pattern_supported` or
  `contextual_effect_consensus`.

- [ ] **Step 1: Write the failing tests**

```python
def test_every_review_becomes_exactly_one_case(self): ...
def test_rebuild_adds_nothing_when_no_new_labels(self): ...
def test_case_keeps_its_original_text_when_the_pack_changes(self): ...
def test_superseded_label_retires_the_old_case(self): ...
def test_rejected_finding_reappearing_is_counted_as_reintroduced(self): ...
def test_reviewer_failure_counts_as_error_not_as_kept(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: permanent replay set from human reviews"`.

---

### Task 4: Promotion gate, ledger and rollback

**Files:**
- Create: `validation/learning/promotion.py`; subcommand `promote-check`
- Create: `docs/validation/ITERATIONS.md` (Iteration Compact template, then one Observation Ledger
  entry per iteration; the first compact is copied from the spec)
- Create: `validation/reference/versions.jsonl` (append-only: version id, card hash, prompts version,
  date, decision, report path)
- Test: `validation/tests/test_promotion.py`

**Interfaces:**
- Produces:
  ```python
  PROMOTION_GATES = {
      "replay_reintroduced_absent": ("max", 0),
      "replay_lost_present_rate":   ("max", 0.05),
      "replay_error_rate":          ("max", 0.05),
      "lab_forbidden_rate":         ("max", 0.0),
      "run_completion":             ("min", 0.95),
  }
  def assert_promotion_ready(metrics: dict[str, float | None]) -> None     # raises ValueError
  def slice_regressions(baseline: dict, candidate: dict, min_n: int = 10) -> list[dict]
  def decide(metrics: dict, regressions: list[dict]) -> dict   # {"promote": bool, "reasons": [...]}
  def record(path: Path, version: str, decision: dict, report: Path) -> None
  ```
- `assert_promotion_ready` fails closed: a missing or `None` metric is a failure, named in the error.
- `slice_regressions` compares per-card and per-`bloc_mix` kept rates on the replay set; a slice with
  at least `min_n` cases whose kept rate falls is a regression. Any regression blocks promotion.
- Rollback: `versions.jsonl` names the previous promoted version; `docs/validation/ITERATIONS.md`
  states the procedure — check out that version's card and prompt files, reassemble the site from the
  previous `biasguard.json`, which every build keeps as `biasguard.prev.json`. `pipeline/capraz_pipeline/build.py`
  copies the existing file to `.prev` before overwriting; add that with a test in `pipeline/tests/test_build.py`.

- [ ] **Step 1: Write the failing tests**

```python
def test_missing_metric_fails_closed(self):
    with self.assertRaisesRegex(ValueError, "lab_forbidden_rate"): assert_promotion_ready({...})
def test_none_metric_fails_closed(self): ...
def test_one_reintroduced_rejection_blocks_promotion(self): ...
def test_overall_gain_with_one_bloc_regression_is_refused_and_names_the_bloc(self): ...
def test_small_slice_change_is_not_a_regression(self): ...
def test_clean_candidate_is_promoted_and_recorded(self): ...
def test_versions_file_is_append_only(self): ...
def test_build_keeps_previous_biasguard_json(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement; write `ITERATIONS.md`.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: fail-closed promotion gate, version ledger and rollback"`.

---

### Task 5: Drift and new-insight report

**Files:**
- Create: `validation/learning/insights.py`; subcommand `insights`
- Modify: `site/js/app.js` (review note field gains an optional checkbox `Kartlarda olmayan bir örüntü`;
  stored as `new_pattern: true` on the review document), `site/js/v7/logic.js` (`reviewsExport` carries it),
  `validation/feedback/labels.py` (`Label.new_pattern: bool`)
- Test: `validation/tests/test_insights.py`, `site/tests/logic.test.cjs`

**Interfaces:**
- Produces:
  ```python
  def drift(snapshots: list[list[dict]]) -> list[dict]
      # per card and per bloc_mix: finding rate per event by pack, flagged when the latest pack is
      # outside mean ± 3·sd of earlier packs (needs ≥ 4 earlier packs; otherwise "too little history")
      # each row carries detector_version_changed: bool
  def tier_shift(snapshots) -> dict                  # share ai_confident / needs_human by pack
  def co_occurrence(rows: list[dict], min_events: int = 10) -> list[dict]
      # card pairs found together in ≥ min_events events, with lift; candidates for merge or split
  def new_pattern_notes(labels: list[Label]) -> list[dict]     # notes flagged new_pattern, grouped by shared tokens (trFold-style folding)
  def proposals(co: list[dict], notes: list[dict], rejected_clusters: list[dict]) -> list[dict]
      # [{"kind": "new_card"|"split_card"|"merge_cards"|"reword_card", "evidence": {...}, "next": "write a lab candidate"}]
  ```
- `insights` writes `docs/validation/reports/insights-<pack>.md`. Every proposal ends with the same
  next step: write it as a lab candidate (Plan 2) and pass promotion (Plan 4, Task 3 or this plan's
  Task 4). Nothing is added to a catalogue from this report directly.
- A proposal needs at least 5 supporting notes or 10 events; below that it is listed under "watching".

- [ ] **Step 1: Write the failing tests**

```python
def test_drift_needs_four_earlier_packs(self): ...
def test_spike_with_unchanged_detector_is_flagged_as_data_drift(self):
    self.assertFalse(drift(snaps)[0]["detector_version_changed"])
def test_pairs_below_min_events_are_not_reported(self): ...
def test_new_pattern_notes_group_turkish_variants(self):       # "başlıkta soru işareti" / "Başlıkta soru isareti"
def test_proposal_requires_minimum_support_else_watching(self): ...
def test_report_never_writes_to_a_catalogue(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Run every suite, commit and push**

```bash
git commit -am "feat: drift, co-occurrence and new-pattern proposals"
git push -u origin claude/zen-ptolemy-7bvru2
```

---

## The loop, once built

| When | Command | Who acts on it |
|---|---|---|
| Every build | `python -m validation.learning snapshot` | automatic |
| After reviewers work | `python -m validation.feedback import …` then `status` | owner |
| Weekly, or after 50 new reviews | `errors`, `replay build`, `insights` | owner reads the two reports |
| Before changing cards or prompts | write the Iteration Compact in `ITERATIONS.md` | owner / builder |
| After the change | reviewer run on replay + lab, then `promote-check` | owner starts the run |
| After the decision | Observation Ledger entry; `versions.jsonl` row | builder |

## Skill lanes deliberately not used

Feature stores, training pipelines, model artefacts, online serving, canary or A/B rollout, latency
budgets and GPU checks do not apply: the detector is a set of cards and prompts run in batch, and the
site is static. Monitoring is the two reports above, read by a person.
