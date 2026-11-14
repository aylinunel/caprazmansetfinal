# Empathy Gap — illustrative implementation

## Process and observable

This module models a single explicit binary-choice forecast. The supplied forecaster and target state labels index hypothetical utility differences, with positive values favoring option A and zero or negative values favoring option B (ties go to B). For forecaster-state difference `u_f`, target-state difference `u_t`, and intervention strength `s`, the forecast uses:

`u_projected = (1 - s) * u_t + s * u_f`

The reference policy at `s = 0` forecasts directly from the target's supplied state-conditioned utility (`u_t`). The primary metric is per-decision binary forecast error: `1` when the projected forecast differs from the target-state reference choice, otherwise `0`. `active` is true only when projection changes that choice. Returned state retains the step count, cumulative errors, and latest states and choices.

## Necessary condition and scenarios

A projection-based empathy gap requires explicit state-conditioned preference differences and a mismatch between forecaster and target state. At identical states, both utility differences necessarily coincide; the projection cannot change the reference choice at any strength. The positive scenario uses a hungry forecaster (`u_f = 2`) and sated target (`u_t = -1`): at `s = 0.8`, the projected difference is `1.4`, predicting A instead of the reference B. The boundary scenario supplies the same state to both parties (`u = 1.5`), so the forecast and reference remain equal.

## Assumptions and limitations

States and utilities are explicit hypothetical inputs; the mechanism does not infer emotion, bodily condition, preference, or motive. Strength is an illustrative user-settable blend weight, not an estimated effect size. The task reduces interpersonal understanding to deterministic choice prediction between two options; it does not model uncertainty, learning, language, or multiple motives. Forecast mismatch is not inherently harmful, and projection can be a useful heuristic in other settings. This mechanism and its scenarios are synthetic, not empirically validated; tests establish only the specified software behavior and arithmetic.