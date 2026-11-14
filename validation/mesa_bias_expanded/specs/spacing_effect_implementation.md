# Spacing Effect — illustrative implementation

## Process and metric

This module models one explicitly supplied study item at a time. Every chronological context provides an `item_id`, an `event` (`study` or `probe`), and a nondecreasing `elapsed_days`. Per-item state retains the complete list of study days and a spacing-stability accumulator. On a subsequent study, a positive interval \(g\) adds

\[
\Delta S = s\,0.8\,\frac{g}{g+1},
\]

where \(s\in[0,1]\) is the generic, uncalibrated intervention strength and the day scale and coefficient are illustrative assumptions. Same-day repetition has \(g=0\) and adds no spacing stability. For each event, with \(n\) studies, age \(a\) in days since the latest study, and accumulated stability \(S\), the normalized retrieval score is

\[
R = (1-e^{-0.7n})e^{-0.25a/(1+S)}.
\]

The primary metric is a hypothetical unitless retrieval score in [0, 1], not a calibrated probability. At strength zero, the same exposure-count and recency policy is used with no spacing-derived stability; this is the explicit comparison reference, not a claim of perfect rationality. The distinct-day interval is necessary for the modeled spacing process to activate.

## Scenarios

- **Positive:** the same item is studied on days 0, 2, and 5 and probed on day 9. Later distinct-day repetitions accumulate stability, so strength .8 is expected to raise the final score relative to strength zero.
- **Boundary:** the item is studied twice on day 0 and probed that day. Repeated exposure remains, but the necessary distinct-day spacing condition is removed; spacing stability remains zero and the final score is equal to the reference.

## Assumptions and limitations

The exponential encoding/forgetting form, coefficients, and day scale are hypothetical user-settable choices, not published effect sizes. This compact process omits learner and item differences, study quality, interference, retrieval practice, and other study conditions. It distinguishes distributed from same-day massed practice only; it does not compare different lags among spaced schedules. Strength is an intervention control, not prevalence or calibrated confidence. This is a synthetic task model, not empirical validation, a classifier, or a diagnosis; positive results must not be generalized to people without evidence.
