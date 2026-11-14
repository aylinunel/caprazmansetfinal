# Outcome bias: illustrative implementation

## Process and metric

For each recorded decision, `evidence_quality` is a supplied 0–1 reference appraisal of the decision using information available when it was made. If the realized result is observed, the hypothetical retrospective appraisal is

`appraisal = evidence_quality + strength × (outcome_quality − evidence_quality)`.

If the result is not observed, appraisal stays at `evidence_quality`. The primary metric is retrospective decision-quality appraisal in normalized 0–1 points. The output state appends each case's evidence score, outcome-observation status, outcome score (or null), and appraisal to an evaluation history.

## Baseline and necessary condition

Strength zero is the explicit evidence-based reference policy: it reports the recorded `evidence_quality` regardless of the result. Strength is an uncalibrated intervention weight, not a probability, prevalence estimate, or effect size. Outcome bias in this model requires an observed realized result; if `outcome_observed` is false, `outcome_quality` must be null and no result-based appraisal shift occurs.

## Scenarios

The positive scenario supplies two chronological records in which the evidence-based quality is high but the observed results are poor. At strength 0.8, the final appraisal is lower than the strength-zero reference. The boundary scenario withholds the result (`outcome_observed: false`, `outcome_quality: null`) and therefore matches the reference. The scenarios are explicit synthetic task inputs, not observations of people.

## Scope and limitations

This process illustrates appraisal of decision quality, not hindsight bias about whether a result was predictable beforehand. It does not infer scores, motives, or hidden mental states, and it is not an NLP detector or diagnosis. Good results can follow poor reasoning and poor results can follow sound reasoning. The linear interpolation, scores, and strength are simplifying user-settable assumptions; there is no claim of empirical validity or calibrated effect size, and passing software checks establishes only implementation-contract behavior.
