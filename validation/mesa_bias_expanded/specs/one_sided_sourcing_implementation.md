# One-sided sourcing: implementation note

**Status:** hypothetical, synthetic-only illustration; not empirically validated and not a detector.

## Process and metric

The module models an editor choosing two source/claim slots from an explicitly supplied, full-story inventory. Only claims explicitly marked relevant are eligible. Let `f1` and `f2` be the highest- and second-highest-quality focus-side claims, and `c1` the highest-quality relevant counter-view claim. Quality is supplied on `[0,1]`; it is not inferred from prose. When both viewpoints are available, the editor first compares balanced allocation `(f1, c1)` with a single-side allocation `(f1, f2)`. The latter replaces the counter-view only if

`quality(f2) - quality(c1) > 2.0 * (1 - strength)`.

The coefficient `2.0` is an illustrative viewpoint-diversity utility, not an estimated effect size. On the bounded quality scale it makes strength zero exactly the stated reference policy: one highest-quality relevant claim from each side. At higher strength the modeled coverage safeguard relaxes; if the second focus-side claim's quality advantage clears the threshold, both slots go to that side. When no relevant counter-view exists, the model selects up to two highest-quality eligible claims and cannot report one-sided sourcing.

The primary metric is a per-story binary indicator, `1` only when a relevant non-focus view exists in the reviewed inventory but none is selected; otherwise `0`. `active` is true only when the selected source slots differ from the strength-zero reference. The returned state records selected source IDs, represented sides, filled slots, and the metric.

## Conditions and scenarios

The necessary conditions are an explicitly confirmed full-story review, at least one relevant focus-side claim, a relevant counter-view claim, and an allocation that selects no counter-view evidence. The positive example has two high-quality focus-side sources and a lower-quality but relevant counter-view; at strength `.8`, the second focus source displaces the counter-view. The boundary example contains a counter-side claim explicitly marked irrelevant, so the necessary relevant-counter-view condition is absent and the primary metric remains equal to the reference (zero).

The caller must provide the complete structured source inventory and annotations. A short RSS excerpt cannot establish that the full story omits a counter-view, and the module rejects inputs that do not explicitly declare full-story review. Benign explanations for an uneven source allocation include editorial scope, space constraints, verification quality, and time limits. The simplified two-slot process, quality scale, and coefficient are assumptions for illustrative simulation only; no claims about real journalists, prevalence, harm, or detection accuracy follow from it.