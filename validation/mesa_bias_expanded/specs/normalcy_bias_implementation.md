# Normalcy Bias — illustrative implementation

## Process

This plugin models a narrow warning-response task, not a person or a detector. Starting from a supplied disruption prior, it carries two log-odds through chronological phases. For a credible warning with likelihood ratio `LR`, the full-evidence reference updates objective log-odds by `ln(LR)`. The intervention updates perceived log-odds by `(1 - 0.8s) ln(LR)`, where `s` is the uncalibrated strength setting in `[0,1]`. An explicitly non-credible alert is not evidence in either policy. Each phase compares perceived probability times disruption loss with precaution cost; preparation, if selected, persists and costs once. If not prepared, that phase accrues objective probability times disruption loss. The primary metric is cumulative expected task loss in hypothetical loss units.

Strength zero is the explicit reference: full incorporation of supplied credible warning evidence, with the same threshold decision, persistence, and task-loss accounting. The 0.8 attenuation coefficient and all scenario values are user-settable illustrative assumptions, not measured effects or calibrated confidence.

## Necessary conditions and scenarios

The modeled bias requires credible disruption-warning evidence with likelihood ratio greater than one. The positive scenario supplies two chronological credible warnings; the reduced perceived evidence can delay preparation and increase final task loss relative to strength zero. The boundary scenario includes alerts with likelihood ratio above one but explicitly marks them non-credible. Since the qualifying credible-warning condition is absent, both policies ignore those alerts and produce equal outcomes.

Every phase requires a valid base disruption probability, boolean credibility flag, finite likelihood ratio of at least one, nonnegative disruption loss, and nonnegative precaution cost. The per-phase inputs are validated during evaluation; `base_disruption_probability` is the only runner-level `required_inputs` field because it is common to all phases.

## Limitations

This is a hypothetical binary-hazard decision process. It omits social and institutional response constraints, changing hazard types, uncertainty about source reliability, and the possibility that calm or delay is prudent. The supplied probability, likelihood ratios, consequences, threshold and attenuation are invented scenario parameters. The model does not infer credibility, evaluate real warnings, diagnose a cognitive condition, or establish empirical validity. Software contract checks establish only that the illustrative implementation runs as specified.