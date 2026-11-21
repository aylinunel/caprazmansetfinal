# Single-source lens ("Tek kaynak okuru") — design

Status: draft for owner approval (builder check done 2026-11-21; owner answered the two open questions). Decisions so far: `docs/superpowers/specs/2026-11-20-single-source-lens-decisions.md`.

## Intent

Show what a single news source does to a reader's picture of the world. A reader of only one outlet sees only that
outlet's choices: which stories exist, which disappear, how charged the words are, how much harsher the headline is than
the story it sits on. Set against every other outlet's version of the same stories, those choices become visible;
where the same choice repeats across many stories, it is a pattern worth naming.

## Goals

1. For every outlet with enough data: how far its version of the news sits from the full picture, measured only on the
   same stories (so a story's own drama is never counted as the outlet's bias).
2. Which big stories its reader never saw.
3. Each difference as a rate ratio with a 95% interval; a pattern worded as "systematically" only when it is
   unmistakable (rule below); otherwise the number and its strength, and the reader judges.
4. AI findings about the outlet beside the score, labelled AI imzalı, never inside it.
5. Slices: whole season, each month, the main topics.

## Non-goals (this version)

- Party tone in the score (it needs the party-name matcher, which lives in the browser; the Partiler page keeps it).
- Blame in the score (mostly AI-coded narratives; it is shown in the AI layer).
- Free date-range filtering (approach C, later if needed).
- Re-telling the event page ("one story, whole country"): a separate small change, later.

## Anti-goals (a failure even if it works)

- A claim of motive. Wording describes behaviour, never intent ("systematically", never "in order to").
- A difference that is really the story mix (any comparison not made on the same stories).
- A strong word on thin data (fewer than 20 stories, or only one month).
- A score that silently includes unverified AI output.

## Approaches (owner chose A)

| | How | Trade-off |
|---|---|---|
| **A. Precomputed lens (chosen)** | A new build step computes every number and verdict; the site draws them | Strictest statistics, tested in Python, small download, matches the roadmap; slices fixed at build time |
| B. In the browser | The page computes on the fly from all headlines | Free exploration; slow tests on phones, weaker verdicts, against the roadmap |
| C. Hybrid | Build ships per-outlet-per-story rows; browser sums them | Free filters plus rigorous headline verdicts; two places to keep in sync, filtered views without verdicts |

## Who is compared, and who gets a lens (owner decision)

The comparison group and the lens are for **active general-news outlets only**: registry type print, tv, web or online,
active on at least 50% of the season's days (`PARAMS.active_day_share`), and not on the exclusion list
`data/reference/lens-groups.json`, which names each left-out outlet and why: aggregators (haberler, sondakika, mynet),
wire agencies (aa, dha, anka), foreign broadcasters' Turkish services (bbcturkce, dwturkce), single-topic outlets
(bloomberght, agos), the fact-checker (teyit). Outlets outside the registry, and part-season outlets, are left out
automatically. A left-out outlet's page says why it has no lens. The list is data, so the owner can change it.

## Stories that count (builder check; my calls)

- Official-notice events are left out, as on every Örüntüler page. The lens uses the same rule as the browser: the URL
  notice rules already shared with Python (`capraz_pipeline/urlpack.NOTICE_URL`, kept identical by a test) and the same
  event share threshold; a parity test compares the Python notice-event set with the browser's on the real data.
- Loaded headline and headline-vs-lede use **political headlines only** (`p`), as every existing figure on the site does,
  so the outlet page never shows two different loaded figures. Skipped and first-to-report use all non-notice stories.
- First-to-report leaves out headlines whose time is exactly 00:00 (date-only timestamps).

## Skipped stories (owner decision, with my calls on the details)

A skip is counted only for outlets whose collection looks **complete**, and only after a text check:
- complete feed (my thresholds): active on ≥ 50% of days, median ≥ 20 collected headlines per active day, and fewer
  than 10% of active days at the outlet's own maximum daily count (a capped feed hits its ceiling repeatedly); the lens
  report lists every outlet's numbers so the rule can be checked;
- confirmation (my call, for accuracy): before a story counts as skipped, the outlet's unclustered and other-event
  headlines within the story's 48-hour window are compared with the story's headlines (TF-IDF cosine ≥ 0.33, the
  clustering threshold); a close match means the outlet did cover it, and it is not a skip;
- outlets without a complete feed get no skip measure; their page says "bu kurumun derlemesi eksik olabildiği için
  atlanan olaylar ölçülmedi".

## Measures (proven, rule-based; the outlet's first headline per story)

All four are yes/no per outlet per story, so each comparison is a **rate ratio on the same stories**:
the Mantel–Haenszel risk ratio stratified by story (the outlet against all other outlets on that story), with a
Greenland–Robins 95% interval and the Cochran–Mantel–Haenszel test.

| Measure | A "yes" for the outlet on a story | Stories counted |
|---|---|---|
| **Skipped a big story** | The outlet published nothing in the story although it was active that day (≥ 1 article) | Stories covered by ≥ 50% of outlets active on the story's first day |
| **Loaded headline** | Headline score ≥ 25 (the site's existing "loaded" threshold, `shared/analysis/rules.cjs`) | Stories the outlet covered |
| **Headline harsher than its own story** | Headline score − lede score ≥ 15 (existing threshold, `analyze.headline_lede_gap`) | Stories the outlet covered, with a lede |
| **First to report** | The outlet's first headline is within 60 minutes of the story's first headline | Stories the outlet covered |

For "skipped", the comparison group is the other outlets active that day (covered or not); for the other three, the other
outlets that covered the story.

**Distance from the full picture** (one number per outlet and slice): the mean over measures of |log2 RR|, each RR clipped
to [1/4, 4], shown as "on average N times as often or as rarely as the other outlets on the same stories" (N = 2^mean).
A measure with fewer than 20 stories is left out (about 10 outlets have almost no ledes, so they lack headline-vs-lede); an outlet needs at least 3 measures to get a distance.

## The "systematically" rule (owner-approved thresholds)

A finding (outlet × measure, whole season) is worded as a pattern ("X sistematik olarak daha sık …") only when all hold:

1. at least 20 stories;
2. RR ≥ 2 or ≤ 0.5;
3. q < 0.01, Benjamini–Hochberg over every outlet × measure tested;
4. it holds in every month with at least 5 stories (same side of 1 and RR ≥ 1.5 or ≤ 1/1.5), with at least 2 such months.

Otherwise the sentence gives the number and interval ("aynı haberlerde diğer kurumlardan 1,6 kat daha sık, %95 aralık
1,2–2,1"). Month and topic slices show numbers only; the strong wording is decided on the whole season.

## AI layer (AI imzalı, outside the score)

From data already in core: the outlet's AI citation rates (`AIX.profile`), the concepts whose findings quote this
outlet most (BG / live BGM evidence), and its most frequent narrative blame codes (labelled hand- or AI-coded). Shown as
"Ek bulgular", with the AI imzalı badge and the review status from the AI denetim masası.

## Where it lives

- **Build:** `pipeline/capraz_pipeline/lens.py` — `compute(core, arts) -> dict`, CLI `python -m capraz_pipeline.lens
  --data <build>` writes `data/reference/lens-82.json`; `narratives.merge` ships it as core key `LENS`. Pure statistics
  (`mh_rr`, `cmh_p`, and Benjamini–Hochberg pulled out of `aix.profile` into one shared function) unit-tested against hand-computed values.
- **Site:** a new section at the top of each outlet page (Kurumlar › outlet): "Bu kaynağı tek başına okusaydınız"
  - a strip of all outlets by distance, this one marked (D3);
  - "Kaçırdığınız büyük olaylar": its largest skipped stories, linked;
  - "Aynı haberleri nasıl anlattı": one dot-and-interval row per measure on a log scale around 1;
  - the pattern sentences; a slice switch (Tümü · Eylül · Ekim · Kasım · main topics);
  - the AI layer.
  On the Kurumlar list: one ranking chart, "Bütün resimden uzaklık". Pure wording helpers in `site/js/v7/logic.js`
  (tested), drawing in `site/js/v7/lens.js`.

## Constraints

Static site, data packs only; no new dependencies (numpy, scipy present); Turkish UI, English code; brand tokens; every
number from data; the method written out on Yöntem.

## Left to the builder

Chart layout details, the exact slice list (main topics = the 6 most frequent `tp` codes among big stories), the
outlet-page placement order below the new section, caching.
