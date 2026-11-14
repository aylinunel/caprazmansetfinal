# Survivorship Bias — implementation note

## Process and task metric

Each supplied case has an explicit binary `success` outcome and `observed` status. For a `full_cohort` question, the strength-zero reference is the census success fraction across every supplied case. The intervention reports a visibility-weighted rate:

`reported_rate = sum(success_i * w_i) / sum(w_i)`, where `w_i = 1` for observed cases and `w_i = 1 - strength` for omitted cases.

Thus strength 0 preserves the full-cohort rate; strength 1 analyzes only observed cases. The primary metric is `reported_success_rate`, a proportion in [0, 1] of analyzed case weight classified as successful. State records the analysis count, last target/rates, and IDs receiving positive weight.

For the positive scenario, four observed successes and six omitted failures produce a full-cohort reference of 0.4 and a rate of 4/(4 + 6 × 0.2) = 10/13 (about 0.769) at strength 0.8. This explicit case-selection relation—not a generic belief offset—makes omitted failures contribute less to the reported estimate.

## Necessary condition and boundary

The necessary condition for this modeled error is an estimand mismatch: the task asks about the full cohort, but omitted cases are discounted in favor of the visible sample. The boundary scenario instead asks the narrow descriptive question “what is the success fraction among observed cases?” The visible cases are then the target population by definition; omitted cases are out of scope, so the mechanism and strength-zero reference both report 1.0. This is not evidence about the full cohort.

## Assumptions and limitations

The inputs stipulate case outcomes and visibility; the model does not infer them, detect selection from language, or diagnose an analyst. Binary outcomes and one visibility process are used, without uncertainty intervals or modeling why cases became unobserved. Visibility may be unrelated to outcomes; selection alone need not change the success rate. Strength is an uncalibrated intervention parameter, not an effect size, prevalence estimate, or claim about actual people. The implementation is synthetic and has not been empirically validated.