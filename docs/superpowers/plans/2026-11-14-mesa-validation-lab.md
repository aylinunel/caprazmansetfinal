# Mesa Validation Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline lab that turns Mesa simulations into answer-free test cases, runs BiasGuard on them, and records every attempt with honest denominators.

**Architecture:** The Mesa package is vendored read-only. A new package `validation/biaslab/` holds a reviewed crosswalk, a whitelist renderer, an adapter that normalises BiasGuard results without collapsing outcomes, an append-only ledger and metrics. Model review reuses the existing file-based reviewer workflow (`biasguard.news` task batches and `FileReviewer`), so the lab itself never calls a provider.

**Tech Stack:** Python 3.12, `unittest`, Mesa 3.5.2 and NumPy (lab only), `pytest` (vendored Mesa suite only).

**Spec:** `docs/superpowers/specs/2026-11-14-capraz-final-integration-design.md`

## Global Constraints

- Prerequisite: the Foundation plan (the seeded repo and its CI).
- Nothing under `pipeline/`, `biasguard/` or `site/` may import from `validation/`.
- `biasguard/data/cards.json` is not changed. Proposed cards live under `validation/biaslab/proposed_cards/`.
- Vendored files under `validation/mesa_bias_expanded/` are byte-identical to the archive; never edited.
- Detector-visible input is exactly two strings: `text` and `context`.
- Forbidden in detector-visible input, task batches and file names the reviewer sees: concept ids,
  detector card ids chosen as targets, `positive`, `boundary`, `strength`, `seed`, `split`, `expected`,
  `active`, family ids.
- Statuses are exactly: `supported`, `contextual_effect`, `not_supported`, `uncertain`, `unassessed`,
  `ineligible`, `error`.
- A ratio with a zero denominator is `None`. It is never 0, never 1, never a pass.
- The sampling unit for intervals is the family, not the row, agent or seed.
- No Mesa metric is combined with, or converted into, a detector score.
- Results from this lab are labelled "synthetic, implementation-authored" wherever they are written.
- Lab tests are `unittest`. Mesa must be installed for them; there are no skip-if-missing decorators.
- Follow the owner's standing instructions: `ponytail` and `anthropic-skills:karpathy-guidelines`.

## Review Focus

1. A case id, batch file name or JSON key that reveals the label → the leak check rejects the case
   before it is written. (Task 5)
2. Evidence whose quote occurs more than once → every occurrence becomes its own span; none is dropped.
   (Task 6)
3. A run where no case completes → every ratio is `None`, the report says "not estimable", exit code is
   non-zero. (Tasks 8, 10)
4. Turkish text with `İ/ı/ş/ğ` and an emoji before the quote → offsets are Python code-point offsets and
   round-trip exactly. (Task 6)
5. Two ledger writes for the same case and configuration → both are kept; the first attempt is the one
   scored. (Task 7)

---

### Task 1: Vendor the simulator

**Files:**
- Create: `validation/__init__.py`, `validation/mesa_bias_expanded/**` (from the archive, excluding
  `results/sweep/`, `results/sweep_first_attempt/`, `results/pytest_results.xml`)
- Create: `validation/reference_adapter/reference_adapter.py` (the owner's uploaded file, unchanged) and
  `validation/reference_adapter/README.md` stating it is the guide's Appendix A mock demo, kept for
  comparison, and that its `MockContractDetector` must never be used on real text
- Create: `validation/requirements.txt` — `mesa==3.5.2`, `numpy>=1.26,<3`, `pytest>=8,<10`
- Create: `validation/tests/__init__.py`, `validation/tests/test_vendored.py`
- Modify: `.github/workflows/checks.yml` (jobs `lab` and `mesa`)

**Interfaces:**
- Produces: `validation/mesa_bias_expanded/expanded_mesa.py` importable after its directory is put on
  `sys.path` (Task 3 does this in one place).

- [ ] **Step 1: Write the failing test**

```python
ROOT = Path(__file__).resolve().parents[1] / "mesa_bias_expanded"
EXCLUDED = ("results/sweep/", "results/sweep_first_attempt/", "results/pytest_results.xml")

def test_every_vendored_file_matches_its_checksum(self):
    sums = json.loads((ROOT / "SHA256SUMS.json").read_text())
    kept = {p: h for p, h in sums.items() if not p.startswith(EXCLUDED)}
    self.assertGreater(len(kept), 400)
    for rel, expected in kept.items():
        self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), expected, rel)

def test_scope_is_138_synthetic_only(self):
    meta = json.loads((ROOT / "runtime_metadata.json").read_text())
    self.assertEqual(meta["expected_new_plugins"], 138)
    self.assertIs(meta["empirically_validated"], False)

def test_reference_adapter_smoke_tests_pass_against_the_vendored_package(self):
    out = subprocess.run([sys.executable, "validation/reference_adapter/reference_adapter.py"],
                         env={**os.environ, "MESA_BIAS_ROOT": str(ROOT)}, capture_output=True, text=True)
    self.assertEqual(out.returncode, 0, out.stderr[-400:])
    self.assertTrue(json.loads(out.stdout)["smoke_tests"].startswith("PASS"))
```

- [ ] **Step 2: Run and confirm failure** — `python -m unittest validation.tests.test_vendored -v`.
- [ ] **Step 3: Extract the archive** into `validation/mesa_bias_expanded/`, leaving out the excluded paths. If `SHA256SUMS.json` keys carry a prefix, adjust `ROOT`, not the files.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Re-run the vendored suite once**

Run: `python -m pip install -r validation/requirements.txt`
Run: `cd validation/mesa_bias_expanded && python -m pytest -q`
Expected: 1531 passed. Record the actual count and Python version in
`docs/provenance/mesa-vendor-check.md`. A different count is recorded, not fixed.

- [ ] **Step 6: Add CI jobs** `lab` (installs `pipeline/requirements.txt` and
  `validation/requirements.txt`, runs `python -m unittest discover -s validation/tests -t . -v`) and
  `mesa` (`cd validation/mesa_bias_expanded && python -m pytest -q`; runs only when
  `validation/mesa_bias_expanded/**` changes, `timeout-minutes: 30`).
- [ ] **Step 7: Commit** — `git commit -m "feat: vendor Mesa bias simulator with checksum test"`.

---

### Task 2: Crosswalk

**Files:**
- Create: `validation/biaslab/__init__.py`, `validation/biaslab/crosswalk.py`,
  `validation/biaslab/crosswalk.json`, `validation/biaslab/build_crosswalk.py` (one-off generator, kept)
- Test: `validation/tests/test_crosswalk.py`

**Interfaces:**
- Produces:
  ```python
  TIERS = ("headline_lede", "full_article", "decision_history", "internal_state")
  RELATIONSHIPS = ("candidate_same_id", "equivalent_within_task", "narrower", "overlapping",
                   "context_only_effect", "unsupported_in_current_taxonomy")
  REVIEW_STATUSES = ("needs_domain_review", "pilot", "approved", "rejected")

  @dataclass(frozen=True)
  class Entry:
      simulation_id: str
      detector_id: str | None
      relationship: str
      evidence_tier: str
      policy: str            # the card's review_policy, or "media_pattern_review"
      review_status: str
      required_evidence: tuple[str, ...]

  def load() -> dict[str, Entry]
  def resolve(simulation_id: str, available_tier: str = "headline_lede") -> str | None
  def coverage() -> dict   # counts by relationship, review_status, tier; resolvable count
  ```
- `resolve` returns a detector id only when `review_status in ("pilot", "approved")`, `detector_id` is
  not `None` and `TIERS.index(entry.evidence_tier) <= TIERS.index(available_tier)`.
- Generated content: 112 entries with `detector_id = simulation_id.replace("_", "-")`,
  `relationship: "candidate_same_id"`, `review_status: "needs_domain_review"`, `policy` copied from the
  card, tier `decision_history` when the card's policy is `requires_behavioral_evidence` or the Mesa
  plugin kind is `psychological_state` (then `internal_state`), else `headline_lede`. 26 entries with
  `detector_id: null`, `relationship: "unsupported_in_current_taxonomy"`,
  `policy: "media_pattern_review"`; tier `full_article` for `source_selection`, `one_sided_sourcing`,
  `commission_and_omission_of_information`, `contextual_omission`, `size_allocation`,
  `story_placement`, `picture_selection`, `picture_explanation`, `event_selection`; `headline_lede`
  for the rest.
- Hand edits after generation: `illusory_truth_effect` → `review_status: "pilot"`;
  `selective_statistics` → `required_evidence` = the three strings in the guide's crosswalk example.

- [ ] **Step 1: Write the failing tests**

```python
def test_one_entry_per_mesa_concept(self):
    self.assertEqual(set(load()), set(mesa_ids()))          # 138 ids from missing_concepts.json

def test_counts(self):
    c = coverage()
    self.assertEqual(c["relationship"]["candidate_same_id"], 112)
    self.assertEqual(c["relationship"]["unsupported_in_current_taxonomy"], 26)
    self.assertEqual(c["resolvable"], 1)

def test_every_detector_id_is_a_real_card(self):
    cards = {c["id"] for c in load_cards()}
    self.assertTrue(all(e.detector_id in cards for e in load().values() if e.detector_id))

def test_unreviewed_same_id_match_does_not_resolve(self):
    self.assertIsNone(resolve("the_sunk_cost_fallacy"))

def test_pilot_entry_resolves(self):
    self.assertEqual(resolve("illusory_truth_effect"), "illusory-truth-effect")

def test_media_technique_has_no_detector_id(self):
    self.assertIsNone(resolve("selective_statistics"))

def test_tier_above_available_does_not_resolve(self): ...   # patch an approved entry to full_article
def test_unknown_id_raises_keyerror(self): ...
def test_invalid_enum_in_file_raises_valueerror(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Write `validation/biaslab/build_crosswalk.py`, run it, apply the two hand edits, implement `crosswalk.py`.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: reviewed-status crosswalk between Mesa and BiasGuard"`.

---

### Task 3: Simulation wrapper

**Files:**
- Create: `validation/biaslab/sim.py`
- Test: `validation/tests/test_sim.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Realized:
      concept: str
      scenario: dict            # as passed to Mesa, deep-copied
      seed: int
      strength: float
      agent: int
      active: bool
      metric: float
      reference_metric: float
      state: dict               # this agent's final state under intervention
      trace: tuple[str, ...]

  def scenario(concept: str, name: str) -> dict
  def realize(concept: str, scenario: dict, *, seed: int = 42, strength: float = 0.8,
              n_agents: int = 12) -> tuple[Realized, ...]
  ```
- `sim.py` is the only module that touches `sys.path`; it inserts the vendored directory once and
  imports `expanded_mesa`. `realize` runs `ExpandedDecisionModel` twice (strength 0 and `strength`) with
  the same seed and reads `agent.active`, `agent.metric`, `agent.state` from the intervention model.

- [ ] **Step 1: Write the failing tests**

```python
def test_positive_selective_statistics_has_active_and_inactive_agents(self):
    rs = realize("selective_statistics", scenario("selective_statistics", "positive"))
    self.assertEqual(len(rs), 12)
    self.assertTrue(any(r.active for r in rs)); self.assertTrue(any(not r.active for r in rs))

def test_active_agent_reports_the_narrow_denominator(self):
    r = next(r for r in realize("selective_statistics", scenario("selective_statistics", "positive")) if r.active)
    self.assertEqual((r.state["last_denominator_used"], r.metric, r.reference_metric), (20, 50.0, 10.0))

def test_boundary_is_never_active(self):
    self.assertFalse(any(r.active for r in realize("selective_statistics", scenario("selective_statistics", "boundary"))))

def test_same_seed_is_deterministic(self): ...
def test_unknown_concept_raises(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: realised-observation wrapper over Mesa runner"`.

---

### Task 4: Cases, families and expectations

**Files:**
- Create: `validation/biaslab/cases.py`
- Test: `validation/tests/test_cases.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class DetectorInput:
      text: str
      context: str = ""

  @dataclass(frozen=True)
  class Expected:
      acceptable: frozenset[str]   # statuses that count as correct
      forbidden: frozenset[str]    # statuses that are a violation

  @dataclass(frozen=True)
  class Case:
      case_id: str                 # "c-" + 12 hex chars
      input: DetectorInput
      private: dict                # concept, kind, family_id, split, variant, seed, strength, active, trace

  KINDS = ("positive", "inactive_control", "boundary_control", "missing_context", "quoted_control")
  PERTURBATIONS = ("none", "reverse_outlets", "relabel_outlets", "irrelevant_detail")

  def family_id(concept: str, facts: dict) -> str     # sha256 of concept + canonical JSON of facts, 16 hex
  def split_of(family: str) -> Literal["dev", "test"] # int(family, 16) % 5 == 0 → "test"
  def case_id(input: DetectorInput, salt: str) -> str # sha256(salt + text + "\0" + context)[:12], prefixed
  def expected(kind: str, resolvable: bool) -> Expected
  ```
- `expected` table:
  | kind | resolvable | acceptable | forbidden |
  |---|---|---|---|
  | any | False | `{ineligible}` | `{supported, contextual_effect, not_supported}` |
  | `positive` | True | `{supported, contextual_effect}` | `{}` |
  | `inactive_control`, `boundary_control`, `quoted_control` | True | `{not_supported, uncertain}` | `{supported, contextual_effect}` |
  | `missing_context` | True | `{uncertain, not_supported}` | `{supported, contextual_effect}` |
- `case_id` depends only on visible content and a per-run random salt, so it carries no label.

- [ ] **Step 1: Write the failing tests**

```python
def test_same_facts_share_family_and_split(self):
    a = family_id("selective_statistics", {"event_count": 10, "relevant_denominator": 100, "selected_denominator": 20})
    b = family_id("selective_statistics", {"selected_denominator": 20, "relevant_denominator": 100, "event_count": 10})
    self.assertEqual(a, b); self.assertEqual(split_of(a), split_of(b))

def test_case_id_is_opaque(self):
    cid = case_id(DetectorInput("metin", "bağlam"), salt="s")
    self.assertRegex(cid, r"^c-[0-9a-f]{12}$")

def test_case_id_changes_with_salt(self): ...
def test_unresolvable_target_expects_ineligible(self):
    self.assertEqual(expected("positive", False).acceptable, frozenset({"ineligible"}))
def test_missing_context_forbids_supported(self):
    self.assertIn("supported", expected("missing_context", True).forbidden)
def test_unknown_kind_raises(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: case, family and expectation model"`.

---

### Task 5: Renderer and leak check

**Files:**
- Create: `validation/biaslab/renderer.py`
- Test: `validation/tests/test_renderer.py`

**Interfaces:**
- Consumes: `Realized`, `DetectorInput`, `KINDS`.
- Produces:
  ```python
  class Leak(ValueError): ...
  FORBIDDEN = ("positive", "boundary", "strength", "seed", "split", "expected", "active",
               "inactive_control", "missing_context", "quoted_control")

  def render(realized: Realized, kind: str, variant: int, perturbation: str = "none") -> DetectorInput
  def assert_no_leak(obj: object, concept: str, detector_id: str | None, family: str) -> None
  def variants(concept: str) -> int        # number of surface templates for the concept
  ```
- `assert_no_leak` serialises `obj` to JSON, lower-cases it (Turkish-safe: `casefold`), and raises
  `Leak` if it contains any `FORBIDDEN` token as a whole word, the concept id in `_` or `-` or space
  form, the detector id, or the family id. Tests call it on the input and on every task batch.
- Inputs follow the news shape BiasGuard already receives: `text` is lines of
  `[Kurum X · HH:MM] <headline> — <lede>`; `context` starts with `Olay: …`.
- `selective_statistics`, variant 0 (rate `r` = `state["last_rate_per_100"]`, denominator `d` =
  `state["last_denominator_used"]`, count `n`, relevant denominator `R`; whole numbers print without
  decimals):
  - text: `[Kurum A · 09:00] Denetimde ihlal oranı yüzde {r} — İncelenen {d} dosyanın {n} tanesinde ihlal saptandı; rapor benzer tüm dosyalar için uyarıyor.`
  - context: `Olay: Denetim raporu açıklandı\nKarşılaştırma verisi: benzer nitelikteki {R} dosyanın {n} tanesinde ihlal var; ihlallerin tümü incelenen dosyalar arasında.`
  - `missing_context`: same text, context is only the `Olay:` line.
  - `quoted_control`: the headline is attributed and rejected:
    `[Kurum A · 09:00] Muhalefet "ihlal oranı yüzde {r}" dedi, Sayıştay rakamı düzeltti — Kurum, oranın benzer {R} dosyada yüzde {n*100/R} olduğunu açıkladı.`
  - At least two further variants that change entity, sentence order and tone; a charged word must
    appear in at least one control and be absent from at least one positive.
- Perturbations keep the expected status: `reverse_outlets` reverses the order of the `[Kurum …]`
  lines (applies only to inputs with two or more lines; otherwise identical to `none`);
  `relabel_outlets` replaces `Kurum A/B` with `Kurum X/Y`; `irrelevant_detail` appends
  ` Açıklama Ankara'da yapıldı.` to the last lede. Private record gains `perturbation` and
  `base_case_id` (the `none` rendering of the same case).
- `illusory_truth_effect`, variant 0: one line per simulation context, 30 minutes apart, alternating
  `Kurum A`/`Kurum B`; with empty `evidence` each line repeats
  `Bakanlık: Şebeke suyu güvenli` plus a rewording and no new source; with evidence each line adds
  `— {k}. bağımsız laboratuvar raporu yayımlandı`. Context: `Olay: Şebeke suyu tartışması`.

- [ ] **Step 1: Write the failing tests**

```python
def test_output_is_only_text_and_context(self):
    self.assertEqual(set(dataclasses.asdict(render(active, "positive", 0))), {"text", "context"})

def test_active_positive_states_the_narrow_rate_and_supplies_the_wide_cohort(self):
    d = render(active, "positive", 0)
    self.assertIn("yüzde 50", d.text); self.assertIn("20 dosyanın 10", d.text)
    self.assertIn("100 dosyanın 10", d.context)

def test_inactive_agent_renders_the_reference_rate(self):
    self.assertIn("yüzde 10", render(inactive, "inactive_control", 0).text)

def test_missing_context_removes_the_comparison(self):
    self.assertNotIn("Karşılaştırma", render(active, "missing_context", 0).context)

def test_boundary_pair_renders_identically(self): ...   # strength 0 vs 0.8 on the boundary scenario

def test_private_state_changes_do_not_change_rendering(self):
    self.assertEqual(render(active, "positive", 0),
                     render(dataclasses.replace(active, trace=("x",), seed=7), "positive", 0))

def test_every_variant_of_every_kind_passes_the_leak_check(self):
    for concept in ("selective_statistics", "illusory_truth_effect"):
        for v in range(variants(concept)): ...  # assert_no_leak does not raise

def test_leak_check_catches_label_in_text(self):
    with self.assertRaises(Leak):
        assert_no_leak(DetectorInput("bu bir positive örnek"), "selective_statistics", None, "ab12")

def test_leak_check_catches_concept_id_in_a_key_or_filename(self):
    with self.assertRaises(Leak):
        assert_no_leak({"file": "selective-statistics-01.json"}, "selective_statistics", None, "ab12")

def test_charged_wording_is_not_confined_to_positives(self): ...
def test_unsupported_concept_raises_keyerror(self): ...
def test_relabel_changes_only_outlet_names(self):
    a, b = render(active, "positive", 0), render(active, "positive", 0, "relabel_outlets")
    self.assertEqual(a.text.replace("Kurum A", "Kurum X"), b.text); self.assertEqual(a.context, b.context)
def test_irrelevant_detail_keeps_every_number(self):
    a, b = render(active, "positive", 0), render(active, "positive", 0, "irrelevant_detail")
    self.assertEqual(re.findall(r"\d+", a.text), re.findall(r"\d+", b.text))
def test_reverse_outlets_reverses_line_order_for_multi_line_input(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** with a registry `{concept: [template_fn, …]}`.
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: whitelist renderer with leak check for two pilot concepts"`.

---

### Task 6: Adapter

**Files:**
- Create: `validation/biaslab/adapter.py`
- Test: `validation/tests/test_adapter.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Span:
      source: Literal["text", "context"]
      quote: str
      start: int      # Python code-point offset
      end: int

  @dataclass(frozen=True)
  class Assessment:
      target: str | None
      status: str
      reason: str
      spans: tuple[Span, ...]
      native_status: str            # BiasGuard's top-level status
      native_adjudication: str | None
      missing_context: tuple[str, ...]
      extra_supported: tuple[str, ...]   # other cards with pattern_supported; unadjudicated, not "false positives"

  def normalize(result: dict, target: str | None) -> Assessment
  ```
- Mapping:
  | condition | status |
  |---|---|
  | `target is None` | `ineligible` |
  | `result["status"] == "input_rejected"` | `error` |
  | `offline_candidates_only` | `unassessed` |
  | `analysis_incomplete` and target not among fully assessed cards | `error` |
  | target absent from `adjudication` on `review_complete` | `unassessed` |
  | adjudication `pattern_supported` | `supported` |
  | `contextual_effect_consensus` | `contextual_effect` |
  | `reviewer_disagreement`, `needs_context` | `uncertain` |
  | `suppressed` | `not_supported` |
- Spans come from the matching finding's `evidence`: one `Span` per `(start_offsets[i], end_offsets[i])`.
- `normalize` raises `ValueError` if a span's slice of the original field does not equal its quote; it
  takes the original input as part of `result["audit"]` hashes only, so the caller passes text/context
  through a second function `verify_spans(assessment, input) -> None`.

- [ ] **Step 1: Write the failing tests** — build real results by running
  `BiasGuard(cards=[card], reviewer=StubReviewer(...)).analyze(..., mode="ai")` with a stub reviewer
  modelled on `biasguard/test_news.py`.

```python
def test_none_target_is_ineligible_without_reading_the_result(self):
    self.assertEqual(normalize({}, None).status, "ineligible")
def test_offline_mode_is_unassessed_not_negative(self): ...
def test_both_supported_is_supported(self): ...
def test_effect_context_only_card_is_contextual_effect(self): ...
def test_disagreement_is_uncertain(self): ...
def test_both_not_supported_is_not_supported(self): ...
def test_reviewer_failure_is_error(self): ...               # stub raises → analysis_incomplete
def test_target_not_selected_is_unassessed(self): ...
def test_repeated_quote_yields_one_span_per_occurrence(self):
    # text contains the quote twice → len(spans) == 2 and offsets differ
def test_turkish_and_emoji_offsets_round_trip(self):
    text = "🙂 İşçiler ığdır'da: Krizi herkes görüyor"
    ...; verify_spans(a, DetectorInput(text))
    self.assertEqual(text[a.spans[0].start:a.spans[0].end], a.spans[0].quote)
def test_verify_spans_rejects_shifted_offsets(self): ...
def test_other_supported_cards_are_listed_as_extra_not_errors(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: BiasGuard result adapter that keeps outcomes distinct"`.

---

### Task 7: Ledger

**Files:**
- Create: `validation/biaslab/ledger.py`
- Test: `validation/tests/test_ledger.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Attempt:
      case_id: str
      config: str            # "baseline" or "candidate"
      attempt: int           # 1-based, assigned by the ledger
      status: str
      target: str | None
      native_status: str
      spans: tuple[dict, ...]
      card_hash: str
      prompts_version: str
      recorded_at: str       # UTC ISO-8601

  class Ledger:
      def __init__(self, path: Path) -> None
      def record(self, case_id: str, config: str, assessment: Assessment, audit: dict) -> Attempt
      def attempts(self) -> list[Attempt]
      def first_attempts(self, config: str) -> dict[str, Attempt]
  ```
- JSONL, append-only (`open(path, "a")`); the file is never rewritten. The ledger stores no `private`
  fields; private case records live in a separate `cases.private.jsonl` written by the runner.

- [ ] **Step 1: Write the failing tests**

```python
def test_second_write_is_kept_and_numbered(self): ...        # attempts 1 and 2 both present
def test_first_attempt_is_the_scored_one(self): ...          # first is "error", second "supported" → "error"
def test_ledger_survives_reopen(self): ...
def test_ledger_never_contains_private_keys(self):
    self.assertNotRegex(path.read_text(), r"family|split|strength|expected|kind")
def test_corrupt_line_raises_with_line_number(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: append-only attempt ledger"`.

---

### Task 8: Metrics

**Files:**
- Create: `validation/biaslab/metrics.py`
- Test: `validation/tests/test_metrics.py`

**Interfaces:**
- Produces:
  ```python
  def ratio(n: int, d: int) -> float | None

  @dataclass(frozen=True)
  class Row:               # one first attempt joined with its private case record
      family: str; kind: str; status: str
      acceptable: frozenset[str]; forbidden: frozenset[str]
      span_ok: bool

  def summarize(rows: Sequence[Row]) -> dict
  def paired_bootstrap(baseline: Sequence[Row], candidate: Sequence[Row], metric: str,
                       *, n_boot: int = 2000, seed: int = 0) -> dict
  ```
- `summarize` keys and definitions (each value `{"n", "d", "value"}`):
  - `completion`: status not `error` / all rows.
  - `eligible`: status not `ineligible` / all rows.
  - `decision_coverage`: status in `{supported, contextual_effect, not_supported}` / rows not `ineligible`.
  - `end_to_end_recall`: `positive` rows whose status is acceptable / all eligible `positive` rows
    (errors, unassessed and uncertain count as misses).
  - `conditional_recall`: same numerator / eligible `positive` rows with a decision.
  - `strict_precision`: rows with status `supported|contextual_effect`, kind `positive`, `span_ok` /
    all rows with status `supported|contextual_effect`.
  - `forbidden_rate`: control rows whose status is in `forbidden` / eligible control rows with a decision.
  - `unsupported_assertion_rate`: `missing_context` rows with a forbidden status / eligible
    `missing_context` rows.
  - `perturbation_consistency`: perturbed rows whose status equals their base case's status /
    perturbed rows where both completed (`Row` gains `base_status: str | None`).
  - plus `counts_by_status` and `families`.
- `paired_bootstrap` resamples family ids with replacement, keeps every row of a drawn family for both
  configurations, and returns `{"point", "lo", "hi", "families", "n_boot", "undefined_draws"}` for
  candidate minus baseline. If `undefined_draws / n_boot > 0.05` or `families < 10`, `lo` and `hi` are
  `None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_zero_denominator_is_none(self):
    self.assertIsNone(ratio(0, 0)); self.assertEqual(ratio(0, 4), 0.0)

def test_precision_with_no_positives_predicted_is_none_not_one(self):
    s = summarize([row(kind="boundary_control", status="not_supported")])
    self.assertIsNone(s["strict_precision"]["value"])

def test_errors_count_against_end_to_end_recall_but_not_conditional(self):
    rows = [row("positive", "supported"), row("positive", "error")]
    s = summarize(rows)
    self.assertEqual((s["end_to_end_recall"]["value"], s["conditional_recall"]["value"]), (0.5, 1.0))

def test_supported_with_bad_span_is_not_a_strict_true_positive(self): ...
def test_ineligible_rows_leave_semantic_denominators(self): ...
def test_perturbation_consistency_ignores_pairs_where_either_side_errored(self): ...
def test_all_error_run_has_no_estimable_semantic_metric(self):
    s = summarize([row("positive", "error")] * 3)
    self.assertEqual(s["completion"]["value"], 0.0)
    self.assertIsNone(s["conditional_recall"]["value"]); self.assertIsNone(s["strict_precision"]["value"])

def test_bootstrap_resamples_families_not_rows(self):
    # 2 families × 50 identical rows each → families == 2 and lo/hi are None
def test_bootstrap_is_deterministic_for_a_seed(self): ...
def test_bootstrap_requires_matching_case_sets(self): ...   # ValueError
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** (`random.Random(seed)`; no NumPy needed).
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: lab metrics with undefined ratios and family bootstrap"`.

---

### Task 9: Lab-only proposed card and configurations

**Files:**
- Create: `validation/biaslab/proposed_cards/selective-statistics.json`
- Create: `validation/biaslab/configs.py`
- Test: `validation/tests/test_configs.py`

**Interfaces:**
- Produces:
  ```python
  def catalog(config: Literal["baseline", "candidate"]) -> list[dict]
  def target(simulation_id: str, config: str) -> str | None
  def manifest(config: str) -> dict   # card_hash, prompts_version, card_count, proposed_card_ids
  ```
- `baseline` = `biasguard.catalog.load_cards()` unchanged. `candidate` = baseline plus every file in
  `proposed_cards/`. `target` is `crosswalk.resolve(...)` for baseline; for candidate it also maps
  `selective_statistics` → `selective-statistics`.
- The proposed card passes `biasguard.catalog.validate_cards`, has `review_policy:
  "bias_error_review"`, `provenance` beginning `LAB-ONLY PROPOSAL, not reviewed, not in production`,
  and exactly these three `necessary_conditions`:
  1. `The text presents a rate or share and its numerator and denominator can be identified from the text or context.`
  2. `The supplied context documents a different comparison population and shows it is comparable to the one used.`
  3. `The text's claim extends beyond the population its denominator covers; a claim explicitly confined to the subgroup does not qualify.`

- [ ] **Step 1: Write the failing tests**

```python
def test_baseline_is_the_stock_catalog(self):
    self.assertEqual(manifest("baseline")["card_hash"], BiasGuard().analyze("x", mode="offline")["audit"]["card_hash_sha256"])
def test_candidate_adds_exactly_the_proposed_cards(self):
    self.assertEqual(manifest("candidate")["card_count"], 117)
def test_production_catalog_file_does_not_contain_the_proposal(self):
    self.assertNotIn("selective-statistics", Path("biasguard/data/cards.json").read_text())
def test_targets(self):
    self.assertIsNone(target("selective_statistics", "baseline"))
    self.assertEqual(target("selective_statistics", "candidate"), "selective-statistics")
    self.assertEqual(target("illusory_truth_effect", "baseline"), "illusory-truth-effect")
def test_proposed_card_has_three_conditions_and_lab_only_provenance(self): ...
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Write the card and `configs.py`.**
- [ ] **Step 4: Run and confirm pass.**
- [ ] **Step 5: Commit** — `git commit -m "feat: baseline and candidate lab configurations"`.

---

### Task 10: Runner CLI

**Files:**
- Create: `validation/biaslab/__main__.py`, `validation/biaslab/run.py`
- Modify: `biasguard/news.py` — `write_tasks(run, stage, batch, bg=None)` and
  `selected_cards` use the supplied `BiasGuard` when given; default behaviour unchanged
- Create: `validation/README.md`
- Modify: `.gitignore` — add `runs/lab/`
- Test: `validation/tests/test_run.py`, `biasguard/test_news.py` (one new test)

**Interfaces:**
- Consumes: everything above.
- Produces three commands, mirroring the existing BiasGuard workflow:
  - `python -m validation.biaslab build --run runs/lab/<name> [--seed 42]`
    writes `inputs.jsonl` (rows `{"event": case_id, "title": "", "outlets": 1, "text", "context"}`),
    `cases.private.jsonl`, `salt.txt` and `manifest.json`. Every row passes `assert_no_leak`.
    Cases: for each pilot concept, for each of its scenarios, one case per (kind, variant) using the
    first active and first inactive agent, and each such case again under every perturbation.
  - `python -m validation.biaslab tasks --run … --config baseline|candidate --stage select|review`
    calls `biasguard.news.write_tasks(..., bg=BiasGuard(cards=configs.catalog(config)))` into
    `<run>/<config>/`, then runs `assert_no_leak` on each written batch.
  - `python -m validation.biaslab score --run … [--mode ai|offline]`
    for each config and case: `BiasGuard(cards, reviewer=FileReviewer(<run>/<config>, case_id))
    .analyze(...)`, `normalize`, `verify_spans`, `Ledger.record`; then writes `report.json` with
    `summarize` per config, `paired_bootstrap` for `end_to_end_recall` and `strict_precision`,
    `crosswalk.coverage()`, both manifests, and the fixed line
    `"scope": "synthetic, implementation-authored cases; not detector accuracy"`.
    Any `None` metric is printed as `not estimable`. Exit code 0 only if `completion` is 1.0 for both
    configs; otherwise 2.
- `validation/README.md` covers: what the lab is and is not, the three commands, where private records
  live, and the sentence from the guide's Section 14 that is safe to state publicly.

- [ ] **Step 1: Write the failing tests**

```python
def test_build_writes_only_text_and_context_for_the_detector(self):
    rows = [json.loads(l) for l in (run / "inputs.jsonl").read_text().splitlines()]
    self.assertTrue(all(set(r) == {"event", "title", "outlets", "text", "context"} for r in rows))
    self.assertTrue(all(re.fullmatch(r"c-[0-9a-f]{12}", r["event"]) for r in rows))

def test_private_records_are_separate_and_complete(self): ...   # one private row per input row, with kind/family/split

def test_all_variants_of_a_family_share_a_split(self): ...

def test_offline_score_reports_everything_unassessed_or_ineligible(self):
    report = score(run, mode="offline")
    self.assertEqual(set(report["baseline"]["counts_by_status"]), {"unassessed", "ineligible"})
    self.assertIsNone(report["baseline"]["end_to_end_recall"]["value"])

def test_score_with_no_reviewer_files_is_all_error_and_exits_2(self): ...

def test_score_with_stub_reviewer_files_end_to_end(self):
    # write selection/advocate/skeptic JSON files for one selective-statistics positive case under
    # <run>/candidate/, score, and assert: candidate status "supported", baseline status "ineligible",
    # report scope line present.

def test_task_batches_pass_the_leak_check(self): ...

def test_news_write_tasks_default_is_unchanged(self): ...       # in biasguard/test_news.py
```

- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Add the optional `bg` parameter in `biasguard/news.py`.** Run `python -m unittest biasguard.test_news -v`; expected PASS.
- [ ] **Step 4: Implement `run.py` and `__main__.py`; write the README.**
- [ ] **Step 5: Run the whole lab suite and every inherited suite**

Run: `python -m unittest discover -s validation/tests -t . -v`
Run: `python -m unittest discover -s tests_repo -t . -v`
Run: `cd pipeline && python -m unittest discover -s tests -v`
Run: `python -m unittest biasguard.test_news -v`
Run: `node --test site/tests/logic.test.cjs`
Expected: every suite passes.

- [ ] **Step 6: Commit and push**

```bash
git commit -am "feat: validation lab build, tasks and score commands"
git push -u origin claude/zen-ptolemy-7bvru2
```

---

## What this plan does not produce

- A reviewer run. `tasks` writes batches; dispatching reviewer agents (as in
  `biasguard/AGENT_REVIEW.md`) or a provider is an owner decision and costs model usage.
- Any accuracy figure for real headlines. That is Plan 3.
- Approval of the 112 same-id crosswalk entries.
