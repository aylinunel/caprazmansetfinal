# Single-Source Lens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every active general-news outlet a "Bu kaynağı tek başına okusaydınız" lens: same-story rate ratios on four proven measures, a distance from the full picture, missed big stories, and "systematically" wording only when a pattern is unmistakable.

**Architecture:** A build step `pipeline/capraz_pipeline/lens.py` reads `core.bin` and the article packs, computes everything (statistics in a small shared `stats.py`), and writes `data/reference/lens-82.json`; `narratives.merge` ships it as core key `LENS`. The site only draws: wording helpers in `logic.js` (tested), drawing in a new `site/js/v7/lens.js` on the outlet page and the Kurumlar list.

**Tech Stack:** Python 3.13 with numpy, scipy, scikit-learn (already used); `unittest`; plain JavaScript and D3 7.9 (vendored), `node site/tests/logic.test.cjs`, `site/tests/smoke.cjs`.

**Spec:** `docs/superpowers/specs/2026-11-21-single-source-lens-design.md`; OpenSpec change `openspec/changes/add-single-source-lens/` (behaviour contract in `specs/single-source-lens/spec.md`).

## Global Constraints

- Every comparison is on the same stories: Mantel–Haenszel risk ratio stratified by story, Greenland–Robins 95% interval, Cochran–Mantel–Haenszel test with continuity correction.
- Comparison group = lens holders = registry type `print`, `tv`, `web` or `online`; active on ≥ 50% of the season's days (`PARAMS.active_day_share`); not in `data/reference/lens-groups.json`.
- Measures use the outlet's first headline per story. Loaded = headline score `v` ≥ 25; harsher = `v − lv` ≥ 15 with a lede; both on political headlines (`p`) only. First to report = first headline within 60 minutes of the story's first headline, ignoring times of exactly `00:00`.
- Big story = covered by ≥ 50% of comparison-group outlets active on the story's first day. Notice stories are excluded everywhere (article notice = `nu & 1` or all-capitals title containing a notice keyword; event notice = notice share ≥ 0.5).
- Complete feed (skip measure only): active ≥ 50% of days, median ≥ 20 headlines per active day, < 10% of active days at its own maximum daily count. Skip confirmed only when no headline of the outlet within 48 h of the story's first headline has cosine ≥ 0.33 (`cluster.vectors`) with any of the story's headlines.
- Measure counted only with ≥ 20 stories. Distance = 2^(mean |log2 RR|), RR clipped to [0.25, 4], needs ≥ 3 measures.
- "Systematically": n ≥ 20, RR ≥ 2 or ≤ 0.5, BH q < 0.01 over every outlet × measure on the whole season, and in every month with ≥ 5 stories the same direction with RR ≥ 1.5 or ≤ 1/1.5, at least 2 such months. Decided on the whole season only.
- Slices: `all`, each month (`2026-09`, `2026-10`, `2026-11`), and the 6 most frequent `tp` codes among big stories.
- AI findings never enter a measure, distance or verdict. No new dependencies. Turkish UI, English code. Seeds `PARAMS.random_state`.

## Review Focus

1. **An outlet with no ledes at all** (about 10 outlets): the harsher measure is absent, not 0 and not a crash; the distance uses the remaining measures if ≥ 3. Pinned in Task 4.
2. **A story where the outlet is the only comparison-group outlet** (no "others"): the stratum carries no information and must be dropped, not divide by zero. Pinned in Task 1.
3. **A slice where nobody reaches 20 stories** (a small topic in November): the page shows "Bu dilimde yeterli haber yok", not an empty chart. Pinned in Tasks 5 and 6.
4. **A ratio of 0 or infinity** (the outlet never or always does it while others vary): the interval is reported as open-ended and the distance clips it, never `NaN` or `Infinity` in JSON. Pinned in Task 1.
5. **Turkish all-capitals detection** (`İ`/`I`, `ı`): a title like "İSTANBUL ... MAHKEMESİ" is a notice; a mixed-case title with the word "Mahkemesi" is not. Pinned in Task 2.

---

### Task 1: Shared rate statistics

**Files:**
- Create: `pipeline/capraz_pipeline/stats.py`
- Modify: `pipeline/capraz_pipeline/aix.py` (`profile()` uses `bh_q`; delete the inline Benjamini–Hochberg loop)
- Test: `pipeline/tests/test_stats.py`

**Interfaces:**
- Produces: `bh_q(ps: list[float]) -> list[float]` (same order as input); `mh_rr(strata: list[tuple[int, int, int, int]]) -> tuple[float | None, float | None, float | None]` — strata are `(a, n1, b, n0)` = (outlet yes, outlet total, others yes, others total); returns `(rr, lo, hi)`, `None` where undefined; `cmh_p(strata) -> float | None`.

- [ ] **Step 1: Write the failing tests**

```python
S = [(8, 10, 10, 40), (6, 10, 5, 40)]
class StatsTest(unittest.TestCase):
    def test_mh_rr_and_interval(self):
        rr, lo, hi = mh_rr(S)
        self.assertAlmostEqual(rr, 3.7333, places=4); self.assertAlmostEqual(lo, 2.2015, places=4); self.assertAlmostEqual(hi, 6.3311, places=4)
    def test_cmh_p(self):
        self.assertAlmostEqual(cmh_p(S), 2.1324e-05, delta=1e-8)
    def test_strata_without_others_are_dropped(self):
        self.assertEqual(mh_rr(S + [(1, 1, 0, 0)]), mh_rr(S))
    def test_zero_and_infinite_ratios_stay_json_safe(self):
        rr, lo, hi = mh_rr([(0, 10, 5, 40), (0, 10, 4, 40)])
        self.assertEqual((rr, lo, hi), (0.0, None, None))
        rr, lo, hi = mh_rr([(5, 10, 0, 40)])
        self.assertEqual((rr, lo, hi), (None, None, None))
    def test_bh(self):
        self.assertEqual([round(q, 4) for q in bh_q([0.01, 0.04, 0.03, 0.005])], [0.02, 0.04, 0.04, 0.02])
```

- [ ] **Step 2: Run to see them fail** — `cd pipeline && python3 -m unittest tests.test_stats -v` → FAIL (no module)

- [ ] **Step 3: Implement.** `mh_rr`: drop strata with `n1 == 0` or `n0 == 0`; RR = Σ a·n0/N ÷ Σ b·n1/N; numerator 0 → `(0.0, None, None)`; denominator 0 → all `None`; Greenland–Robins variance Σ(n1·n0·(a+b) − a·b·N)/N² ÷ (num·den), interval exp(log RR ± 1.96·√var). `cmh_p`: χ² = (|Σa − ΣE| − 0.5)² / ΣV with E = n1·m1/N, V = n1·n0·m1·m0/(N²(N−1)), m1 = a+b, strata with N < 2 skipped; `scipy.stats.chi2.sf(x, 1)`; `None` when ΣV = 0. `bh_q`: step-up with running minimum from the largest p.

- [ ] **Step 4: Run the tests** — `python3 -m unittest tests.test_stats tests.test_aix -v` → PASS (the AI-vs-rules tests stay green after the refactor)

- [ ] **Step 5: Commit** — `feat(pipeline): shared same-story rate statistics (MH, CMH, BH)`

---

### Task 2: Who is compared, which stories count

**Files:**
- Create: `pipeline/capraz_pipeline/lens.py` (this task: groups, feeds, notices, story helpers), `data/reference/lens-groups.json`
- Modify: `pipeline/capraz_pipeline/aix.py` (`load_articles` also carries `"nu": a["nu"][k] if "nu" in a else 0`)
- Test: `pipeline/tests/test_lens.py`

**Interfaces:**
- Consumes: `aix.load_articles(data, core)`, `aix._load`.
- Produces:
  - `lens-groups.json` = `{"exclude": {"<slug>": "<Turkish reason shown on the page>", ...}}` with: haberler, sondakika, mynet ("Haber toplayıcı: başka kurumların haberlerini yeniden yayımlıyor."), aa, dha, anka ("Haber ajansı: haberleri kurumlara dağıtıyor."), bbcturkce, dwturkce ("Yabancı yayıncının Türkçe servisi."), bloomberght, agos ("Tek bir konuya odaklı yayın."), teyit ("Doğrulama platformu.").
  - `NOTICE_KEYWORDS: list[str]` (equal to `PARAMS.noticeRules.keywords` in `site/js/turkish-layer.js`); `is_notice_article(a: dict) -> bool`; `notice_events(core, arts) -> set[str]`.
  - `days_active(arts) -> dict[str, dict[str, int]]` (outlet → day → article count); `season_days(core) -> list[str]`.
  - `group(core, arts, groups) -> dict[str, dict]` → per registry outlet `{"lens": bool, "reason": str, "active_share": float}`; reasons for automatic exclusion: "Yalnızca sezonun bir kısmında derlendi." / "Kayıt defterinde genel haber kurumu olarak geçmiyor.".
  - `feed_complete(counts: dict[str, int], n_days: int) -> tuple[bool, dict]` → `(complete, {"active_share", "median", "at_max_share"})`.

- [ ] **Step 1: Write the failing tests**

```python
class GroupTest(unittest.TestCase):
    def test_keywords_match_the_browser(self):
        js = (REPO / "site/js/turkish-layer.js").read_text(encoding="utf-8")
        block = re.search(r"noticeRules: \{ url: .*?keywords: (\[[^\]]*\])", js, re.S).group(1)
        self.assertEqual(json.loads(block), NOTICE_KEYWORDS)
    def test_notice_article_needs_all_capitals(self):
        self.assertTrue(is_notice_article({"t": "İSTANBUL 3. ASLİYE HUKUK MAHKEMESİ", "nu": 0}))
        self.assertFalse(is_notice_article({"t": "Mahkemesi kararını verdi", "nu": 0}))
        self.assertTrue(is_notice_article({"t": "Haber", "nu": 1}))
    def test_feed_complete(self):
        days = {f"d{i}": 20 + i for i in range(40)}           # its maximum (59) on 1 of 40 days
        self.assertTrue(feed_complete(days, 60)[0])
        capped = {f"d{i}": 6 for i in range(60)}
        ok, st = feed_complete(capped, 60)
        self.assertFalse(ok); self.assertEqual(st["at_max_share"], 1.0)
    def test_group_excludes_listed_and_part_season(self):
        core = {"S": [{"s": "sabah", "t": "print"}, {"s": "aa", "t": "web"}, {"s": "aksam", "t": "web"}],
                "meta": {"window": {"start": "2026-09-01T00:00:00.000Z", "end": "2026-09-10T23:59:00.000Z"}}}
        arts = {f"a{i}": {"s": "sabah", "d": f"2026-09-{1 + i:02d}T10:00"} for i in range(10)}
        arts |= {f"b{i}": {"s": "aa", "d": f"2026-09-{1 + i:02d}T10:00"} for i in range(10)}
        arts |= {"c0": {"s": "aksam", "d": "2026-09-01T10:00"}}
        g = group(core, arts, {"exclude": {"aa": "Haber ajansı: haberleri kurumlara dağıtıyor."}})
        self.assertEqual({k: v["lens"] for k, v in g.items()}, {"sabah": True, "aa": False, "aksam": False})
        self.assertEqual(g["aa"]["reason"], "Haber ajansı: haberleri kurumlara dağıtıyor.")
```

- [ ] **Step 2: Run to see them fail** — `cd pipeline && python3 -m unittest tests.test_lens -v` → FAIL

- [ ] **Step 3: Implement** the data file and the functions. All-capitals uses Turkish case mapping (`store.tr_lower`, and `tr_upper` = `str.upper` after mapping `i`→`İ`, `ı`→`I`): a title is all-capitals when it equals its Turkish upper form and differs from its Turkish lower form. Days are the Istanbul dates `d[:10]`.

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Commit** — `feat(lens): comparison group, complete feeds, notice stories`

---

### Task 3: Confirmed skips

**Files:**
- Modify: `pipeline/capraz_pipeline/lens.py`
- Test: `pipeline/tests/test_lens.py`

**Interfaces:**
- Consumes: `cluster.vectors(titles) -> csr_matrix`, `cluster.minutes(stamp) -> int`, Task 2's `notice_events`, `days_active`, `group`.
- Produces: `big_stories(core, arts, group_out, notices) -> list[dict]` → `[{"event", "day", "active": [slugs], "covered": [slugs]}]`; `confirmed_skips(stories, core, arts, outlets: list[str]) -> dict[str, set[str]]` → outlet → events truly skipped (no headline of that outlet within 48 h of the event's first headline at cosine ≥ 0.33 with any of the event's headlines).

- [ ] **Step 1: Write the failing test**

```python
def test_a_matching_headline_outside_the_event_is_not_a_skip(self):
    core = {"E": [{"i": "e1", "a": ["x1", "x2"], "s": ["sabah", "sozcu"], "f": "2026-09-01T10:00"}]}
    arts = {"x1": {"s": "sabah", "t": "Bakan istifa etti", "d": "2026-09-01T10:00"},
            "x2": {"s": "sozcu", "t": "Bakan istifa etti, yerine atama", "d": "2026-09-01T10:05"},
            "y1": {"s": "karar", "t": "Bakan istifa etti ve gitti", "d": "2026-09-01T12:00"},
            "z1": {"s": "birgun", "t": "Hava durumu yağmurlu", "d": "2026-09-01T12:00"}}
    stories = [{"event": "e1", "day": "2026-09-01", "active": ["sabah", "sozcu", "karar", "birgun"], "covered": ["sabah", "sozcu"]}]
    self.assertEqual(confirmed_skips(stories, core, arts, ["karar", "birgun"]), {"karar": set(), "birgun": {"e1"}})
```

- [ ] **Step 2: Run to see it fail** — FAIL (`confirmed_skips` undefined)

- [ ] **Step 3: Implement.** Vectorise once per run over every headline in play (event headlines plus candidate outlets' headlines in the windows); compare each candidate outlet's in-window headlines with the event's headlines by dot product of the normalised rows. When fewer than 2 documents share a term (`min_df=2`), the vectoriser still fits because the event's own headlines repeat words; for an empty vocabulary, treat the skip as unconfirmed (not counted).

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Commit** — `feat(lens): big stories and text-confirmed skips`

---

### Task 4: Measures, verdicts and the lens file

**Files:**
- Modify: `pipeline/capraz_pipeline/lens.py` (add `MEASURES`, `strata`, `outlet_lens`, `compute`, `main`), `pipeline/capraz_pipeline/narratives.py` (`merge` ships `LENS` from `data/reference/lens-82.json`, like `AIX`)
- Test: `pipeline/tests/test_lens.py`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces:
  - `MEASURES = ("skip", "loaded", "harsher", "first")`.
  - `stories` passed to `strata` are `{"event", "month", "tp": [codes], "first": {slug: article id}, "active": [slugs], "skipped": {slugs}}`; `active` and `skipped` are filled only for big stories (`skipped` from `confirmed_skips`).
  - `strata(measure: str, outlet: str, stories: list[dict], arts, others: list[str]) -> list[tuple[int, int, int, int]]` — one stratum per story where the outlet is eligible: for `skip`, the outlet is active that day and `others` are only complete-feed comparison outlets active that day; for the other three, the outlet covered the story and `others` are the other comparison outlets that covered it, each with the measure's own eligibility (political headline for `loaded` and `harsher`, a lede for `harsher`, a time other than `00:00` for `first`).
  - `verdict(m: dict, months: dict[str, dict]) -> bool` — the "systematically" rule exactly as in Global Constraints.
  - `distance(measures: dict[str, dict]) -> float | None`.
  - `compute(core, arts, groups) -> dict` → `{"params": {...}, "slices": [{"k": "all", "l": "Bütün sezon"}, {"k": "2026-09", "l": "Eylül"}, …, {"k": "tp:yargi", "l": <TP name>}], "outlets": {slug: {"lens": bool, "reason": str, "feed": {...}, "slices": {k: {"measures": {m: {"n", "rr", "lo", "hi", "p", "q", "strong"}}, "distance": float | None}}, "missed": [event ids, largest first, at most 8]}}}` — `q` and `strong` only on `all`; no `NaN`/`Infinity` anywhere (`allow_nan=False` on dump).
  - CLI `python -m capraz_pipeline.lens --data <build>` writes `data/reference/lens-82.json` and prints, per lens outlet, its distance and its complete-feed numbers.

- [ ] **Step 1: Write the failing tests**

```python
def test_verdict_needs_every_condition(self):
    m = {"n": 40, "rr": 2.4, "q": 0.004}
    months = {"2026-09": {"n": 12, "rr": 2.1}, "2026-10": {"n": 15, "rr": 1.8}, "2026-11": {"n": 3, "rr": 0.5}}
    self.assertTrue(verdict(m, months))                                   # the 3-story month is ignored
    self.assertFalse(verdict({**m, "q": 0.02}, months))
    self.assertFalse(verdict({**m, "rr": 1.9}, months))
    self.assertFalse(verdict(m, {"2026-09": {"n": 12, "rr": 2.1}}))        # only one month with 5+ stories
    self.assertFalse(verdict(m, {**months, "2026-10": {"n": 15, "rr": 1.2}}))
def test_distance_clips_and_needs_three_measures(self):
    self.assertAlmostEqual(distance({"a": {"n": 30, "rr": 8.0}, "b": {"n": 30, "rr": 0.5}, "c": {"n": 30, "rr": 1.0}}), 2 ** ((2 + 1 + 0) / 3))
    self.assertIsNone(distance({"a": {"n": 30, "rr": 2.0}, "b": {"n": 30, "rr": 2.0}, "c": {"n": 10, "rr": 2.0}}))
def test_no_ledes_means_no_harsher_measure(self):
    arts = {"x": {"s": "o", "v": 30, "lv": None, "p": 1, "d": "2026-09-01T10:00"}}
    self.assertEqual(strata("harsher", "o", [{"event": "e1", "first": {"o": "x", "q": "y"}}], arts | {"y": {"s": "q", "v": 0, "lv": 0, "p": 1, "d": "2026-09-01T10:00"}}, ["q"]), [])
def test_eligibility_political_and_timed(self):
    arts = {"x": {"s": "o", "v": 30, "lv": 0, "p": 0, "d": "2026-09-01T00:00"}, "y": {"s": "q", "v": 30, "lv": 0, "p": 1, "d": "2026-09-01T10:00"}}
    st = [{"event": "e1", "first": {"o": "x", "q": "y"}}]
    self.assertEqual(strata("loaded", "o", st, arts, ["q"]), [])          # the outlet's headline is not political
    self.assertEqual(strata("first", "o", st, arts, ["q"]), [])           # its time is a bare date
def test_compute_writes_json_safe_output(self):
    json.dumps(compute(*small_fixture()), allow_nan=False)   # small_fixture: 2 lens outlets, 25 stories, one outlet never loaded
```

- [ ] **Step 2: Run to see them fail** — FAIL

- [ ] **Step 3: Implement.** For each slice, the stories are the non-notice events whose first headline falls in that month or whose `tp` contains the topic; for each lens outlet and measure, build strata against the other comparison-group outlets, keep the measure only with ≥ 20 stories, run `mh_rr` and `cmh_p`; then `bh_q` over every (outlet, measure) on `all`, then `verdict` with the month slices. `missed` = the outlet's confirmed skips ordered by the event's outlet count. Add the `LENS` lines to `narratives.merge` next to `AIX`.

- [ ] **Step 4: Run the tests** — PASS; then `python3 -m capraz_pipeline.lens --data <build dir with core.bin and a-*.bin>` on the real data prints a distance for most lens outlets and lists every outlet's feed numbers.

- [ ] **Step 5: Commit** — `feat(lens): same-story measures, verdicts, distance; core key LENS` (code, tests, `data/reference/lens-82.json`)

---

### Task 5: Wording helpers

**Files:**
- Modify: `site/js/v7/logic.js` (add and export `LENS_MEASURES`, `lensSentence`, `lensDistanceText`)
- Test: `site/tests/logic.test.cjs`

**Interfaces:**
- Consumes: the `LENS` shape of Task 4.
- Produces:
  - `LENS_MEASURES = [["skip", "büyük olayları atlıyor", "büyük olayı atladı"], ["loaded", "yüklü başlık atıyor", "yüklü başlık"], ["harsher", "başlığı haberinden sert yazıyor", "haberinden sert başlık"], ["first", "olayı ilk veriyor", "ilk veriş"]]` — key, verb phrase for sentences, noun for chart labels.
  - `lensSentence(name: string, key: string, m: {n, rr, lo, hi, strong}) -> string`; `lensDistanceText(d: number | null) -> string`.

- [ ] **Step 1: Write the failing tests**

```js
test("lensSentence: strong wording only when strong", () => {
  assert.equal(L.lensSentence("Sabah", "loaded", { n: 40, rr: 2.4, lo: 1.8, hi: 3.1, strong: true }),
    "Sabah aynı haberlerde sistematik olarak daha sık yüklü başlık atıyor (2,4 kat; %95 aralık 1,8–3,1; 40 haber).");
  assert.equal(L.lensSentence("Sabah", "first", { n: 30, rr: 0.6, lo: 0.4, hi: 0.9, strong: false }),
    "Sabah, aynı haberlerde “ilk veriş” bakımından diğer kurumların 0,6 katı (%95 aralık 0,4–0,9; 30 haber).");
  assert.equal(L.lensSentence("Sabah", "loaded", { n: 25, rr: 0, lo: null, hi: null, strong: false }),
    "Sabah · bu 25 haberin hiçbirinde “yüklü başlık” yok; diğer kurumlarda var.");
  assert.equal(L.lensSentence("Sabah", "loaded", { n: 25, rr: null, lo: null, hi: null, strong: false }),
    "Sabah · bu 25 haberde “yüklü başlık” yalnızca bu kurumda var; diğer kurumlarda yok.");
});
test("lensDistanceText", () => {
  assert.equal(L.lensDistanceText(1.6), "Ortalamada diğer kurumlardan 1,6 kat farklı davranıyor.");
  assert.equal(L.lensDistanceText(null), "Bu dilimde yeterli haber yok.");
});
```

- [ ] **Step 2: Run to see them fail** — `node site/tests/logic.test.cjs` → 2 failures

- [ ] **Step 3: Implement.** Numbers with one decimal and a Turkish comma (the site's `dec`); when `strong` and `rr < 1`, "daha seyrek" replaces "daha sık"; behaviour words only; never a suffix attached to the outlet name (Turkish vowel harmony cannot be generated reliably for every name).

- [ ] **Step 4: Run the tests** — PASS

- [ ] **Step 5: Commit** — `feat(site): lens wording helpers`

---

### Task 6: The lens on the outlet page and the Kurumlar ranking

**Files:**
- Create: `site/js/v7/lens.js`
- Modify: `pipeline/capraz_pipeline/site.py` (`V7_ORDER` gains `"lens"` before `"desk"`), `site/js/app.js` (`pgSource` inserts `lensSection(k)` after the page head; `pgSources` list view inserts `lensRanking()`), `site/styles.css`, `site/js/v7/yontem.js` (method paragraph), `site/tests/smoke.cjs`
- Test: `site/tests/smoke.cjs`

**Interfaces:**
- Consumes: `D.LENS`, `lensSentence`, `lensDistanceText`, `LENS_MEASURES`, `d3Load`/`aiMount` patterns from `aiimza.js`, `aiCard`, `yzBadge`.
- Produces: `lensSection(slug: string) -> string` (empty when `D.LENS` is missing); `lensRanking() -> string`.

- [ ] **Step 1: Write the failing smoke checks** (in `smoke.cjs`, for `#/kurum?s=takvim` and `#/kurum?s=aa`):
  - `#/kurum?s=takvim` has `section.lens` with `h2` "Bu kaynağı tek başına okusaydınız", a slice switch with the button "Bütün sezon", one `.lens-row` per measure shown, and a `.lens-ai` box carrying exactly one "AI imzalı" badge;
  - `#/kurum?s=aa` has no `section.lens` but a `.lens-none` sentence equal to the reason in `lens-groups.json`;
  - clicking the "Eylül" slice changes the text of `.lens-dist`.

- [ ] **Step 2: Run to see them fail** — `node site/tests/smoke.cjs public <out> "#/kurum?s=takvim" "#/kurum?s=aa"` → FAIL

- [ ] **Step 3: Implement.** The section, top to bottom:
  - the distance sentence and a one-row D3 strip of all lens outlets by distance, this outlet marked;
  - "Kaçırdığınız büyük olaylar": linked event titles from `missed`, or "bu kurumun derlemesi eksik olabildiği için atlanan olaylar ölçülmedi" when the feed is not complete;
  - "Aynı haberleri nasıl anlattı": one `.lens-row` per measure, a dot-and-interval on a log scale centred on 1 (open-ended intervals drawn to the axis edge), and the `lensSentence` text under it;
  - the slice switch;
  - "Ek bulgular" (`.lens-ai`): the outlet's AI citation rates from `AIX.profile`, its three most-quoted concepts from live findings, its most frequent narrative blame codes labelled hand- or AI-coded, with `yzBadge()`.

  A slice with no measure at 20+ stories shows "Bu dilimde yeterli haber yok." The Kurumlar list gets `lensRanking()`: lens outlets sorted by `all` distance, a dot each, linked. The Yöntem paragraph states the four measures, the same-story comparison, the comparison group and the "systematically" rule.

- [ ] **Step 4: Run the checks** — smoke on both routes → `smoke ok`; `node site/tests/logic.test.cjs` → all pass.

- [ ] **Step 5: Commit** — `feat(site): single-source lens on outlet pages and the Kurumlar ranking`

---

### Task 7: Rebuild, verify, publish

**Files:**
- Modify: `public/data/core.bin`, `public/index.html` (generated), `openspec/changes/add-single-source-lens/tasks.md` (tick)

- [ ] **Step 1: Pack** — run Task 4's CLI on the build folder, then `python -m biasguard.news pack --build <dir> --run runs/bg82 --media-run runs/bgm82`; confirm the only new core key is `LENS`.
- [ ] **Step 2: Assemble** — `cd pipeline && python3 -m capraz_pipeline site --site ../public`.
- [ ] **Step 3: Verify** — every Python suite (`pipeline/tests`, `biasguard`, `validation/tests`, `tests_repo`), `node site/tests/logic.test.cjs`, the full `site/tests/smoke.cjs` → all green; `openspec validate add-single-source-lens --strict` → valid.
- [ ] **Step 4: Commit and push** — `data: single-source lens in core.bin`.
- [ ] **Step 5: Publish** the artifact (only `index.html` and `data/core.bin.txt` change) and update the knowledge graph (`graphify` incremental update with the changed files).
