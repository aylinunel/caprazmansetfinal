# Spotlight effect — illustrative implementation

## Process and task measure

This plugin models overestimation of **others' attention to an externally visible focal event**, not visibility of private thoughts or feelings (the latter belongs to the illusion-of-transparency boundary). Inputs are structured hypothetical prominence ratings `focal_prominence` and `other_prominence`, plus explicit `self_salience`; each is a finite number in `[0, 1]`, and the two prominence ratings cannot both be zero.

The strength-zero reference allocates attention in proportion to visible prominence:

`reference_share = focal_prominence / (focal_prominence + other_prominence)`

At intervention strength `s`, the focal event is reweighted by explicit self-salience `q`:

`estimated_share = focal_prominence * (1 + 2.5*s*q) / (focal_prominence * (1 + 2.5*s*q) + other_prominence)`

The metric is `estimated_share - reference_share`, in audience-attention share points. This is a task-specific simulated overestimate, not an observed belief, a measured audience response, or a diagnostic score. The `2.5` gain is a transparent illustrative assumption, not a published effect size. State stores the last reference share, estimated share, and their difference; it does not infer history or private states.

## Scenarios and boundary

- **Positive:** focal visibility is 0.20, competing visibility 0.80, and self-salience 0.90. At strength 0.8, reweighting raises estimated focal attention above the strength-zero reference.
- **Boundary:** the same external prominence evidence is retained, but self-salience is zero. The necessary self-focused reweighting condition is absent, so strength 0.8 equals the reference metric.

## Assumptions and limitations

The two-option normalized allocation is a simplified illustrative process. It ignores audience heterogeneity, context, attention costs, and other causes of perceived attention. Prominence and self-salience must be supplied as structured hypothetical facts; the plugin is not an NLP/image detector and does not infer motives or internal states. Strength is an uncalibrated intervention parameter. Passing software checks is not empirical validation, and no prevalence, causal, or population-level claim is made.
