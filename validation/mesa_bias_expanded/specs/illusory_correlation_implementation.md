# Illusory Correlation — implementation note

## Process and observable

This plugin is a deliberately narrow, hypothetical **memory-weighted association** process over chronological pairs of explicitly coded binary observations `(A, B)`. It maintains two 2×2 contingency tables across rounds: `observed_cells` counts each pair once, while `memory_cells` records the perceptual table. At strength `s`, each observed pair increments its cell in both tables by 1. If and only if the current pair is the first-ever `(1,1)` in the entire carried history, its memory-table cell receives an additional `s`. Thus the distinctive first joint occurrence is selectively overrepresented; no other cell receives an extra count.

For either table, the primary metric is signed phi:

`phi = (n11*n00 - n10*n01) / sqrt((n10+n11)(n00+n01)(n01+n11)(n00+n10))`.

It is dimensionless and lies in `[-1, 1]` when both variables vary. This is an association observable, not a causal estimate or direct measurement of a person's belief. The mechanism is active when memory-weighted phi differs from ordinary observed-data phi on that step. State carries both tables and the evaluated-step count; chronological batches are added in order.

## Reference and scenarios

At strength zero, each pair contributes exactly one count to each table and reported phi is ordinary phi of the supplied observations. This is a transparent task-specific reference, not a claim of perfect reasoning. The positive scenario supplies a distinctive `(1,1)` event followed by a more negatively associated set of observations; its extra memory weight makes final phi less negative (an increase). The boundary scenario contains no `(1,1)` event anywhere in its chronological history. Removing that necessary trigger makes the memory table equal the observed table, so the intervention and strength-zero metrics are equal.

The implementation explicitly represents paired co-occurrence only. It does not infer categories, event rarity from a population, sample representativeness, or causality. Missing or degenerate evidence is rejected rather than assigned a zero metric. Strength is an uncalibrated illustrative intervention coefficient, not a fitted effect size, prevalence, confidence, or empirical estimate.

## Assumptions and limitations

The binary codes and observation order are externally supplied hypothetical task data. Extra encoding of a first joint event is one conceivable salience process, not an established general account of illusory correlation. A memorable coincidence can be benign, adaptive, or accurate; salience alone does not establish an error. In particular, this model must not be confused with treating a genuine correlation as proof of causation: it computes an association statistic and makes no causal claim. Tests establish software behavior only, not empirical validity, diagnostic utility, or population-level claims.
