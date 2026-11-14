# Hot Hand Fallacy implementation note

## Process and metric

This illustrative plugin models a next-trial success forecast after chronological binary outcomes. The primary metric is a probability in `[0, 1]`. Its explicit strength-zero reference policy is `base_rate + supported_persistence_delta`, where both values must be supplied and their sum cannot exceed one. At each step, state carries the consecutive-success streak. If the current streak is at least two and the explicitly supplied supported persistence increment is zero, the model adds

`min(1 - reference_forecast, strength * 0.12 * (streak - 1) / (streak + 1))`.

The coefficient and curve are illustrative assumptions, not effect sizes. The state is updated using the current outcome; there is no stochastic choice.

## Conditions and scenarios

A positive effect requires consecutive successes, explicit absence of supported persistence increment (`supported_persistence_delta=0`), and strength above zero. The included positive scenario carries two successes and compares `.8` with strength zero. Its last forecast is `0.532` versus the `0.5` reference. The boundary scenario keeps the success streak but supplies an explicit supported persistence increment (`0.1`), so the forecast remains `0.6` at both strengths. A broken streak is also tested and produces no uplift.

## Assumptions and limitations

The caller supplies trustworthy task base-rate and persistence evidence; this mechanism does not estimate either or infer support from words. An explicit zero increment means no persistence support is supplied, while missing evidence is rejected. This is a compact hypothetical process model, not an empirical theory, population claim, diagnostic, or natural-language detector. The chosen streak threshold and uplift curve have not been empirically validated; genuine persistence may arise in skill-based tasks, and the inputs may be misspecified.
