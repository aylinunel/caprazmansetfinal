# Negativity bias: illustrative implementation

**Status:** Explicitly hypothetical and not empirically validated. This is a structured process model, not an NLP detector, fitted psychological model, population estimate, or diagnosis.

## Process and task

The task is a narrow evidence-prioritization score. Each supplied evidence record has a topic, valence (`negative` or `positive`), severity, and relevance, with severity and relevance normalized to `[0, 1]`. At strength zero, the reference metric is

`reference = Σ(negative severity × relevance) − Σ(positive severity × relevance)`.

Evidence contributes according to its severity and relevance in the baseline; raw item count alone does not establish comparable weight. The model groups records by exact `(topic, severity, relevance)` and pairs positive and negative records one-to-one. At intervention strength `s`, it adds

`0.5 × s × Σ(matched negative severity × relevance)`

to the reference score. The coefficient `0.5` is an illustrative assumption, not an effect size. The reported metric is the resulting net risk-priority score in weighted risk-priority points; it may be negative when the weighted positive information outweighs negative information. The state retains the current and reference scores, modeled increment, count of comparable pairs, and number of evaluated calls.

## Necessary conditions and scenarios

The extra weighting requires opposing-valence evidence about the same supplied topic with exactly equal supplied severity and relevance, and positive severity×relevance. With no comparable positive/negative pair, the modeled increment is zero and the primary metric equals the strength-zero reference. The `positive` scenario uses one exactly matched pair and has a metric increase at strength `0.8`; the `boundary` scenario removes comparability through unmatched, different-topic, or different-severity evidence and must match the reference metric.

## Assumptions and limitations

The structured labels and scales are hypothetical input facts; the mechanism does not infer them. Exact matching is intentionally conservative and will miss comparable items encoded differently. Severity and relevance can justify unequal weights, while the baseline reflects those dimensions directly. A greater score is not proof of bad judgment, misleading presentation, or harmful bias; emphasizing severe negative evidence may be beneficial. This single-step scoring proxy does not model actual attention, memory, audience response, evidence quality, truth, or intent. Software tests check the specified illustrative arithmetic only and are not empirical validation.
