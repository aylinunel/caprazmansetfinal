# Machine Learning for the Narrative Map and the Behavioural Review — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the narrative coding (Anlatı haritası) and the behavioural bias review (BiasGuard) a human answer key, measure the AI against it, let the AI learn from it without retraining, and stand up the first trained baselines, so that every later model has a number to beat.

**Architecture:** A new package `validation/answerkey/` turns human coding into one append-only record (blind packets out, desk exports in, agreement and gold out). Blind coding happens in a blind mode of the AI denetim masası (`site/js/v7/desk.js`): packets ship in core key `BLIND` without the AI's verdicts, and the desk's review export is imported back. There is one expert (the owner), so agreement is same-coder consistency: a second blind pass at least 14 days after the first. The narrative pipeline gains a task builder whose few-shot examples never include the event being coded, so the agent can be scored against the human-coded weeks. `validation/mlbench/` trains and cross-validates small scikit-learn models against the same gold. The measured narrative quality is shipped as core key `NQ` and shown on the narrative page.

**Tech Stack:** Python 3.13, `unittest`, scikit-learn and SciPy (already in `pipeline/requirements.txt`); plain JavaScript in `site/`, tested with `node site/tests/logic.test.cjs`.

**Spec:** the stakeholder report "Çapraz Manşet: How the Algorithm Works", section "The machine-learning part" (https://claude.ai/artifact/9szRkwkQAYjcGzeGMw1Xv1), and the loop in `docs/validation/ITERATIONS.md`. For the two algorithms named here, this plan implements stages 1, 2 and 4 and the baseline half of stage 6 of that report. Stage 3 (re-testing the media cards) and stage 5 (the section sorter) concern other parts of the system and are not in this plan; stages 6–7 proper are deferred (see the end).

## Global Constraints

- Gold labels come from people only. AI output (agent codings, BiasGuard findings) is never written as, merged into or resolved as gold.
- Coders are stored as anonymous slots: a letter for the person and a digit for the pass (`"A1"`, `"A2"`; a second person would be `"B1"`). Never a name, email or user id (same rule as `validation/feedback/labels.py`).
- One expert (owner decision, 2026-11-21): agreement is measured between two blind passes of the same coder. A second pass opens at least 14 days after its packet is made from the first, never shows the first pass's answers, and every report names the measure "same-coder consistency (two passes ≥ 14 days apart)", never "inter-coder agreement".
- Blind coding happens only in the desk's blind mode (owner decision, 2026-11-21): a blind item shows no AI verdict, AI coding, confidence, quote highlight, earlier answer or link to the event page. The private key (which items the AI showed) never enters core.
- A field is *usable* (for measurement, examples or training) only when its items coded in two passes reach Krippendorff's alpha ≥ 0.67 on at least 30 items. Below that, reports print the number and say "not usable yet".
- Stage-1 targets from the report: 300 behavioural gold items, at least 20 per live concept; narrative: the 61 human-coded events (weeks v1, w1–w6) plus 20 of them re-coded blind by the owner (pass `A2`).
- Assumption to confirm with the owner: the existing hand-coded weeks are the owner's own coding, so core rows are slot `A1` (`CORE_SLOT` in Task 3). If someone else coded them, `CORE_SLOT` becomes `"H1"` and the narrative report reads "between coders".
- Cross-validation splits by event (a narrative key or an event id): no event has rows in both train and test.
- Few-shot examples shown to an AI coder or reviewer never come from an event in the same batch.
- No new dependencies. Random seeds use `PARAMS.random_state` = `20261028` from `pipeline/capraz_pipeline/config.py`.
- Nothing trained in this plan changes what the public site shows as a finding. The only public change is the measured-quality sentence of Task 9.
- Turkish for everything a coder or reader sees; English for code, comments and reports in `docs/validation/reports/`.
- Commit messages end with the session's attribution lines. Do not commit `.10x/` state files.

## Review Focus

1. **A blind item that gives the answer away**: the coder expects to see only the headline(s) and the concept, never the AI's verdict, an AI-coded narrative value, an "AI imzalı" badge or an earlier pass's answer. Pinned in Task 5 (`blindItemHtml` test).
2. **An export holding an item no packet has** (an old export, a renamed packet, a hand-edited file): the owner expects a refusal naming the review key, and nothing half-imported. Pinned in Task 4.
3. **Opening the second pass too early**: the coder expects the pass to stay locked with its opening date until 14 days have passed. Pinned in Tasks 4 and 5.
4. **An example leaking into its own test**: coding event X with event X among the examples inflates the agreement number. Pinned in Tasks 6 and 8.
5. **A class missing from a training fold** (for example no `implied` blame in one fold): the expected result is a prediction of a known class, not a crash. Pinned in Task 9.

---

### Task 1: Agreement statistic

**Files:**
- Create: `validation/answerkey/__init__.py` (empty), `validation/answerkey/agreement.py`
- Test: `validation/tests/test_answerkey.py`

**Interfaces:**
- Produces: `krippendorff_alpha(units: Sequence[Sequence[str | None]]) -> float | None` (nominal alpha; a unit is one item's values across coders, `None` = not coded; units with fewer than 2 values are ignored; returns `None` when fewer than 2 pairable values or no expected disagreement). `percent_agreement(units) -> float | None` (share of units with ≥ 2 values whose values are all equal).

- [ ] **Step 1: Write the failing tests**

```python
class AlphaTest(unittest.TestCase):
    def test_textbook_example(self):  # Krippendorff (2011), "Computing Krippendorff's alpha", nominal: 0.743
        K = [[1,1,None,1],[2,2,3,2],[3,3,3,3],[3,3,3,3],[2,2,2,2],[1,2,3,4],[4,4,4,4],[1,1,2,1],[2,2,2,2],
             [None,5,5,5],[None,None,1,1],[None,None,3,None]]
        self.assertAlmostEqual(krippendorff_alpha([[None if v is None else str(v) for v in u] for u in K]), 0.743, places=3)
    def test_small_cases(self):
        self.assertAlmostEqual(krippendorff_alpha([["a","a"],["a","a"],["b","b"],["a","b"]]), 0.5333, places=4)
        self.assertEqual(krippendorff_alpha([["a","a"],["b","b"],["c","c"]]), 1.0)
        self.assertIsNone(krippendorff_alpha([["a","a"],["a","a"]]))           # one value only: undefined
        self.assertAlmostEqual(krippendorff_alpha([["a","a",None],["a","b","b"],[None,"c","c"],["a",None,None]]), 0.625, places=4)
    def test_percent(self):
        self.assertEqual(percent_agreement([["a","a"],["a","b"],["c",None]]), 0.5)
```

- [ ] **Step 2: Run to see it fail**

Run: `python3 -m unittest validation.tests.test_answerkey -v`
Expected: FAIL, `ModuleNotFoundError: validation.answerkey`

- [ ] **Step 3: Implement both functions in `validation/answerkey/agreement.py`** with the coincidence-matrix method: each unit with m values adds 1/(m−1) per ordered pair; alpha = 1 − D_o / D_e.

- [ ] **Step 4: Run the tests**

Run: `python3 -m unittest validation.tests.test_answerkey -v`
Expected: PASS

- [ ] **Step 5: Commit** — `feat(answerkey): Krippendorff's alpha`

---

### Task 2: Narrative codebook

The narrative coding is free text (145 different frames, person names as "hero"). Two targets can be learned and compared: how a headline assigns blame, and a frame category.

**Files:**
- Create: `data/reference/narrative_codebook.json`, `validation/answerkey/codebook.py`
- Test: `validation/tests/test_answerkey.py`

**Interfaces:**
- Produces: `HUMAN_STATUSES = ("hand_coded", "headline_coded")`; `BLAME_LEVELS = ("none", "implied", "explicit")`; `load_codebook(path: Path = <data/reference/narrative_codebook.json>) -> dict`; `blame_level(raw: str) -> str`; `frame_category(raw: str, codebook: dict) -> str`; `human_rows(core: dict) -> list[dict]` (every row of every `N` entry whose `status` is in `HUMAN_STATUSES`, each as `{"key": <N key>, **row}`).
- Codebook file shape: `{"approved": false, "categories": [...], "frames": {"<raw frame>": "<category>", ...}}`.

- [ ] **Step 1: Write the failing tests**

```python
class CodebookTest(unittest.TestCase):
    def test_blame_level(self):
        self.assertEqual(blame_level(""), "none")
        for raw in ("—", "Belirtilmiyor", "Belirsiz (ima)"):
            self.assertEqual(blame_level(raw), "none")
        self.assertEqual(blame_level("Yargı (ima)"), "implied")
        self.assertEqual(blame_level("Belediye yönetimi"), "explicit")
    def test_frame_category(self):
        cb = {"categories": ["Yargı ve soruşturma", "Diğer"], "frames": {"Adli süreç": "Yargı ve soruşturma"}}
        self.assertEqual(frame_category(" Adli süreç ", cb), "Yargı ve soruşturma")
        self.assertEqual(frame_category("Adli surec", cb), "Diğer")      # unmapped spelling -> Diğer, never a guess
        self.assertEqual(frame_category("", cb), "Diğer")
    def test_codebook_covers_every_human_frame(self):
        cb = load_codebook()
        core = _load(REPO / "public" / "data" / "core.bin")
        raw = {(r.get("frame") or "").strip() for r in human_rows(core)} - {""}
        self.assertEqual(sorted(raw - set(cb["frames"])), [])
        self.assertTrue(set(cb["frames"].values()) <= set(cb["categories"]))
        self.assertEqual(cb["categories"][-1], "Diğer")
```

- [ ] **Step 2: Run to see them fail**

Run: `python3 -m unittest validation.tests.test_answerkey -v`
Expected: FAIL on import of `validation.answerkey.codebook`

- [ ] **Step 3: Write `data/reference/narrative_codebook.json`** with `"approved": false` and exactly these categories, in this order:
  `"Yargı ve soruşturma"`, `"Olgu aktarımı"`, `"Suç ve güvenlik"`, `"Yolsuzluk ve hesap verebilirlik"`, `"Siyaset ve iktidar"`, `"Ekonomi"`, `"İnsani ilgi"`, `"Basın ve ifade özgürlüğü"`, `"Kriz ve dram"`, `"Spor"`, `"Diğer"`.
  Map every distinct non-empty `frame` of `human_rows(core)` (print them with a one-off script) to the category closest to its idea; when in doubt, `"Diğer"`. Anchors: `Adli süreç`, `Fon soruşturması`, `Suç / ceza` → Yargı ve soruşturma; `Olgu aktarımı`, `Hizmet / bilgi`, `Resmî veri` → Olgu aktarımı; `Güvenlik / FETÖ`, `Mali suç`, `Şüpheli ölüm` → Suç ve güvenlik; `Yolsuzluk`, `Siyasi sorumluluk`, `Kurumsal sorumluluk` → Yolsuzluk ve hesap verebilirlik; `Siyasi hamle`, `Devlet otoritesi`, `Devlet başarısı`, `Yönetim / kontrol` → Siyaset ve iktidar; `Hayat pahalılığı`, `Piyasa beklentisi` → Ekonomi; `Merak / kişi profili`, `Gösteriş / magazin` → İnsani ilgi; `Basın özgürlüğü`, `Sansür / ifade özgürlüğü` → Basın ve ifade özgürlüğü; `Kriz / dramatize`, `Dramatize`, `Gizem / şüphe`, `Belirsizlik` → Kriz ve dram; `Maç önizlemesi` → Spor.

- [ ] **Step 4: Implement `validation/answerkey/codebook.py`.** `blame_level`: strip; empty, `—`, or a value starting with `Belirtilmiyor` or `Belirsiz` → `none`; contains `(ima)` → `implied`; otherwise `explicit`. `frame_category`: exact match on the stripped value, else `"Diğer"`.

- [ ] **Step 5: Run the tests** — `python3 -m unittest validation.tests.test_answerkey -v` → PASS

- [ ] **Step 6: Commit** — `feat(answerkey): narrative codebook (blame level, frame category)`. The owner reviews the mapping and sets `"approved": true` in a later commit; until then every report prints "codebook not yet approved".

---

### Task 3: Answer-key record, gold and agreement report

**Files:**
- Create: `validation/answerkey/record.py`, `validation/answerkey/__main__.py`, `validation/reference/answerkey/.gitkeep`
- Test: `validation/tests/test_answerkey.py`

**Interfaces:**
- Consumes: `krippendorff_alpha`, `percent_agreement` (Task 1); `blame_level`, `frame_category`, `human_rows`, `load_codebook` (Task 2).
- Produces:
  - `@dataclass(frozen=True, order=True) class Coding: item: str; coder: str; field: str; value: str` — `item` is `<narrative key>__<outlet slug>` for narratives and `<event>__<card id>` for behaviour; `coder` is a slot matching `^[A-Z][1-9]$` (person letter + pass digit); `field` ∈ `FIELDS = ("blame_level", "frame_category", "present")`; values: `blame_level` ∈ `BLAME_LEVELS + ("unsure",)`, `frame_category` ∈ the codebook categories + `"unsure"`, `present` ∈ `("yes", "no", "unsure")`.
  - `CORE_SLOT = "A1"` (see the assumption in Global Constraints).
  - `CODINGS = validation/reference/answerkey/codings.jsonl`; `read(path=CODINGS) -> list[Coding]`; `append(codings, path=CODINGS) -> int` (adds only records not present; refuses a second value from the same slot for the same item and field, and any slot not matching the pattern, with `ValueError` naming the item or slot; nothing is written when it refuses).
  - `from_core(core: dict, codebook: dict) -> list[Coding]` — the existing human narrative coding as slot `CORE_SLOT` (both narrative fields), derived on the fly, never written to `codings.jsonl`.
  - `units(codings, field) -> dict[str, list[str | None]]` — per item, one value per slot, sorted by slot; `unsure` counts as not coded.
  - `agreement(codings, field) -> dict` → `{"items_double": int, "alpha": float | None, "percent": float | None, "usable": bool, "kind": "same coder" | "between coders" | None}`; `items_double` counts items with ≥ 2 non-`unsure` values; `kind` is `"same coder"` when every slot on those items shares one letter, `"between coders"` otherwise, `None` with no such items; `usable` = `items_double >= 30 and alpha is not None and alpha >= 0.67`.
  - `gold(codings, field) -> tuple[dict[str, str], list[str]]` → (item → value where every slot that coded it, `unsure` aside, agrees; items with disagreement, for adjudication).
  - CLI: `python -m validation.answerkey agreement` writes `docs/validation/reports/answerkey-agreement.md` (one row per field: items coded twice, alpha, percent, usable, and the measure's name: "same-coder consistency (two passes ≥ 14 days apart)" or "agreement between coders") and prints it.

- [ ] **Step 1: Write the failing tests**

```python
class RecordTest(unittest.TestCase):
    def test_append_dedupes_and_refuses_a_changed_answer(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.jsonl"
            a = Coding("e1__framing-effect", "A1", "present", "yes")
            self.assertEqual(append([a, a], p), 1)
            with self.assertRaisesRegex(ValueError, "e1__framing-effect"):
                append([Coding("e1__framing-effect", "A1", "present", "no")], p)
            with self.assertRaisesRegex(ValueError, "Ayşe"):
                append([Coding("e2__framing-effect", "Ayşe", "present", "no")], p)   # names never stored
    def test_gold_and_disagreement(self):
        cs = [Coding("i1", "A1", "present", "yes"), Coding("i1", "A2", "present", "yes"),
              Coding("i2", "A1", "present", "yes"), Coding("i2", "A2", "present", "no"),
              Coding("i3", "A1", "present", "unsure")]
        self.assertEqual(gold(cs, "present"), ({"i1": "yes"}, ["i2"]))
    def test_usable_needs_thirty_items_coded_twice(self):
        cs = [Coding(f"i{n}", c, "present", "yes" if n % 2 else "no") for n in range(29) for c in ("A1", "A2")]
        self.assertFalse(agreement(cs, "present")["usable"])
    def test_two_passes_of_one_person_are_same_coder(self):
        cs = [Coding("i1", "A1", "present", "yes"), Coding("i1", "A2", "present", "yes")]
        self.assertEqual(agreement(cs, "present")["kind"], "same coder")
        self.assertEqual(agreement(cs + [Coding("i1", "B1", "present", "no")], "present")["kind"], "between coders")
    def test_core_rows_become_coder_a(self):
        core = {"N": {"k1": {"status": "headline_coded", "rows": [{"s": "sabah", "frame": "Adli süreç", "blame": "Yargı (ima)"}]},
                      "k2": {"status": "agent_coded", "rows": [{"s": "sabah", "frame": "Adli süreç", "blame": ""}]}}}
        cb = {"categories": ["Yargı ve soruşturma", "Diğer"], "frames": {"Adli süreç": "Yargı ve soruşturma"}}
        self.assertEqual(sorted(from_core(core, cb)), [Coding("k1__sabah", "A1", "blame_level", "implied"),
                                                       Coding("k1__sabah", "A1", "frame_category", "Yargı ve soruşturma")])
```

- [ ] **Step 2: Run to see them fail** — `python3 -m unittest validation.tests.test_answerkey -v` → FAIL, no `record` module

- [ ] **Step 3: Implement `record.py` and the `agreement` sub-command of `__main__.py`** (argparse with sub-commands; later tasks add `packet`, `import`, `narrative-eval`, `behaviour-eval`, `examples`). `append` validates the whole batch before writing any line. `agreement` merges `read()` with `from_core(core, load_codebook())`, core from `--core` (default `public/data/core.bin`, read with `biasguard.news._load`).

- [ ] **Step 4: Run the tests** — PASS; then `python3 -m validation.answerkey agreement` prints three rows with `items_double` 0 and "not usable yet".

- [ ] **Step 5: Commit** — `feat(answerkey): coding record, gold and agreement report`

---

### Task 4: Blind packets and the desk-export import

A packet is a fixed list of items one coder codes blind in the desk (Task 5). Packets ship to the site in core key `BLIND`; the private key (which items the AI showed) stays in the repository, never in core.

**Files:**
- Create: `validation/answerkey/packets.py`; data files `data/reference/blind-packets.json` and `validation/reference/answerkey/<packet id>.key.json` (written by the CLI)
- Modify: `validation/answerkey/__main__.py` (sub-commands `packet`, `import`), `pipeline/capraz_pipeline/narratives.py` (`merge`: core key `BLIND`)
- Test: `validation/tests/test_answerkey.py`, `pipeline/tests/test_narratives.py`

**Interfaces:**
- Consumes: `Coding`, `append`, `read`, `human_rows`, `load_codebook`, `BLAME_LEVELS`, `CORE_SLOT` (Tasks 2–3); `biasguard.catalog.load_cards()`; a BiasGuard run's `biasguard.json` (events with `status`, `selected`, `supported`, `uncertain`, each finding with `id`) and `inputs.jsonl` (`event`, `title`, `text`).
- Produces:
  - `PACKETS = data/reference/blind-packets.json`, shape `{"categories": [codebook categories], "packets": [packet, ...]}`. A packet is `{"id": str, "kind": "narrative" | "behaviour", "coder": slot, "created": "YYYY-MM-DD", "not_before": "YYYY-MM-DD" | null, "events": {...}, "items": [...]}`:
    - narrative: `events` = `{N key: {"olay": q.happened}}`; item = `{"item": "<N key>__<outlet slug>", "event": N key, "kurum": outlet name from core S, "baslik": row hl}`; rows without `hl` are skipped.
    - behaviour: `events` = `{event: {"baslik": title, "metin": inputs text}}`; item = `{"item": "<event>__<card id>", "event": event, "card": card id, "ad": card name, "tanim": definition, "kosullar": necessary_conditions}`.
  - `narrative_packet(core: dict, n_events: int, seed: int, pid: str, coder: str, today: date) -> dict` — `n_events` keys drawn with `random.Random(seed)` from the sorted human-coded N keys; items shuffled with the same generator; `not_before` null.
  - `behaviour_packet(results: dict, inputs: dict[str, dict], cards: list[dict], n_events: int, seed: int, pid: str, coder: str, today: date) -> tuple[dict, dict]` — `n_events` events with status `review_complete`, drawn as above; per event every shown finding (`supported` + `uncertain`) plus `max(shown, 2)` catalogue cards not in its `selected` list, drawn at random; items shuffled. Second value is the key `{item: {"event", "card", "ai_shown": bool}, "_unflagged": {event: {"sampled": int, "total": int}}}`, where `total` = catalogue cards not in `selected`.
  - `repeat_packet(first: dict, codings: list[Coding], n_items: int, seed: int, pid: str, coder: str, today: date, gap_days: int = 14) -> dict` — the same kind and events, `n_items` items drawn from `first`'s items that `first["coder"]` coded with a value other than `unsure`, shuffled; `not_before` = `today + gap_days`. Fewer coded items than `n_items` → `ValueError` saying how many are coded.
  - `upsert(packet: dict, categories: list[str], path=PACKETS) -> None` — adds the packet; an existing id with identical items is a no-op; an existing id with different items → `ValueError` naming the id (a packet never changes once coding may have started).
  - `read_export(export: dict, packets: dict) -> list[Coding]` — reads the reviews whose `key` starts `blind__`; key = `"blind__" + packet id + "__" + item`; each such review carries `answers`: narrative `{"blame_level", "frame_category"}`, behaviour `{"present"}`, values as in `Coding`. Slot = the packet's `coder`. An unknown packet id, an item not in its packet, a missing or unknown field, or an unknown value → `ValueError` naming the review key, and nothing is returned. Reviews without `blind__` are ignored.
  - `merge(core)` sets `core["BLIND"]` to the whole `PACKETS` file when it exists.
  - CLI (seed default `PARAMS.random_state`, `today` = the run date):
    - `packet --kind narrative --events 20 --coder A2 --id narrative-A2`
    - `packet --kind behaviour --run runs/bg82 --events 30 --coder A1 --id behaviour-A1` (also writes `validation/reference/answerkey/behaviour-A1.key.json`)
    - `packet --repeat behaviour-A1 --items 30 --coder A2 --id behaviour-A2` (copies the first packet's key entries for its items into `behaviour-A2.key.json`)
    - `import <export.json>` → `append(read_export(...))`; prints the new codings per packet.

- [ ] **Step 1: Write the failing tests**

```python
class PacketTest(unittest.TestCase):
    def test_behaviour_packet_is_balanced_and_carries_no_verdict(self):
        p, key = behaviour_packet(RESULTS_FIXTURE, INPUTS_FIXTURE, CARDS_FIXTURE, n_events=1, seed=1,
                                  pid="b-A1", coder="A1", today=date(2026, 11, 21))
        self.assertEqual(len(p["items"]), 3)                              # 1 shown finding + max(1, 2) unselected cards
        self.assertEqual(set(p["items"][0]), {"item", "event", "card", "ad", "tanim", "kosullar"})
        self.assertNotIn("ai_shown", json.dumps(p))
        self.assertEqual(key["_unflagged"], {"e1": {"sampled": 2, "total": 3}})
    def test_repeat_packet_opens_after_the_gap(self):
        first = {"id": "b-A1", "kind": "behaviour", "coder": "A1", "events": {}, "items": [{"item": f"e1__c{i}"} for i in range(4)]}
        cs = [Coding("e1__c0", "A1", "present", "yes"), Coding("e1__c1", "A1", "present", "no"),
              Coding("e1__c2", "A1", "present", "unsure")]
        p = repeat_packet(first, cs, n_items=2, seed=1, pid="b-A2", coder="A2", today=date(2026, 11, 21))
        self.assertEqual(p["not_before"], "2026-12-05")
        self.assertEqual(sorted(i["item"] for i in p["items"]), ["e1__c0", "e1__c1"])
        with self.assertRaisesRegex(ValueError, "2"):
            repeat_packet(first, cs, n_items=3, seed=1, pid="b-A2", coder="A2", today=date(2026, 11, 21))
    def test_read_export_maps_answers_to_the_packet_slot(self):
        ex = {"reviews": [{"key": "blind__b-A1__e1__c1", "status": "coded", "answers": {"present": "yes"}},
                          {"key": "s1__framing-effect", "status": "verified"}]}
        self.assertEqual(read_export(ex, PACKETS_FIXTURE), [Coding("e1__c1", "A1", "present", "yes")])
    def test_read_export_refuses_an_item_no_packet_has(self):
        ex = {"reviews": [{"key": "blind__b-A1__e9__c1", "status": "coded", "answers": {"present": "yes"}}]}
        with self.assertRaisesRegex(ValueError, "blind__b-A1__e9__c1"):
            read_export(ex, PACKETS_FIXTURE)
    def test_upsert_refuses_changed_items(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            upsert({"id": "x", "items": [{"item": "a"}]}, ["Diğer"], path)
            upsert({"id": "x", "items": [{"item": "a"}]}, ["Diğer"], path)
            with self.assertRaisesRegex(ValueError, "x"):
                upsert({"id": "x", "items": [{"item": "b"}]}, ["Diğer"], path)
```

```python
def test_merge_ships_blind_packets_without_the_key(self):   # pipeline/tests/test_narratives.py
    core = {}
    merge(core)
    self.assertEqual(core.get("BLIND"), json.loads((REPO / "data/reference/blind-packets.json").read_text(encoding="utf-8")))
    self.assertNotIn("ai_shown", json.dumps(core["BLIND"]))
```

`RESULTS_FIXTURE`, `INPUTS_FIXTURE`, `CARDS_FIXTURE` and `PACKETS_FIXTURE` are helpers in the same file: one event `e1` with status `review_complete`, `selected: ["c1"]` and one `uncertain` finding of card `c1`; its inputs entry; a catalogue of `c1`–`c4`; and `{"packets": [{"id": "b-A1", "kind": "behaviour", "coder": "A1", "items": [{"item": "e1__c1"}]}]}`.

- [ ] **Step 2: Run to see them fail** — `python3 -m unittest validation.tests.test_answerkey -v` → FAIL, no `packets` module

- [ ] **Step 3: Implement `packets.py`, the two sub-commands and the `BLIND` line in `merge`**

- [ ] **Step 4: Run the tests** — PASS (the merge test passes once Step 5 has written the file)

- [ ] **Step 5: Make the two real packets** — `python3 -m validation.answerkey packet --kind behaviour --run runs/bg82 --events 30 --coder A1 --id behaviour-A1` and `python3 -m validation.answerkey packet --kind narrative --events 20 --coder A2 --id narrative-A2`; print each packet's item count (behaviour: every shown finding of 30 events plus the unflagged sample).

- [ ] **Step 6: Commit** — `feat(answerkey): blind packets for the desk and the export import` (code, tests, `blind-packets.json`, `behaviour-A1.key.json`)

---

### Task 5: Blind mode in the AI denetim masası

**Files:**
- Modify: `site/js/v7/logic.js` (`BLIND_FIELDS`, `blindKey`, `blindOpen`, `blindProgress`, `blindItemHtml`; `reviewsExport` keeps `answers`), `site/js/v7/desk.js` (group, packet list, item view, save), `site/js/app.js` (`rev7Save`: keep `answers`; no event-text binding for `blind__` keys), `site/styles.css`
- Test: `site/tests/logic.test.cjs`, `site/tests/smoke.cjs`

**Interfaces:**
- Consumes: core `BLIND` (Task 4 shape); `deskName(card, fallback)`; `rev7`, `rev7Save`.
- Produces:
  - `BLIND_FIELDS = {narrative: [["blame_level", "Sorumlu tutma", [["none", "Yok"], ["implied", "İma"], ["explicit", "Açık"], ["unsure", "Emin değilim"]]], ["frame_category", "Çerçeve", null]], behaviour: [["present", "Bu kavram bu haberlerde var mı?", [["yes", "Evet"], ["no", "Hayır"], ["unsure", "Emin değilim"]]]]}` — `null` options = `BLIND.categories` plus `["unsure", "Emin değilim"]`.
  - `blindKey(pid, item) -> string` = `"blind__" + pid + "__" + item`.
  - `blindOpen(packet, today: "YYYY-MM-DD") -> boolean` — true when `not_before` is null or `today >= not_before`.
  - `blindProgress(packet, reviews) -> {done: number, total: number}` — `done` counts items whose review has every field of its kind in `answers`.
  - `blindItemHtml(blind, packet, item, answers) -> string` — the item view: narrative shows `olay`, `kurum`, `baslik`; behaviour shows the event `baslik` and `metin` lines, then the concept (`deskName(card, ad)`, `tanim`, `kosullar` as a list); then one control per field with the saved answer marked. It contains no AI status, verdict, confidence, quote, "AI" badge, other pass's answer or link to the event page.
  - Desk: group `["kor", "Kör kodlama"]` in `DESK_GROUPS`, shown when `D.BLIND` has packets. The group lists the packets (id, kind in Turkish, `done/total`); a locked one reads "Bu tur <gün ay yıl> tarihinde açılır; ilk turdaki yanıtlarınızın etkisi geçsin diye." Inside a packet: the first item without a complete answer opens; keys `1`–`4` pick the first field's option, the frame is a select, `Enter` saves when every field is answered, `J`/`K` move. Save = `rev7Save(blindKey(pid, item), "coded", "", false, {answers: {...}})`.

- [ ] **Step 1: Write the failing tests**

```js
test("blind helpers", () => {
  assert.equal(L.blindKey("b-A1", "e1__c1"), "blind__b-A1__e1__c1");
  assert.equal(L.blindOpen({ not_before: null }, "2026-11-21"), true);
  assert.equal(L.blindOpen({ not_before: "2026-12-05" }, "2026-12-04"), false);
  assert.equal(L.blindOpen({ not_before: "2026-12-05" }, "2026-12-05"), true);
  const pk = { id: "n-A2", kind: "narrative", items: [{ item: "k1__sabah" }, { item: "k1__ntv" }] };
  assert.deepEqual(L.blindProgress(pk, { "blind__n-A2__k1__sabah": { answers: { blame_level: "none", frame_category: "Spor" } },
                                         "blind__n-A2__k1__ntv": { answers: { blame_level: "none" } } }), { done: 1, total: 2 });
});
test("blind item shows no AI", () => {
  const blind = { categories: ["Spor", "Diğer"], packets: [] };
  const pk = { id: "b-A1", kind: "behaviour", events: { e1: { baslik: "Başlık", metin: "[sabah · 10:00] Haber" } } };
  const h = L.blindItemHtml(blind, pk, { item: "e1__c1", event: "e1", card: "c1", ad: "Card", tanim: "Tanım", kosullar: ["k1"] }, {});
  assert.ok(h.includes("[sabah · 10:00] Haber") && h.includes("Tanım"));
  assert.ok(!/AI|Yapay|kanıt|Doğrulan|Belirsiz|#\/olay/.test(h));
});
test("export keeps blind answers", () => {
  const x = L.reviewsExport({ "blind__b-A1__e1__c1": { status: "coded", answers: { present: "yes" } } }, "p1");
  assert.deepEqual(x.reviews[0].answers, { present: "yes" });
});
```

`blindItemHtml` lives in `logic.js` so Node can test it; `deskName` is not available there, so it takes the concept title from the item's `ad` when the global `deskName` is undefined.

- [ ] **Step 2: Run to see them fail** — `node site/tests/logic.test.cjs` → FAIL

- [ ] **Step 3: Implement the helpers, the desk group and the two `allowlist` lines** (`rev7Save` and `reviewsExport` gain `answers`; `rev7Save` skips the `bg7ev` text binding when the key starts with `blind__`).

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Rebuild and check in the browser.** Pack core with the Task 4 packets (`python -m biasguard.news pack --build <dir> --run runs/bg82 --media-run runs/bgm82`), `cd pipeline && python3 -m capraz_pipeline site --site ../public`, then with the owner mock (`window.claude` via `addInitScript`, as the desk was checked before) open the desk's Kör kodlama group at 390 px and 1280 px: `behaviour-A1` and `narrative-A2` are listed with `0/N`, an item saves with `1` then `Enter` and the count becomes `1/N`, and the item view text contains none of the words in the test above. Then `node site/tests/smoke.cjs public <out> "#/yonetim?t=bilissel"` → `smoke ok`.

- [ ] **Step 6: Commit** — `feat(yönetim): blind coding mode in the AI denetim masası`

---

### Task 6: Score the narrative agent against the human-coded weeks

**Files:**
- Modify: `pipeline/capraz_pipeline/narratives.py` (add `DIM_LABELS`, `tasks()`, CLI command `tasks`)
- Create: `validation/answerkey/narrative_eval.py`; data file `data/reference/narrative-quality.json` (written by the CLI)
- Modify: `validation/answerkey/__main__.py` (sub-command `narrative-eval`), `runs/narr/PROMPT.md` (field name `examples`)
- Test: `pipeline/tests/test_narratives.py` (create if absent), `validation/tests/test_answerkey.py`

**Interfaces:**
- Consumes: `human_rows`, `HUMAN_STATUSES`, `blame_level`, `frame_category`, `krippendorff_alpha`, `percent_agreement`.
- Produces:
  - `DIM_LABELS = {"frame": "Çerçeve", "hero": "Merkezdeki aktör", "blame": "Sorumlu tutulan", "cause": "Sunulan neden", "cons": "Öne çıkan sonuç", "aff": "Etkilenen kesim", "sol": "Meşrulaştırılan çözüm", "moral": "Ahlaki çerçeve", "start": "Hikâyenin başlangıcı"}`.
  - `tasks(items: list[dict], examples: list[dict], out: Path, batch: int = 12, n_examples: int = 2) -> list[Path]` — `items` are `{"event", "week", "title", "headlines": [{"s", "hl"}]}`; `examples` are human-coded `N` entries as `{"key", "q", "rows"}`; writes `out/tasks/batch-K.json` = `{"dimensions": DIM_LABELS, "examples": [...], "events": [...]}` where the examples are the `n_examples` highest-`score` gold entries whose key is not an `event` of that batch.
  - CLI: `python -m capraz_pipeline.narratives tasks --source gold --core ../public/data/core.bin --out ../runs/narr-eval` (items = the human-coded `N` entries, `event` = the N key, headlines = their `hl`); `--source candidates` keeps today's production flow from `candidates.json`.
  - `compare(agent: dict[str, dict], core: dict, codebook: dict) -> dict` → `{"events": int, "blame_level": {"n": int, "agreement": float, "alpha": float | None}, "frame_category": {...}, "unmapped_frames": int, "codebook_approved": bool}`; `agent` maps N key → the agent's coded JSON; pairs are matched on `(key, s)`; agent frames go through `frame_category`, so unmapped non-empty agent spellings among the matched pairs count in `unmapped_frames`.
  - CLI: `python -m validation.answerkey narrative-eval --coded runs/narr-eval/coded` writes `data/reference/narrative-quality.json` (the dict above plus `"measured": "<YYYY-MM-DD>"`) and `docs/validation/reports/narrative-agent-vs-human.md`.

- [ ] **Step 1: Write the failing tests**

```python
# pipeline/tests/test_narratives.py
def test_examples_never_include_an_event_of_the_batch(self):
    gold = [{"key": k, "q": {}, "rows": [], "score": s} for k, s in (("g1", 3.0), ("g2", 2.0), ("g3", 1.0))]
    items = [{"event": "g1", "week": "w1", "title": "t", "headlines": []}]
    with tempfile.TemporaryDirectory() as d:
        b = json.loads(tasks(items, gold, Path(d), batch=12, n_examples=2)[0].read_text())
    self.assertEqual([x["key"] for x in b["examples"]], ["g2", "g3"])
# validation/tests/test_answerkey.py
def test_compare_scores_matching_rows_only(self):
    core = {"N": {"k1": {"status": "headline_coded", "rows": [
        {"s": "sabah", "frame": "Adli süreç", "blame": "Yargı"}, {"s": "ntv", "frame": "Adli süreç", "blame": ""}]}}}
    agent = {"k1": {"rows": [{"s": "sabah", "frame": "Adli süreç", "blame": "Savcı"}, {"s": "ntv", "frame": "Spor", "blame": ""},
                             {"s": "cnn", "frame": "x", "blame": ""}]}}
    r = compare(agent, core, {"approved": False, "categories": ["Yargı ve soruşturma", "Diğer"],
                              "frames": {"Adli süreç": "Yargı ve soruşturma"}})
    self.assertEqual((r["blame_level"]["n"], r["blame_level"]["agreement"]), (2, 1.0))
    self.assertEqual(r["frame_category"]["agreement"], 0.5)
    self.assertEqual(r["unmapped_frames"], 1)
```

- [ ] **Step 2: Run to see them fail** — `cd pipeline && python3 -m unittest tests.test_narratives -v` and `python3 -m unittest validation.tests.test_answerkey -v` → FAIL

- [ ] **Step 3: Implement `tasks()`, `compare()` and both CLI commands**; rename `examples_from_hand_coded_weeks` to `examples` in `runs/narr/PROMPT.md`.

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Run the blind re-coding.** `python -m capraz_pipeline.narratives tasks --source gold --core ../public/data/core.bin --out ../runs/narr-eval`, then dispatch one coding agent per batch with `runs/narr/PROMPT.md` (batch path `runs/narr-eval/tasks/batch-K.json`, output `runs/narr-eval/coded/<event>.json`). The agents must not open `public/`, `data/` or any other `coded/` folder.

- [ ] **Step 6: Score it** — `python3 -m validation.answerkey narrative-eval --coded runs/narr-eval/coded` prints both agreements for 61 events and writes the two files.

- [ ] **Step 7: Commit** — `feat(narratives): leak-free coding tasks; agent scored against the human-coded weeks` (code, tests, `narrative-quality.json`, report; not `runs/narr-eval/`)

---

### Task 7: Measure the behavioural review against blind gold

**Files:**
- Create: `validation/answerkey/behaviour_eval.py`
- Modify: `validation/answerkey/__main__.py` (sub-command `behaviour-eval`)
- Test: `validation/tests/test_answerkey.py`

**Interfaces:**
- Consumes: `gold` (Task 3); the packet key file of Task 4; `validation.feedback.stats.wilson_lower`, `card_status`.
- Produces:
  - `measure(gold: dict[str, str], key: dict) -> dict` → `{"overall": {...}, "cards": {card: {...}}}` with, per scope: `tp` (AI-shown, gold yes), `fp` (AI-shown, gold no), `found_unflagged` (not shown, gold yes), `missed_est` = Σ over events of `found_unflagged_e × total_e / sampled_e`, `precision` = tp/(tp+fp) or `None`, `precision_lower` = `wilson_lower(tp, tp+fp)`, `recall_est` = tp/(tp+missed_est) or `None`.
  - `as_card_stats(m: dict) -> dict` — the shape `card_status()` reads: `{card: {"reviewed": tp+fp, "kept": tp, "rejected": fp, "precision": …, "lower": …}}`.
  - CLI: `behaviour-eval --key validation/reference/answerkey/behaviour-A1.key.json` writes `docs/validation/reports/behaviour-blind.md`; with `--status` it also writes `validation/reference/card_status.json` through the existing `card_status(stats, gates)`, with `"measure": "blind precision"`.

- [ ] **Step 1: Write the failing test**

```python
def test_measure_estimates_misses_from_the_unflagged_sample(self):
    key = {"e1__c1": {"event": "e1", "card": "c1", "ai_shown": True},
           "e1__c2": {"event": "e1", "card": "c2", "ai_shown": True},
           "e1__c3": {"event": "e1", "card": "c3", "ai_shown": False},
           "_unflagged": {"e1": {"sampled": 1, "total": 4}}}
    m = measure({"e1__c1": "yes", "e1__c2": "no", "e1__c3": "yes"}, key)
    self.assertEqual((m["overall"]["tp"], m["overall"]["fp"], m["overall"]["missed_est"]), (1, 1, 4.0))
    self.assertEqual(m["overall"]["precision"], 0.5)
    self.assertAlmostEqual(m["overall"]["recall_est"], 0.2)
    self.assertEqual(as_card_stats(m)["c1"]["kept"], 1)
```

- [ ] **Step 2: Run to see it fail** — FAIL, no `behaviour_eval`

- [ ] **Step 3: Implement `measure`, `as_card_stats` and the CLI**

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Commit** — `feat(answerkey): blind precision and estimated recall for the behavioural review`

- [ ] **Step 6 (after the owner has coded `behaviour-A1` in the desk and the export is imported):** `python3 -m validation.answerkey behaviour-eval --key validation/reference/answerkey/behaviour-A1.key.json` prints overall and per-card precision; `--status` only when the agreement report shows `present` usable.

---

### Task 8: Human examples for the BiasGuard reviewers (learning without retraining)

**Files:**
- Modify: `biasguard/news.py` (`write_tasks`, `prompts`, CLI `--examples`)
- Modify: `validation/answerkey/__main__.py` (sub-command `examples`)
- Test: `biasguard/test_news.py` (class `TaskCatalogTests`), `validation/tests/test_answerkey.py`

**Interfaces:**
- Consumes: `gold` (Task 3, field `present`); the packet key (Task 4) for each item's event and card; event texts from the run's `inputs.jsonl`.
- Produces:
  - Examples file: `{card_id: [{"event": str, "text": str, "present": "yes" | "no"}, ...]}`, written by `python -m validation.answerkey examples --run runs/bg82 --out runs/bg-next/examples.json`, holding only items whose `present` field is usable (Task 3), at most one `yes` and one `no` per card.
  - `write_tasks(run, stage, batch, bg=None, examples: dict[str, list[dict]] | None = None)` — in review tasks, each card used by the batch gets `"examples"`: the card's examples whose `event` is not an event of that batch, at most 2.
  - `prompts("review", role)` gains one sentence when examples are present: "Örnekler başka olaylardan, insanların kodladığı yanıtlardır; bu olayın kanıtı değildir."
  - CLI: `python -m biasguard.news tasks --run <run> --stage review --examples <file>`.

- [ ] **Step 1: Write the failing tests**

```python
def test_review_tasks_carry_examples_from_other_events_only(self):
    ex = {"framing-effect": [{"event": "e0", "text": "x", "present": "yes"}, {"event": "e9", "text": "y", "present": "no"}]}
    with tempfile.TemporaryDirectory() as d:
        run = self._selected_run(d)
        path = write_tasks(run, "review", 10, examples=ex)[0]
        card = next(c for c in json.loads(path.read_text())["cards"] if c["id"] == "framing-effect")
    self.assertEqual([e["event"] for e in card["examples"]], ["e9"])
def test_no_examples_file_leaves_tasks_unchanged(self):
    with tempfile.TemporaryDirectory() as d:
        cards = json.loads(write_tasks(self._selected_run(d), "review", 10)[0].read_text())["cards"]
    self.assertFalse(any("examples" in c for c in cards))
def _selected_run(self, d):
    # TaskCatalogTests._run (inputs.jsonl with event e0) plus a selection, so the review stage has cards to send
    run = self._run(d)
    (run / "selections").mkdir()
    (run / "selections" / "e0.json").write_text(json.dumps(
        {"candidate_ids": ["framing-effect"], "selection_uncertainty": [], "selection_note": ""}))
    return run
```

- [ ] **Step 2: Run to see them fail** — `python3 -m unittest biasguard.test_news -v` → FAIL (`unexpected keyword argument 'examples'`)

- [ ] **Step 3: Implement the parameter, the prompt sentence, both CLIs**

- [ ] **Step 4: Run the tests** — PASS, and `python3 -m unittest discover -s biasguard -p "test_*.py"` stays green

- [ ] **Step 5: Commit** — `feat(biasguard): human examples in review tasks, never from the same event`

- [ ] **Step 6 (when Task 7 shows a usable `present` field): adopt through the existing gate.** Run the loop in `docs/validation/ITERATIONS.md` with the examples file as the single change: replay run, lab run, `python -m validation.learning promote-check`. Record the Observation Ledger entry whatever the result. The examples become the default only if the promotion gate passes.

---

### Task 9: First trained baselines (mlbench)

**Files:**
- Create: `validation/mlbench/__init__.py`, `validation/mlbench/data.py`, `validation/mlbench/models.py`, `validation/mlbench/evaluate.py`, `validation/mlbench/__main__.py`
- Test: `validation/tests/test_mlbench.py`

**Interfaces:**
- Consumes: `human_rows`, `blame_level`, `frame_category`, `load_codebook` (Task 2); the agent's coded folder from Task 6.
- Produces:
  - `@dataclass(frozen=True) class Row: group: str; outlet: str; text: str; blame_level: str; frame_category: str` and `rows(core, codebook) -> list[Row]` (human rows with a headline `hl`; `group` = N key).
  - `class Predictor(Protocol): name: str; def fit(self, texts: list[str], labels: list[str]) -> None; def predict(self, texts: list[str]) -> list[str]` — the plug-in point for every later model (a Turkish language model, an in-house detector).
  - `Majority()`; `TfidfLogReg(random_state: int = 20261028)`: word 1–2-gram plus character 3–5-gram TF-IDF (`char_wb`), `LogisticRegression(max_iter=2000, class_weight="balanced")`; a training set with a single class predicts that class.
  - `cross_validate(make: Callable[[], Predictor], rows, label: str, folds: int = 5) -> dict` → `{"n", "accuracy", "macro_f1", "per_class": {cls: {"f1", "support"}}}`, using `GroupKFold(n_splits=folds)` on `group`; `macro_f1` over the classes present in the gold.
  - `score_fixed(pred: dict[tuple[str, str], str], rows, label) -> dict` — same metrics for a fixed prediction set (the agent, keyed by `(group, outlet)`).
  - CLI: `python -m validation.mlbench run --coded runs/narr-eval/coded` writes `validation/reference/mlbench.json` = `{label: {"majority": …, "tfidf_logreg": …, "agent": …}}` and `docs/validation/reports/mlbench.md`, for the labels `blame_level` and `frame_category`.

- [ ] **Step 1: Write the failing tests**

```python
class MlbenchTest(unittest.TestCase):
    def test_groups_never_split_across_folds(self):
        rs = [Row(f"g{i // 3}", f"o{i}", f"metin {i}", "none" if i % 2 else "explicit", "Diğer") for i in range(30)]
        seen = []
        class Spy(Majority):
            def fit(self, texts, labels): seen.append(set(texts)); super().fit(texts, labels)
        cross_validate(Spy, rs, "blame_level", folds=5)
        for train in seen:
            groups = {r.group for r in rs if r.text in train}
            self.assertFalse(any(r.group in groups and r.text not in train for r in rs))
    def test_single_class_training_fold_predicts_that_class(self):
        m = TfidfLogReg(); m.fit(["a b", "c d"], ["none", "none"])
        self.assertEqual(m.predict(["e f"]), ["none"])
    def test_majority_baseline(self):
        rs = [Row("g1", "o", "x", "none", "Diğer")] * 3 + [Row("g2", "o", "y", "explicit", "Diğer")]
        self.assertEqual(score_fixed({("g1", "o"): "none", ("g2", "o"): "none"}, rs, "blame_level")["accuracy"], 0.75)
```

- [ ] **Step 2: Run to see them fail** — `python3 -m unittest validation.tests.test_mlbench -v` → FAIL, no package

- [ ] **Step 3: Implement the package**

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Run it on the real data** — `python3 -m validation.mlbench run --coded runs/narr-eval/coded` prints a 3 × 2 table (majority, TF-IDF, agent × the two labels); every cell shows `n`.

- [ ] **Step 6: Commit** — `feat(mlbench): grouped cross-validation, majority and TF-IDF baselines, agent scored alongside`

---

### Task 10: Show measured narrative quality on the narrative page

**Files:**
- Modify: `pipeline/capraz_pipeline/narratives.py` (`merge`: core key `NQ` from `data/reference/narrative-quality.json`)
- Modify: `site/js/v7/logic.js` (add and export `narrQualityLine`), `site/js/v7/anlati.js` (`v7Body`)
- Test: `site/tests/logic.test.cjs`, `pipeline/tests/test_narratives.py`

**Interfaces:**
- Consumes: `data/reference/narrative-quality.json` (Task 6).
- Produces: `narrQualityLine(nq: object | undefined) -> string` — empty string when `nq` is missing or either agreement is missing; otherwise exactly
  `"Bu kodlama, elle kodlanmış " + nq.events + " olayda insan kodlamasıyla karşılaştırıldı: sorumlu tutmada %" + round(100 × blame agreement) + ", çerçevede %" + round(100 × frame agreement) + " uyum."` followed by `" Kategori listesi henüz onaylanmadı."` when `codebook_approved` is false.

- [ ] **Step 1: Write the failing tests**

```js
test("narrQualityLine", () => {
  assert.equal(L.narrQualityLine(undefined), "");
  assert.equal(L.narrQualityLine({ events: 61, codebook_approved: true,
    blame_level: { agreement: 0.824 }, frame_category: { agreement: 0.6 } }),
    "Bu kodlama, elle kodlanmış 61 olayda insan kodlamasıyla karşılaştırıldı: sorumlu tutmada %82, çerçevede %60 uyum.");
});
```

```python
def test_merge_ships_narrative_quality(self):   # pipeline/tests/test_narratives.py
    core = {}
    merge(core)
    self.assertEqual(core.get("NQ"), json.loads((REPO / "data/reference/narrative-quality.json").read_text()))
```

- [ ] **Step 2: Run to see them fail** — `node site/tests/logic.test.cjs` and `cd pipeline && python3 -m unittest tests.test_narratives -v` → FAIL

- [ ] **Step 3: Implement.** `merge` reads the file like `W82`. In `v7Body`, when `ai` is true and `narrQualityLine(D.NQ)` is not empty, append `<p class="v7-note">` with it after the "Kısaca" block.

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Rebuild and check in the browser.** Pack core (`python -m biasguard.news pack --build <dir> --run runs/bg82 --media-run runs/bgm82`), `python -m capraz_pipeline site --site ../public`, then run the smoke test (`node site/tests/smoke.cjs public <out> "#/anlati"`) → `smoke ok`. An agent-coded narrative shows the sentence; a hand-coded one does not.

- [ ] **Step 6: Commit** — `feat(site): narrative page states how well AI coding matches human coding`

---

## Deferred to a separate plan (report stages 6–7)

No tasks here. A new plan starts when all three hold:
1. `answerkey-agreement.md` shows `blame_level` and `present` usable, with at least 2,000 gold narrative rows and 300 behavioural gold items.
2. `mlbench.json` has a TF-IDF baseline for both narrative labels.
3. The owner has set `"approved": true` in the codebook.

That plan adds a Turkish language model and, later, an in-house pre-screening detector as new `Predictor` implementations in `validation/mlbench/models.py`. Each is scored by the same `cross_validate`, and is adopted only when it beats `tfidf_logreg` and `agent` on macro-F1 without lowering precision on the behavioural blind gold.
