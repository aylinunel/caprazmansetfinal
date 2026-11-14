# Telescoping effect: illustrative implementation

## Process and task

Each chronological context supplies an `event_id`, its supplied `event_day`, and the `current_day` of a recall report. The plugin carries dated reports in `state.history`, requires strictly increasing current days, and rejects a repeated event ID with a conflicting event date. Actual age is `current_day - event_day`. For ages of at least 30 days, the illustrative forward-telescoping rule reports `actual_age × (1 − 0.20 × strength)`, bringing the old event closer to the present. For positive ages under 30 days, the illustrative backward-telescoping rule reports `actual_age × (1 + 0.20 × strength)`, pushing the recent event farther away. At age zero, no elapsed temporal distance exists, so the date is unchanged.

The primary metric is absolute recalled-age error in days, `abs(recalled_age − actual_age)`. This is a task-specific observable, not a measure of a person's general memory or a belief score. `active` is true only when positive strength changes an event report. The strength-zero reference explicitly reports supplied dates without telescoping (`recalled_age = actual_age`); it is a comparison policy, not a claim of perfect human recall.

## Scenarios and necessary condition

The positive scenario repeatedly reports a dated old event as chronological current day advances. At strength 0.8, a 90-day-old event is represented as 75.6 days old, yielding 14.4 days absolute error; the zero-strength reference yields 0. The boundary scenario reports events dated exactly on their respective current days. It removes the process's necessary condition—nonzero elapsed temporal distance—so the date cannot be displaced and both policies yield zero error. These are hypothetical structured task inputs, not detected memories.

## Assumptions and limitations

The 30-day cutoff and 20% maximum proportional shift are transparent illustrative parameters, not published or fitted effect sizes. Strength is an uncalibrated intervention setting. The model captures only the annotation's two directional age-displacement patterns for already dated events; it does not infer dates, identify telescoping in natural language, establish empirical validity, or represent other causes of recall error. Accurate and distorted recall can coexist, and this synthetic process makes no prevalence, diagnostic, or population claim. Software-contract success is not empirical validation.
