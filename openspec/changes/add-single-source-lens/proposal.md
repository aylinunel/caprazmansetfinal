## Why

A reader of a single news outlet sees only that outlet's choices: which stories exist, how charged the words are, how much
harsher the headline is than its own story. Çapraz Manşet compares outlets today with season-wide averages, which mix an
outlet's style with the stories it happens to cover. The owner wants each outlet's picture set against every other outlet's
version of the same stories, with a pattern named only when it is unmistakable.

## What Changes

- A build step computes, per general-news outlet, same-story rate ratios with 95% intervals on four proven measures
  (skipped big stories, loaded headline, headline harsher than its lede, first to report), a "distance from the full
  picture", and the "systematically" verdict, for the whole season, each month and the six main topics.
- Each outlet page gets a "Bu kaynağı tek başına okusaydınız" section; the Kurumlar list gets a distance ranking.
- AI findings about the outlet appear beside the measures as "Ek bulgular", labelled AI imzalı, never inside the score.
- Skips are counted only for outlets with a complete-looking feed and only after a 48-hour text check.
- Benjamini–Hochberg is shared between the existing AI-vs-rules analysis and the lens.

## Capabilities

### New Capabilities
- `single-source-lens`: how far one outlet's version of the news sits from every other outlet's version of the same stories.

### Modified Capabilities
<!-- none: no existing OpenSpec capability -->

## Impact

- New: `pipeline/capraz_pipeline/stats.py`, `pipeline/capraz_pipeline/lens.py`, `data/reference/lens-groups.json`,
  `data/reference/lens-82.json`, `site/js/v7/lens.js`; core key `LENS`.
- Changed: `aix.py` (shared BH, article loader carries `nu`), `narratives.merge`, `site/js/v7/logic.js`, `site.py`
  build order, outlet and Kurumlar pages, Yöntem.
- No new dependencies (numpy, scipy, scikit-learn already used).
- Design: `docs/superpowers/specs/2026-11-21-single-source-lens-design.md`.
- Plan: `docs/superpowers/plans/2026-11-21-single-source-lens.md`.
