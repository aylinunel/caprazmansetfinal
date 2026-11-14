# Medyanın Oyunları Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect media techniques in headlines and ledes and show them as "Medyanın oyunları", a group separate from behavioural biases.

**Architecture:** Media techniques get their own catalogue file and entry type, so the 116 behavioural cards are untouched. Each card is first written as a lab candidate and tested on rendered cases; only cards that pass the lab controls are copied into the production media catalogue. The news review runs behavioural and media cards as two separate passes, and the site groups findings by entry type.

**Tech Stack:** Python 3.12, `unittest`; plain JavaScript, `node --test`.

**Spec:** `docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md` (section "Medyanın oyunları")

## Global Constraints

- Prerequisites: Plan 2 (lab) and Plan 3 (tiers and badges).
- Group names, fixed: `Medyanın oyunları` and `Davranışsal yanlılıklar`.
- The 17 concepts that get cards: `ad_hominem`, `causal_overclaim`, `cherry_picking`,
  `consequence_framing`, `emphasis_framing`, `episodic_framing`, `false_dilemma`, `fear_appeal`,
  `labeling`, `loaded_language`, `metaphorical_framing`, `responsibility_framing`,
  `selective_statistics`, `spin`, `strawman`, `thematic_framing`, `word_choice`.
- The 9 that do not: `source_selection`, `one_sided_sourcing`,
  `commission_and_omission_of_information`, `contextual_omission`, `size_allocation`,
  `story_placement`, `picture_selection`, `picture_explanation`, `event_selection`. They appear only
  in a list titled `Bu veriyle ölçülemiyor`.
- A media card describes what the text does. No card, prompt or site string states intent, deception,
  motive or affiliation.
- Card definitions come from `validation/mesa_bias_expanded/specs/<id>.json` (definition and
  annotation boundary) and `data/reference/editorial.json`. Every card records that provenance.
- `thematic_framing` and `spin` are context effects: `review_policy: "effect_context_only"`.
- No score from the deterministic scorer (`shared/analysis/rules.cjs`) is merged with an AI finding.
- `biasguard/data/cards.json` is not changed.
- Follow the owner's standing instructions: `ponytail` and `anthropic-skills:karpathy-guidelines`.

## Review Focus

1. A headline that quotes someone else's loaded phrase in order to report or reject it → not a finding
   against the outlet. (Tasks 2, 3)
2. An opinion column or an attributed statement → the card's non-examples cover it; lab control exists. (Task 2)
3. The same headline matched by `loaded_language`, `word_choice` and `labeling` at once → shown as
   separate findings, never added up into a count that reads as severity. (Task 5)
4. A media card missing from the production file because it failed the lab → the site lists it under
   `Henüz yayında değil`, not silently absent. (Tasks 3, 5)
5. An event reviewed for behavioural cards but not yet for media cards → the media group shows
   `incelenemedi`, not an empty clean group. (Tasks 4, 5)

---

### Task 1: Media entry type and separate catalogue

**Files:**
- Modify: `biasguard/catalog.py` (`ENTRY_TYPES` gains `"media_practice"`; `REVIEW_POLICIES` gains
  `"media_pattern_review"`)
- Create: `biasguard/data/media_cards.json` (`[]` at first)
- Test: `biasguard/test_catalog_media.py`

**Interfaces:**
- Produces:
  ```python
  def load_media_cards() -> list[dict]          # [] when the file holds no cards; never raises for empty
  def load_cards() -> list[dict]                # unchanged: the 116 behavioural cards
  ```
- `engine.py`: a finding from a `media_pattern_review` card adjudicates like `bias_error_review`
  (`pattern_supported`), and carries `entry_type: "media_practice"`.

- [ ] **Step 1: Write the failing tests**

```python
def test_behavioural_catalogue_is_unchanged(self):
    self.assertEqual(len(load_cards()), 116)
    self.assertFalse(any(c.get("entry_type") == "media_practice" for c in load_cards()))
def test_empty_media_catalogue_loads_as_empty_list(self): ...
def test_media_card_validates_with_new_entry_type_and_policy(self): ...
def test_media_finding_carries_entry_type(self): ...     # BiasGuard(cards=[media_card], reviewer=stub)
def test_unknown_entry_type_still_rejected(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run with `biasguard.test_news`; confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: media_practice entry type and separate catalogue"`.

---

### Task 2: Seventeen candidate cards and their lab cases

**Files:**
- Create: `validation/biaslab/proposed_cards/<card-id>.json` × 17 (the `selective-statistics` file from
  Plan 2 is updated to `entry_type: "media_practice"`, `review_policy: "media_pattern_review"`)
- Modify: `validation/biaslab/renderer.py` (one template family per concept), `validation/biaslab/configs.py`,
  `validation/biaslab/crosswalk.json` (the 17 get `detector_id`, `relationship: "equivalent_within_task"`,
  `review_status: "pilot"`)
- Test: `validation/tests/test_media_cards.py`, `validation/tests/test_renderer_media.py`

**Interfaces:**
- Card id = concept id with `-`. Each card has: `definition`; 2–4 `necessary_conditions`, each
  checkable from headline, lede or supplied context; at least 3 `non_examples`, always including
  (a) quoted or attributed speech that the outlet reports or rejects, (b) an opinion column or
  interview, (c) the technique's legitimate use; `limitations` stating "Metnin ne yaptığını tanımlar;
  niyet hakkında bir şey söylemez."; `provenance` naming the spec file.
- Renderer: for each concept, kinds `positive`, `inactive_control`, `quoted_control` at minimum, two
  surface variants, all passing `assert_no_leak`. `boundary_control` where the Mesa plugin's boundary
  scenario renders differently from its positive.
- `configs.catalog("candidate")` = behavioural cards + all proposed cards.

- [ ] **Step 1: Write the failing tests**

```python
IDS = [...]  # the 17 ids

def test_all_seventeen_cards_exist_and_validate(self): ...
def test_every_card_has_quoted_speech_and_opinion_non_examples(self): ...
def test_no_card_text_mentions_intent(self):
    for card in cards:
        self.assertNotRegex(json.dumps(card, ensure_ascii=False).casefold(),
                            r"kasıt|kasten|niyet(?!.*söylemez)|intent(?!.*not)|deliberate|manipül")
def test_context_effect_cards_have_context_only_policy(self): ...   # thematic-framing, spin
def test_every_concept_renders_three_kinds_and_passes_leak_check(self): ...
def test_quoted_control_attributes_the_phrase_to_a_named_speaker(self): ...
def test_candidate_catalogue_has_133_cards(self): ...               # 116 + 17
def test_crosswalk_resolves_exactly_the_seventeen_plus_illusory_truth_on_candidate(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Write the cards and templates.** Work concept by concept from the spec file; where the
  spec's annotation boundary and `editorial.json` disagree, follow the narrower one and note it in
  `limitations`.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Owner review.** List the 17 definitions and conditions in
  `docs/validation/media-cards-for-review.md` for the owner to approve or edit. Do not continue to
  Task 3 for a card the owner has not approved.
- [ ] **Step 6: Commit** — `git commit -m "feat: seventeen candidate media-technique cards with lab cases"`.

---

### Task 3: Lab run and promotion

**Files:**
- Create: `validation/biaslab/promote.py`; subcommand `promote` in `validation/biaslab/__main__.py`
- Create: `docs/validation/media-lab-run.md` (the recorded result)
- Test: `validation/tests/test_promote.py`

**Interfaces:**
- Produces:
  ```python
  def promotable(report: dict, card_id: str) -> tuple[bool, list[str]]
  def promote(report_path: Path, approved: Sequence[str]) -> list[str]   # writes biasguard/data/media_cards.json
  ```
- A card is promotable when, in the candidate config of the lab report, for that card's cases:
  completion is 1.0; no `quoted_control`, `inactive_control` or `boundary_control` case has a
  forbidden status; no `missing_context` case has a forbidden status; at least one `positive` case is
  `supported` or `contextual_effect`; and the card id is in `approved`.
- `promote` copies promotable cards into `media_cards.json` (sorted by id, provenance extended with the
  lab run id) and returns the ids that were refused, each with its reasons. It never removes a card
  already promoted; removal is a separate, explicit edit.
- This step needs a reviewer run for the lab cases (`tasks` → reviewer agents → `score`, as in
  `biasguard/AGENT_REVIEW.md`). That run costs model usage and is started by the owner.

- [ ] **Step 1: Write the failing tests** (synthetic report dicts)

```python
def test_card_with_a_forbidden_control_is_refused_with_reason(self): ...
def test_card_with_no_supported_positive_is_refused(self): ...
def test_unapproved_card_is_refused_even_if_clean(self): ...
def test_incomplete_cases_block_promotion(self): ...
def test_promote_writes_only_promotable_cards_sorted(self): ...
def test_promote_never_touches_cards_json(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Owner-run lab pass, then** `python -m validation.biaslab promote --report runs/lab/<name>/report.json --approved <ids>`; write the outcome per card into `docs/validation/media-lab-run.md`.
- [ ] **Step 6: Commit** — `git commit -m "feat: lab-gated promotion of media cards"`.

---

### Task 4: Media pass in the news review

**Files:**
- Modify: `biasguard/news.py` (`--catalog behavioural|media` on `tasks` and `apply`; media run folder
  `runs/bg-media`), `biasguard/AGENT_REVIEW.md` (the media pass, same rules)
- Modify: `pipeline/capraz_pipeline/build.py` (optional key `BGM` ← `<out>/biasguard-media.json`)
- Test: `biasguard/test_news.py`, `pipeline/tests/test_build.py`

**Interfaces:**
- `apply(run, catalog="behavioural", card_status_path=None)`; with `catalog="media"` it uses
  `load_media_cards()` and writes the same result shape, each finding carrying
  `entry_type: "media_practice"`, `tier` and `tier_reasons` (Plan 3 rule, unchanged).
- With an empty media catalogue, `tasks --catalog media` writes nothing and exits 0 with the message
  `media catalogue is empty`.
- `core.bin` key `BGM` has the same structure as `BG`.

- [ ] **Step 1: Write the failing tests**

```python
def test_media_apply_uses_only_media_cards(self): ...
def test_default_catalog_behaviour_is_unchanged(self): ...
def test_empty_media_catalogue_writes_no_tasks(self): ...
def test_media_findings_are_tiered(self): ...
def test_build_adds_bgm_only_when_file_exists(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: media-technique pass in the news review"`.

---

### Task 5: The "Medyanın oyunları" group on the site

**Files:**
- Modify: `site/js/v7/logic.js`, `site/js/app.js` (`bg7*` rendering), `site/js/v7/olay.js`,
  `site/js/v7/yontem.js`, `site/styles.css`
- Test: `site/tests/logic.test.cjs`, `site/tests/smoke.cjs`
- Regenerate: `public/index.html`

**Interfaces:**
- `logic.js`:
  ```js
  // → [{group: "Medyanın oyunları"|"Davranışsal yanlılıklar", state: "ok"|"incelenemedi", findings: [...]}]
  function findingGroups(bgEvent, bgmEvent)
  // → {scorer: [{key, label}], ai: [{id, name}], notMeasurable: [names], notLive: [names]}
  function mediaCoverage(scorerKeys, mediaCards, allMediaConcepts)
  ```
  `findingGroups` puts `Medyanın oyunları` first; a group with `state: "ok"` and no findings is
  omitted; a missing or incomplete media review gives `state: "incelenemedi"`.
- Event page: two headed groups. Under `Medyanın oyunları`, AI findings (with Plan 3 badges) and the
  deterministic scorer's matched rules for that event's headlines are shown as two labelled lists,
  `YZ incelemesi` and `Kural tabanlı ölçüm`. No combined count.
- Each media finding shows the outlets whose headline holds the quote (the existing `o` field).
- Method page: the 26 concepts in three lists — live, `Henüz yayında değil`, `Bu veriyle ölçülemiyor` —
  from `mediaCoverage`, plus the sentence "Bu bulgular metnin ne yaptığını tanımlar; niyet hakkında
  bir şey söylemez."

- [ ] **Step 1: Write the failing tests**

```js
test('media group comes first and behavioural second', ...);
test('event without media review shows incelenemedi, not an empty group', ...);
test('group with a completed review and no findings is omitted', ...);
test('mediaCoverage sorts 26 concepts into live, not live and not measurable', () => {
  const c = mediaCoverage(SCORER_KEYS, [{id:'labeling',name:'Etiketleme'}], ALL26);
  assert.equal(c.notMeasurable.length, 9);
  assert.equal(c.ai.length + c.notLive.length, 17);
});
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement; extend the smoke test** to assert both group headings' rules and the intent sentence on the method page.
- [ ] **Step 4: Regenerate `public/index.html`; run logic and smoke tests; confirm pass.**
- [ ] **Step 5: Run every suite, commit and push**

```bash
git commit -am "feat: Medyanın oyunları group on event and method pages"
git push -u origin claude/zen-ptolemy-7bvru2
```
