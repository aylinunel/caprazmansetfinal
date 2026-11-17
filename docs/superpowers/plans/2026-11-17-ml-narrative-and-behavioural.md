# Machine Learning for the Narrative Map and the Behavioural Review — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the narrative coding (Anlatı haritası) and the behavioural bias review (BiasGuard) a human answer key, measure the AI against it, let the AI learn from it without retraining, and stand up the first trained baselines, so that every later model has a number to beat.

**Architecture:** A new package `validation/answerkey/` turns human coding into one append-only record (blind coding packets out, filled packets in, agreement and gold out). The narrative pipeline gains a task builder whose few-shot examples never include the event being coded, so the agent can be scored against the human-coded weeks. `validation/mlbench/` trains and cross-validates small scikit-learn models against the same gold. The measured narrative quality is shipped as core key `NQ` and shown on the narrative page.

**Tech Stack:** Python 3.13, `unittest`, scikit-learn and SciPy (already in `pipeline/requirements.txt`); plain JavaScript in `site/`, tested with `node site/tests/logic.test.cjs`.

**Spec:** the stakeholder report "Çapraz Manşet: How the Algorithm Works", section "The machine-learning part" (https://claude.ai/artifact/9szRkwkQAYjcGzeGMw1Xv1), and the loop in `docs/validation/ITERATIONS.md`. For the two algorithms named here, this plan implements stages 1, 2 and 4 and the baseline half of stage 6 of that report. Stage 3 (re-testing the media cards) and stage 5 (the section sorter) concern other parts of the system and are not in this plan; stages 6–7 proper are deferred (see the end).

## Global Constraints

- Gold labels come from people only. AI output (agent codings, BiasGuard findings) is never written as, merged into or resolved as gold.
- Coders are stored as anonymous slots `"A"`, `"B"`, `"C"`… Never a name, email or user id (same rule as `validation/feedback/labels.py`).
- A field is *usable* (for measurement, examples or training) only when its double-coded items reach Krippendorff's alpha ≥ 0.67 on at least 30 items. Below that, reports print the number and say "not usable yet".
- Stage-1 targets from the report: 300 behavioural gold items, at least 20 per live concept; narrative: the 61 human-coded events (weeks v1, w1–w6) plus 20 events re-coded by a second coder.
- Cross-validation splits by event (a narrative key or an event id): no event has rows in both train and test.
- Few-shot examples shown to an AI coder or reviewer never come from an event in the same batch.
- No new dependencies. Random seeds use `PARAMS.random_state` = `20261028` from `pipeline/capraz_pipeline/config.py`.
- Nothing trained in this plan changes what the public site shows as a finding. The only public change is the measured-quality sentence of Task 9.
- Turkish for everything a coder or reader sees; English for code, comments and reports in `docs/validation/reports/`.
- Commit messages end with the session's attribution lines. Do not commit `.10x/` state files.

## Review Focus

1. **Turkish letters in coder input** (`İ`, `ı`, `ş`, trailing spaces, Excel's byte-order mark): a coder typing `Açık`, `açık ` or `AÇIK` expects it to count as `açık`. Pinned in Task 4.
2. **A filled packet with a missing, extra or renamed row**: the coder expects a clear refusal naming the row, and nothing half-imported. Pinned in Task 4.
3. **An example leaking into its own test**: coding event X with event X among the examples inflates the agreement number. Pinned in Tasks 5 and 7.
4. **A class missing from a training fold** (for example no `implied` blame in one fold): the expected result is a prediction of a known class, not a crash. Pinned in Task 8.
5. **An unmapped free-text value** (a new frame spelling): the expected result is the category `Diğer` and a count of unmapped values in the report, never a silent wrong category. Pinned in Task 2.

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
  - `@dataclass(frozen=True, order=True) class Coding: item: str; coder: str; field: str; value: str` — `item` is `<narrative key>__<outlet slug>` for narratives and `<event>__<card id>` for behaviour; `field` ∈ `FIELDS = ("blame_level", "frame_category", "present")`; `present` values ∈ `("yes", "no", "unsure")`.
  - `CODINGS = validation/reference/answerkey/codings.jsonl`; `read(path=CODINGS) -> list[Coding]`; `append(codings, path=CODINGS) -> int` (adds only records not present; refuses a second value from the same coder for the same item and field with `ValueError` naming the item).
  - `from_core(core: dict, codebook: dict) -> list[Coding]` — the existing human narrative coding as coder `"A"` (both narrative fields), derived on the fly, never written to `codings.jsonl`.
  - `units(codings, field) -> dict[str, list[str | None]]` — per item, one value per coder slot, sorted by slot; `unsure` counts as not coded.
  - `agreement(codings, field) -> dict` → `{"items_double": int, "alpha": float | None, "percent": float | None, "usable": bool}`; `usable` = `items_double >= 30 and alpha is not None and alpha >= 0.67`.
  - `gold(codings, field) -> tuple[dict[str, str], list[str]]` → (item → value where every coder who coded it agrees, items with disagreement for adjudication).
  - CLI: `python -m validation.answerkey agreement` writes `docs/validation/reports/answerkey-agreement.md` (one row per field: double-coded items, alpha, percent, usable) and prints it.

- [ ] **Step 1: Write the failing tests**

```python
class RecordTest(unittest.TestCase):
    def test_append_dedupes_and_refuses_a_changed_answer(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.jsonl"
            a = Coding("e1__framing-effect", "A", "present", "yes")
            self.assertEqual(append([a, a], p), 1)
            with self.assertRaisesRegex(ValueError, "e1__framing-effect"):
                append([Coding("e1__framing-effect", "A", "present", "no")], p)
    def test_gold_and_disagreement(self):
        cs = [Coding("i1", "A", "present", "yes"), Coding("i1", "B", "present", "yes"),
              Coding("i2", "A", "present", "yes"), Coding("i2", "B", "present", "no"),
              Coding("i3", "A", "present", "unsure")]
        self.assertEqual(gold(cs, "present"), ({"i1": "yes"}, ["i2"]))
    def test_usable_needs_thirty_double_coded_items(self):
        cs = [Coding(f"i{n}", c, "present", "yes" if n % 2 else "no") for n in range(29) for c in "AB"]
        self.assertFalse(agreement(cs, "present")["usable"])
    def test_core_rows_become_coder_a(self):
        core = {"N": {"k1": {"status": "headline_coded", "rows": [{"s": "sabah", "frame": "Adli süreç", "blame": "Yargı (ima)"}]},
                      "k2": {"status": "agent_coded", "rows": [{"s": "sabah", "frame": "Adli süreç", "blame": ""}]}}}
        cb = {"categories": ["Yargı ve soruşturma", "Diğer"], "frames": {"Adli süreç": "Yargı ve soruşturma"}}
        self.assertEqual(sorted(from_core(core, cb)), [Coding("k1__sabah", "A", "blame_level", "implied"),
                                                       Coding("k1__sabah", "A", "frame_category", "Yargı ve soruşturma")])
```

- [ ] **Step 2: Run to see them fail** — `python3 -m unittest validation.tests.test_answerkey -v` → FAIL, no `record` module

- [ ] **Step 3: Implement `record.py` and the `agreement` sub-command of `__main__.py`** (argparse with sub-commands; later tasks add `packet`, `import`, `narrative-eval`, `behaviour-eval`, `examples`). `agreement` merges `read()` with `from_core(core, load_codebook())`, core from `--core` (default `public/data/core.bin`, read with `biasguard.news._load`).

- [ ] **Step 4: Run the tests** — PASS; then `python3 -m validation.answerkey agreement` prints three rows with `items_double` 0 and "not usable yet".

- [ ] **Step 5: Commit** — `feat(answerkey): coding record, gold and agreement report`

---

### Task 4: Blind coding packets and their import

A packet is a spreadsheet a coder fills in without seeing any other coder's answer or the AI's verdict.

**Files:**
- Create: `validation/answerkey/packets.py`
- Modify: `validation/answerkey/__main__.py` (sub-commands `packet`, `import`)
- Test: `validation/tests/test_answerkey.py`

**Interfaces:**
- Consumes: `Coding`, `append`, `from_core`, `human_rows` (Tasks 2–3); `biasguard.catalog.load_cards()`.
- Produces:
  - `narrative_packet(core: dict, n_events: int, seed: int) -> list[dict]` — `n_events` narrative keys drawn with `random.Random(seed)` from the human-coded keys; one row per outlet: `{"item", "olay", "kurum", "başlık", "sorumlu_tutma": "", "çerçeve": ""}` (`olay` = `q.happened`, `kurum` = outlet name from core `S`, `başlık` = row `hl`). Rows without `hl` are skipped.
  - `behaviour_packet(results: dict, cards: list[dict], n_events: int, seed: int) -> tuple[list[dict], dict]` — from `n_events` completed events: every finding shown on the site (`supported` + `uncertain`) plus, per event, `max(shown, 2)` catalogue cards that are not in the event's `selected` list, drawn at random; rows `{"item", "başlıklar", "kavram", "tanım", "koşullar", "var_mı": ""}` in shuffled order; the second value is the private key `{item: {"event", "card", "ai_shown": bool}, "_unflagged": {event: {"sampled": int, "total": int}}}`, written next to the CSV as `<name>.key.json`.
  - `write_csv(rows, path)` — UTF-8 with byte-order mark, comma-separated, header row.
  - `read_coded(path, kind: str, coder: str, packet_items: list[str]) -> list[Coding]` — `kind` ∈ `("narrative", "behaviour")`; answers folded with `trFold`-equivalent lower-casing (`İ`→`i`, `I`→`ı`) and stripped; narrative: `sorumlu_tutma` ∈ {`yok`→`none`, `ima`→`implied`, `açık`→`explicit`}, `çerçeve` ∈ the codebook categories; behaviour: `var_mı` ∈ {`evet`→`yes`, `hayır`→`no`, `emin değilim`→`unsure`}; blank cells give no coding; any unknown item, missing item, duplicate item or unknown value raises `ValueError` naming the row number and nothing is returned.
  - CLI: `packet --kind narrative --events 20 --coder B --out runs/answerkey/narrative-B.csv`; `packet --kind behaviour --results runs/bg82/biasguard.json --events 30 --coder A --out runs/answerkey/behaviour-A.csv`; `import <csv> --kind … --coder …` (items read from the CSV's own `item` column of the packet, re-generated from the same seed to check nothing was added or lost).

- [ ] **Step 1: Write the failing tests**

```python
class PacketTest(unittest.TestCase):
    def test_behaviour_packet_is_blind_and_balanced(self):
        rows, key = behaviour_packet(RESULTS_FIXTURE, CARDS_FIXTURE, n_events=1, seed=1)
        self.assertEqual(set(rows[0]), {"item", "başlıklar", "kavram", "tanım", "koşullar", "var_mı"})   # no verdict column
        self.assertEqual(len(rows), 3)                                    # 1 shown finding + max(1, 2) unselected cards
        self.assertEqual(key["_unflagged"], {"e1": {"sampled": 2, "total": 3}})
    def test_read_coded_folds_turkish_case(self):
        p = self._csv([{"item": "k1__sabah", "sorumlu_tutma": " AÇIK", "çerçeve": "Spor"}])
        self.assertEqual(read_coded(p, "narrative", "B", ["k1__sabah"])[0], Coding("k1__sabah", "B", "blame_level", "explicit"))
    def test_read_coded_refuses_a_missing_row(self):
        p = self._csv([{"item": "k1__sabah", "sorumlu_tutma": "yok", "çerçeve": ""}])
        with self.assertRaisesRegex(ValueError, "k1__ntv"):
            read_coded(p, "narrative", "B", ["k1__sabah", "k1__ntv"])
    def test_read_coded_refuses_an_unknown_value(self):
        p = self._csv([{"item": "k1__sabah", "sorumlu_tutma": "belki", "çerçeve": ""}])
        with self.assertRaisesRegex(ValueError, "row 2"):
            read_coded(p, "narrative", "B", ["k1__sabah"])
```

`RESULTS_FIXTURE`, `CARDS_FIXTURE` and `_csv` are test helpers in the same file: one completed event `e1` with `selected: ["c1"]` and one `uncertain` finding of card `c1`, a catalogue of `c1`–`c4`, and a writer that saves rows with a byte-order mark. Row numbers in errors count the header as row 1.

- [ ] **Step 2: Run to see them fail** — FAIL, no `packets` module

- [ ] **Step 3: Implement `packets.py` and the two sub-commands**

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Smoke the round trip** — `python3 -m validation.answerkey packet --kind narrative --events 2 --coder B --out runs/answerkey/try.csv` writes a CSV that opens in a spreadsheet with Turkish letters intact; delete it afterwards.

- [ ] **Step 6: Commit** — `feat(answerkey): blind coding packets and import`

---

### Task 5: Score the narrative agent against the human-coded weeks

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

### Task 6: Measure the behavioural review against blind gold

**Files:**
- Create: `validation/answerkey/behaviour_eval.py`
- Modify: `validation/answerkey/__main__.py` (sub-command `behaviour-eval`)
- Test: `validation/tests/test_answerkey.py`

**Interfaces:**
- Consumes: `gold` (Task 3); the packet key file of Task 4; `validation.feedback.stats.wilson_lower`, `card_status`.
- Produces:
  - `measure(gold: dict[str, str], key: dict) -> dict` → `{"overall": {...}, "cards": {card: {...}}}` with, per scope: `tp` (AI-shown, gold yes), `fp` (AI-shown, gold no), `found_unflagged` (not shown, gold yes), `missed_est` = Σ over events of `found_unflagged_e × total_e / sampled_e`, `precision` = tp/(tp+fp) or `None`, `precision_lower` = `wilson_lower(tp, tp+fp)`, `recall_est` = tp/(tp+missed_est) or `None`.
  - `as_card_stats(m: dict) -> dict` — the shape `card_status()` reads: `{card: {"reviewed": tp+fp, "kept": tp, "rejected": fp, "precision": …, "lower": …}}`.
  - CLI: `behaviour-eval --key runs/answerkey/behaviour-A.key.json` writes `docs/validation/reports/behaviour-blind.md`; with `--status` it also writes `validation/reference/card_status.json` through the existing `card_status(stats, gates)`, with `"measure": "blind precision"`.

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

---

### Task 7: Human examples for the BiasGuard reviewers (learning without retraining)

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

- [ ] **Step 6 (when Task 6 shows a usable `present` field): adopt through the existing gate.** Run the loop in `docs/validation/ITERATIONS.md` with the examples file as the single change: replay run, lab run, `python -m validation.learning promote-check`. Record the Observation Ledger entry whatever the result. The examples become the default only if the promotion gate passes.

---

### Task 8: First trained baselines (mlbench)

**Files:**
- Create: `validation/mlbench/__init__.py`, `validation/mlbench/data.py`, `validation/mlbench/models.py`, `validation/mlbench/evaluate.py`, `validation/mlbench/__main__.py`
- Test: `validation/tests/test_mlbench.py`

**Interfaces:**
- Consumes: `human_rows`, `blame_level`, `frame_category`, `load_codebook` (Task 2); the agent's coded folder from Task 5.
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

### Task 9: Show measured narrative quality on the narrative page

**Files:**
- Modify: `pipeline/capraz_pipeline/narratives.py` (`merge`: core key `NQ` from `data/reference/narrative-quality.json`)
- Modify: `site/js/v7/logic.js` (add and export `narrQualityLine`), `site/js/v7/anlati.js` (`v7Body`)
- Test: `site/tests/logic.test.cjs`, `pipeline/tests/test_narratives.py`

**Interfaces:**
- Consumes: `data/reference/narrative-quality.json` (Task 5).
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
