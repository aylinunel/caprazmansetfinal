# Review Status and Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show every AI finding on the public feed with an honest status (YZ emin, İnsan kontrolü bekliyor, İnsan doğruladı, İnsan düzeltti), and turn editor reviews into data the detector can learn from.

**Architecture:** A routing rule in `biasguard/news.py` stamps each finding with a tier when results are applied. The existing owner-only editor review (`rev7`, artifact `reviews` collection) gains an "approve" action and an export. A small package `validation/feedback/` imports those reviews into an append-only label file, computes per-card verify-pass precision, and writes a card-status file that the next build feeds back into routing.

**Tech Stack:** Python 3.12 standard library, `unittest`; plain JavaScript in `site/`, `node --test`.

**Spec:** `docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md` (section "Owner decisions")

## Global Constraints

- Prerequisite: the Foundation plan. This plan does not need the Mesa lab.
- Tiers are exactly `ai_confident` and `needs_human`. Review outcomes are exactly `verified`,
  `corrected`, `rejected`.
- Turkish display text, fixed: `YZ emin`, `İnsan kontrolü bekliyor`, `İnsan doğruladı`,
  `İnsan düzeltti`. Tooltip for `YZ emin`: `İki ayrı YZ incelemesi aynı sonuca vardı; henüz insan
  kontrolünden geçmedi.`
- `ai_confident` is a rule, never a number. No percentage or score is shown with it.
- A failed or missing review stays `analysis_incomplete` / `not_attempted` and is shown as
  `incelenemedi`; it never becomes a finding or a clean result.
- A review applies only to the data-pack version and event-text hash it was made on. On any other
  version the finding is shown by its tier again.
- Reviewer identity is not stored in the repo; the label file records `owner` only.
- Label and status files are append-only or regenerated whole; nothing is hand-edited.
- Thresholds live in `validation/reference/gates.json` with the recommended values and
  `"agreed": false`. While not agreed, card demotion and hiding are computed and reported but not applied.
- Precision from editor reviews is labelled "verify-pass precision" everywhere; it is not called accuracy.
- `pipeline/`, `biasguard/` and `site/` do not import from `validation/`; they read files.
- Site strings are escaped with the existing `esc`. `public/index.html` is regenerated, never edited.
- Follow the owner's standing instructions: `ponytail` and `anthropic-skills:karpathy-guidelines`.

## Review Focus

1. Today's data: 439 findings, all `needs_context` → every one is `needs_human`; the page must not
   show an empty "YZ emin" section or a zero as if it were a result. (Tasks 1, 5)
2. A review stored against an older pack or a changed event text → ignored, finding shown by tier. (Task 3)
3. An exported reviews file with an unknown key shape, an unknown status or a duplicate key → the
   import rejects the whole file and names the entry; nothing is appended. (Task 3)
4. A card with zero reviews → precision "not estimable"; it is never demoted, hidden or promoted. (Task 4)
5. The audit sample must be the same findings on every rebuild of the same pack, or reviewers would
   chase a moving list. (Task 2)

---

### Task 1: Routing rule

**Files:**
- Create: `biasguard/routing.py`
- Modify: `biasguard/news.py` (`apply`: add `tier` and `tier_reasons` to each slim finding; add
  `aiConfident` and `needsHuman` counts to `summary`)
- Test: `biasguard/test_routing.py`

**Interfaces:**
- Produces:
  ```python
  def tier(finding: dict, rejected_for_card: int, card_status: str | None) -> tuple[str, list[str]]
  ```
  `finding` is the engine's full finding (before slimming); `card_status` is `None`, `"eligible"`,
  `"demoted"` or `"hidden"`.
- `ai_confident` only if all hold; otherwise `needs_human` with one reason per failed check, in this
  order and wording:
  | check | reason |
  |---|---|
  | `finding["status"]` is `pattern_supported` or `contextual_effect_consensus` | `incelemeler hemfikir değil` |
  | every necessary condition `satisfied` for both roles | `koşul doğrulanamadı` |
  | `finding["missing_context"]` empty | `eksik bağlam var` |
  | `rejected_for_card == 0` | `alıntı reddedildi` |
  | `card_status != "demoted"` | `insan incelemeleri bu kavramda yetersiz buldu` |
- `card_status == "hidden"` → the finding is dropped by `apply` and counted in `summary["hiddenByGate"]`.
- `apply(run, card_status_path=None)` reads the optional status file written by Task 4.

- [ ] **Step 1: Write the failing tests** (reuse the stub reviewer pattern from `biasguard/test_news.py`)

```python
def test_unanimous_complete_finding_is_ai_confident(self):
    self.assertEqual(tier(finding(status="pattern_supported"), 0, None), ("ai_confident", []))
def test_needs_context_is_needs_human_with_reason(self):
    self.assertEqual(tier(finding(status="needs_context"), 0, None)[1][0], "incelemeler hemfikir değil")
def test_missing_context_blocks_confidence(self): ...
def test_unsatisfied_condition_blocks_confidence(self): ...
def test_rejected_quote_blocks_confidence(self): ...
def test_demoted_card_is_needs_human(self): ...
def test_reasons_accumulate_in_fixed_order(self): ...
def test_apply_stamps_every_finding_and_counts_tiers(self):
    out = apply(run); f = out["events"][0]["uncertain"][0]
    self.assertEqual(f["tier"], "needs_human")
    self.assertEqual(out["summary"]["aiConfident"] + out["summary"]["needsHuman"], total_findings(out))
def test_apply_drops_findings_of_hidden_cards_and_counts_them(self): ...
def test_apply_without_status_file_behaves_as_before_plus_tier(self): ...
```

- [ ] **Step 2: Run and confirm failure** — `python -m unittest biasguard.test_routing -v`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run `biasguard.test_routing` and `biasguard.test_news`; confirm pass.**
- [ ] **Step 5: Check against real data**

Run: `python -m biasguard.news apply --run runs/bg --out /tmp/bg-tier.json`
Expected: `summary.needsHuman == 439`, `summary.aiConfident == 0`, statuses unchanged from `core.bin`.
Record the actual numbers in the commit message.

- [ ] **Step 6: Commit** — `git commit -m "feat: tier every BiasGuard finding as ai_confident or needs_human"`.

---

### Task 2: Review queue and audit sample

**Files:**
- Modify: `biasguard/routing.py`
- Modify: `biasguard/news.py` (`apply`: add `audit: true` to sampled findings; write `review_queue`)
- Test: `biasguard/test_routing.py`

**Interfaces:**
- Produces:
  ```python
  def in_audit_sample(event: str, card_id: str, pack_version: str, rate: float = 0.10) -> bool
  def review_queue(events: list[dict], reviewed_counts: dict[str, int]) -> list[dict]
      # [{"event", "card_id", "why": "needs_human"|"audit", "priority": int}], highest priority first
  ```
- `in_audit_sample` is deterministic: `int(sha256(f"{pack_version}|{event}|{card_id}")[:8], 16) / 2**32 < rate`.
- Queue order: `needs_human` and audit findings of cards with the fewest human reviews first; ties by
  number of outlets in the event, descending; then event id.
- `pack_version` is `core["meta"]["built"]` as written by the pipeline.

- [ ] **Step 1: Write the failing tests**

```python
def test_audit_sample_is_stable_for_a_pack(self): ...
def test_audit_sample_changes_with_pack_version(self): ...
def test_audit_rate_is_close_to_ten_percent_over_many_keys(self):   # 10,000 keys → 800..1200
def test_queue_puts_least_reviewed_cards_first(self): ...
def test_queue_contains_every_needs_human_finding_once(self): ...
def test_ai_confident_outside_sample_is_not_queued(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: deterministic audit sample and review queue"`.

---

### Task 3: Editor review, approve action, export and import

**Files:**
- Modify: `site/js/app.js` (review controls near `rev7Save`, line ~6693; admin export button)
- Modify: `site/js/v7/logic.js` (pure helpers), `site/tests/logic.test.cjs`
- Create: `validation/__init__.py` (if absent), `validation/feedback/__init__.py`,
  `validation/feedback/labels.py`, `validation/feedback/__main__.py`
- Create: `validation/reference/labels.jsonl` (empty), `validation/reference/README.md`
- Test: `validation/tests/__init__.py`, `validation/tests/test_feedback_labels.py`

**Interfaces:**
- Site: a third action `approve` next to reject/correct, stored as `status: "verified"`. Every review
  document now also stores `pack: <meta.built>` and `text: <sha256 of the event text shown>`.
  Existing documents without those fields are treated as made on the pack in which they are first
  seen, and are re-saved with the fields by the owner's next visit.
- `logic.js`:
  ```js
  // returns {state: "dogrulandi"|"duzeltildi"|"reddedildi"|"yz_emin"|"insan_bekliyor", label, tip}
  function reviewState(finding, review, packVersion, textHash)
  function reviewsExport(REV7, packVersion)   // → JSON-serialisable {pack, exported_at, reviews: [{key, status, note, at, pack, text}]}
  ```
  A review whose `pack` or `text` differs from the current one is ignored by `reviewState`.
- Admin page: a button `İncelemeleri indir` that downloads `reviewsExport(...)` as
  `reviews-<pack>.json`. Owner-only, like the existing controls.
- Python:
  ```python
  @dataclass(frozen=True)
  class Label:
      event: str; card_id: str; pack_version: str; text_sha256: str
      outcome: str              # verified | corrected | rejected
      note: str; tier_at_review: str; audit: bool; reviewed_at: str

  def import_export(export: dict, results: dict, known_cards: set[str]) -> list[Label]   # raises ValueError
  def append(path: Path, labels: Sequence[Label]) -> int     # all-or-nothing; skips exact duplicates; returns added
  def read(path: Path) -> list[Label]
  ```
  `results` is the `biasguard.json` for that pack; it supplies `tier_at_review` and `audit`.
  CLI: `python -m validation.feedback import <reviews.json> --results <biasguard.json>`.
- `import_export` rejects the whole file on: key not shaped `<event>__<card>`, unknown status, unknown
  card, event/card pair absent from `results`, duplicate key, or `pack` different from `results`' pack.
  Keys beginning `narr__` are skipped and counted (narrative reviews are out of scope here).

- [ ] **Step 1: Write the failing tests**

```js
test('verified review on the current pack shows İnsan doğruladı', ...);
test('corrected review shows İnsan düzeltti', ...);
test('review from another pack is ignored and tier is shown', ...);
test('review on changed event text is ignored', ...);
test('unreviewed ai_confident shows YZ emin with the fixed tooltip', ...);
test('unreviewed needs_human shows İnsan kontrolü bekliyor', ...);
test('reviewsExport carries pack and text for every review', ...);
```

```python
def test_import_round_trip(self): ...
def test_narrative_reviews_are_skipped_and_counted(self): ...
def test_unknown_status_rejects_whole_file(self): ...
def test_pair_not_in_results_rejects_whole_file(self): ...
def test_pack_mismatch_rejects_whole_file(self): ...
def test_append_is_all_or_nothing_and_idempotent(self): ...
def test_label_file_has_no_reviewer_identity(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement site helpers, controls and export; implement the Python import.**
- [ ] **Step 4: Run and confirm pass** — `node --test site/tests/logic.test.cjs`; `python -m unittest discover -s validation/tests -t . -v`.
- [ ] **Step 5: Add a CI job `feedback`** running the `validation/tests` command; assert it in `tests_repo/test_ci.py`.
- [ ] **Step 6: Commit** — `git commit -m "feat: approve action, review export and label import"`.

---

### Task 4: Card statistics and gate

**Files:**
- Create: `validation/feedback/stats.py`, `validation/reference/gates.json`
- Modify: `validation/feedback/__main__.py` (subcommand `status`)
- Test: `validation/tests/test_feedback_stats.py`

**Interfaces:**
- Produces:
  ```python
  def wilson_lower(successes: int, n: int, z: float = 1.6449) -> float | None    # one-sided 95%
  def card_stats(labels: Sequence[Label]) -> dict[str, dict]
      # card → {"reviewed", "kept", "rejected", "precision", "lower",
      #         "audit_reviewed", "audit_kept", "audit_precision", "by_tier": {...}}
  def card_status(stats: dict, gates: dict) -> dict[str, dict]
      # card → {"status": "eligible"|"demoted"|"hidden"|"unjudged", "applied": bool, "reasons": [...]}
  ```
- `kept` = `verified` + `corrected` (the pattern was present; the wording needed fixing). `precision` =
  kept / reviewed; `None` when reviewed is 0.
- `gates.json`:
  ```json
  {"agreed": false,
   "min_run_completion": 0.95,
   "min_reviews_to_judge": 30,
   "min_precision_lower_bound": 0.85,
   "hide_min_reviews": 20,
   "hide_below_precision": 0.50,
   "audit_rate": 0.10}
  ```
- Rules: fewer than `hide_min_reviews` reviews → `unjudged`. Precision below `hide_below_precision`
  with at least `hide_min_reviews` → `hidden`. At least `min_reviews_to_judge` and lower bound below
  `min_precision_lower_bound` → `demoted`. At least `min_reviews_to_judge` and lower bound at or above
  it → `eligible`. Otherwise `unjudged`. `applied` is `gates["agreed"]`.
- `status` command writes `validation/reference/card_status.json`
  (`{pack_version, generated_at, agreed, cards}`) and prints a table. `biasguard.news apply
  --card-status <file>` (Task 1) honours only entries with `applied: true`.

- [ ] **Step 1: Write the failing tests**

```python
def test_wilson_known_values(self):
    self.assertIsNone(wilson_lower(0, 0))
    self.assertAlmostEqual(wilson_lower(30, 30), 0.9173, places=3)
    self.assertLess(wilson_lower(28, 30), 0.85); self.assertGreater(wilson_lower(29, 30), 0.85)
def test_card_with_no_reviews_is_unjudged_with_none_precision(self): ...
def test_corrected_counts_as_kept(self): ...
def test_29_of_30_is_eligible_and_28_of_30_is_demoted(self): ...
def test_9_of_20_is_hidden(self): ...
def test_nothing_is_applied_while_not_agreed(self):
    self.assertFalse(any(c["applied"] for c in card_status(stats, GATES).values()))
def test_audit_precision_uses_only_audit_sampled_ai_confident_findings(self): ...
def test_every_status_has_a_reason(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: verify-pass card statistics and gate"`.

---

### Task 5: Status badges on the public pages

**Files:**
- Modify: `site/js/app.js` (`bg7finding`, `bg7Live`, summary block), `site/js/v7/olay.js`,
  `site/styles.css`, `site/js/v7/yontem.js` (one paragraph in the AI-review section)
- Modify: `site/tests/smoke.cjs`
- Regenerate: `public/index.html`

**Interfaces:**
- Consumes: `reviewState` (Task 3), `tier` on findings (Task 1).
- Each finding's summary line shows its badge after the name. Findings are ordered: İnsan doğruladı,
  İnsan düzeltti, YZ emin, İnsan kontrolü bekliyor. Rejected findings are not rendered (existing
  behaviour).
- The event's AI section opens with one line built from counts that are non-zero only, for example
  `3 bulgu insan kontrolü bekliyor.` No "0 YZ emin" text.
- Method page paragraph states: what each badge means, that YZ emin is agreement between two AI
  reviews and not a measured accuracy, and that findings may be missed.
- Old data without `tier` renders every unreviewed finding as `İnsan kontrolü bekliyor`.

- [ ] **Step 1: Extend the smoke test** to assert, on an event page with findings: every finding row
  has exactly one badge from the four labels; no text matches `/\b0 (YZ emin|bulgu)/`; the method page
  contains the `YZ emin` explanation sentence.
- [ ] **Step 2: Run and confirm failure** — `node site/tests/smoke.cjs public /tmp/smoke-out`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Regenerate and run**

Run: `cd pipeline && python3 -c "from pathlib import Path; from capraz_pipeline import site; site.assemble(Path('../public/data'), Path('../public'))"`
Run: `node --test site/tests/logic.test.cjs` and `node site/tests/smoke.cjs public /tmp/smoke-out`
Expected: pass; with today's pack every finding shows `İnsan kontrolü bekliyor`.

- [ ] **Step 5: Run every suite, commit and push**

```bash
git commit -am "feat: review status badges on event pages"
git push -u origin claude/zen-ptolemy-7bvru2
```

---

## What this plan does not do

- Rebuild `core.bin` with tiers. That needs a pipeline build from the collector export; until then the
  site falls back to `İnsan kontrolü bekliyor` for all 439 findings, which is also what the rule gives.
- Measure recall, or precision free of reviewer anchoring. See
  `parked/2026-11-14-blind-reference-study.md`.
- Apply demotion or hiding. That starts when the owner sets `"agreed": true` in `gates.json`.
