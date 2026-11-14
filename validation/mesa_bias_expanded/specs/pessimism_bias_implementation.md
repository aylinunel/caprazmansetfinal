# Pessimism bias implementation note

## Illustrative process

This synthetic, single-step task models a hypothetical adverse-outcome forecast from three explicit inputs: a base adverse rate and favorable/adverse evidence-support scores, each in `[0, 1]`. The strength-zero reference policy uses symmetric evidence updates in log odds:

`reference_log_odds = logit(base_adverse_rate) + 1.20 * (adverse_evidence - favorable_evidence)`

The illustrative bias adds an asymmetric upward term only when favorable support exists and adverse evidence is below the assumed corroboration threshold of `0.60`:

`bias_log_odds = strength * 1.40 * favorable_evidence * (1 - adverse_evidence / 0.60)`

Otherwise the bias term is zero. The output metric is the logistic transform of reference log odds plus this bias term: the task-specific probability forecast of an adverse outcome. The coefficients and threshold are hypothetical choices, not estimated effect sizes. Strength is an intervention setting, not calibrated confidence or population prevalence.

## Baseline and necessary condition

At strength zero, the forecast is the stated evidence-adjusted reference forecast, not a claim of perfect rationality. The mechanism requires both favorable evidence to be discountable and a lack of adequate adverse corroboration. Adverse evidence at or above `0.60` removes that necessary condition and protects a potentially justified adverse forecast from the modeled distortion.

## Scenarios

- **Positive:** base adverse rate `0.35`, favorable evidence `0.80`, adverse evidence `0.15`. At strength `0.8`, the adverse forecast increases relative to the same-task strength-zero reference.
- **Boundary:** same base rate and favorable support, but adverse support is `0.80`. This supplies adequate adverse corroboration, so the extra term is zero and the forecast equals the reference.

Both scenarios are one-step tasks; no temporal inference or hidden state is claimed.

## Scope and limitations

This is a compact process illustration, not a classifier, diagnosis, or model of all pessimistic judgment. Support scores are structured hypothetical inputs, not inferred from language; their evidence quality, dependence, and calibration are unmodeled. The threshold is an explicit simplified boundary, while real evidentiary adequacy depends on domain and context. A more adverse forecast can be justified; only the stipulated insufficient-support case is modeled here. Software contract checks do not establish empirical validity, detection accuracy, or any population-level claim.
