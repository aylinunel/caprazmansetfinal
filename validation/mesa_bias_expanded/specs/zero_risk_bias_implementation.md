# Zero Risk Bias — illustrative implementation

## Process and task measure

Each option is a risk profile with residual event probabilities, an additive expected-harm calculation, and an explicit cost. For baseline risks `pᵢ` and supplied severity weights `hᵢ`, baseline harm is `H₀ = Σ pᵢhᵢ`. Plan `j` has gross reduction `Rⱼ = H₀ − Σ qᵢⱼhᵢ` and unadjusted net value `Nⱼ = Rⱼ − cⱼ`. The strength-zero reference chooses the plan maximizing `Nⱼ` (input order breaks exact ties).

A zero-endpoint premium is considered only when a plan takes at least one strictly positive baseline risk to exactly zero, and there is a rival with both a larger gross expected-harm reduction and higher unadjusted net value. For such a qualifying endpoint plan, the illustrative choice score is `Nⱼ + strength × 2 × Σ(pᵢhᵢ)` over only the risks it eliminates. The coefficient `2` is a transparent hypothetical assumption, not a calibrated effect. Other plans retain `Nⱼ`. The selected option's primary metric is residual expected harm plus its supplied cost, in expected-harm units per decision; `active` is true only if this process changes the strength-zero plan choice.

This is a direct option-selection model, not a generic belief adjustment. It encodes the defined endpoint preference while separating risk levels, severity, and costs. A zero-risk choice can remain appropriate when it already maximizes the unadjusted value; the model does not label every zero endpoint an error.

## Inputs and scenarios

Every decision requires the top-level fields `baseline_risks`, `harm_severities`, `options`, and `plan_costs`. Risk and severity keys must match; every option must specify the same risks; costs must match the option names. Probabilities are in `[0,1]`, severity weights are positive, and costs are nonnegative and expressed in the same illustrative units as harm. Inputs are validated within `evaluate`; missing or malformed evidence is rejected, not treated as a negative finding.

The positive scenario starts from risks `0.10` and `0.40`. Eliminating the smaller risk reduces expected harm by `0.11`; a comparator reduces it by `0.25`. At strength `0.8`, the endpoint premium is `0.8 × 2 × 0.10 = 0.16`, enough to change the choice from the comparator (metric `0.25`) to the endpoint plan (metric `0.39`). The boundary scenario changes that endpoint to a residual probability of `0.01`, so no positive risk is fully eliminated; the larger-reduction option remains selected and the metric matches the strength-zero reference.

## Scope and limitations

The inputs and choices are hypothetical and synthetic only. Strength is an uncalibrated intervention parameter, not confidence, prevalence, or empirical effect size. This deterministic example does not model risk dependence, uncertainty intervals, interactions, heterogeneous harm distributions, fairness, implementation constraints, reversibility, or value disagreement. Supplied severity and cost units must be comparable, and the additive expectation may not suit real decisions. No human-validated or empirical-validity claim is made; software-contract checks do not establish psychological accuracy.
