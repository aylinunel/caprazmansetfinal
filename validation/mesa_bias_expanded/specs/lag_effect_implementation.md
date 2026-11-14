# Lag Effect — illustrative implementation

## Process and measure

This module models spaced practice, not a learner classification. Its chronological task contexts are explicit `study` or `test` events with a nonnegative day and a positive `retention_horizon_days`. The complete learner task state carries `memory_strength`, `last_study_day`, and `study_count` between events.

For a study after a previous study, let `g` be the gap in days and `H` the supplied horizon. Stored strength first decays to `m_d = m * exp(-g/H)`. The fixed-gain, strength-zero reference uses `q = 0.20`. When and only when `0 < g <= H`, the illustrative intervention uses `q = 0.20 * (1 + strength * 2 * g/H)`. The resulting stored strength is `m' = 1 - (1 - m_d) * exp(-q)`. A first study or a gap outside the suitable positive interval uses the same fixed gain at every strength. A test event reports `m * exp(-(day-last_study_day)/H)` and does not modify study history.

The primary metric is the unitless modeled retention-strength score, bounded by zero and one. `active` is true only for a study with a suitable positive prior interval and positive intervention strength. The coefficient and equations are transparent illustrative assumptions; intervention strength is not a calibrated effect estimate.

## Necessary condition and scenarios

A lag effect in this toy process requires at least two distinct study events and a strictly positive gap no greater than the supplied retention horizon. The positive scenario studies on day 0 and day 5 with horizon 10, making the later session's encoding gain increase over the fixed-gain reference. The boundary scenario has two study events on day 0; the zero-day gap removes the necessary spaced-interval condition, so its final metric equals the reference. Both scenarios are chronological, and the runner compares final metrics after the supplied events only.

The required context inputs (`action`, `day`, and `retention_horizon_days`) exist in every phase. Event/state validation remains inside `evaluate`: a test requires prior study history, and an invalid or impossible horizon/time/state is rejected rather than treated as zero evidence.

## Assumptions and limitations

The model is deterministic and omits item difficulty, retrieval success, encoding variability, interference, schedule design, individual differences, and uncertain retention horizons. Its single exponential time constant and coefficients are not claims about empirical effect size. Real spacing benefits depend on the later retention horizon; longer intervals are not universally better. This implementation is hypothetical and is not empirical validation, an individual prediction, diagnosis, or a natural-language detector. Passing executable checks establishes only that the plugin follows its software contract.
