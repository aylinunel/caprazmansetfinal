# Observer Expectancy Effect — implementation note

## Illustrative process

This plugin models one narrowly specified route for an observer's expectation to affect an observed participant: an expectation is conveyed through a visible interpersonal cue, the participant responds to that cue, and the changed participant expectancy affects performance on a susceptible task. For each chronological round, let `E` be prior participant expectancy, `O` the explicit signed observer expectation, `C` cue visibility (or zero when the observer is absent), `R` participant responsiveness, `s` the intervention strength, `T` task susceptibility, and `B` baseline performance:

`E' = E + s × C × R × (O − E)`

`task_performance = B + T × E'`

The state carries `E'` between rounds, so a previously conveyed expectation can persist after a cue changes. The returned task-specific metric is in illustrative task-performance units; it is not a belief score or a judgment by the observer. The trace reports the transition and resulting performance.

## Reference and necessary conditions

At strength zero, the reference policy disables transmission (`E' = E`) while retaining the same task baseline and susceptibility. It is a transparent comparison policy, not a claim of perfect or unbiased human behavior. For a transmission effect, the model requires a nonzero observer expectation, an observer present, a communicated cue, participant responsiveness, and task susceptibility. The boundary scenario keeps the observer present and expectation positive but sets cue visibility to zero: merely being watched is not enough, so the intervention matches the zero-strength reference. If expectation is already present in carried state, its persistence can continue to affect performance even when a later cue is absent.

## Scenarios and assumptions

The positive scenario uses three chronological rounds of a positive expectation cue, with explicit hypothetical observer expectation, cue visibility, participant responsiveness, task susceptibility, and baseline performance. The boundary scenario uses two rounds with no cue communicated. All scenario task inputs are top-level fields required in every phase; runner-provided state and per-agent metadata are not embedded in scenario contexts.

All coefficients and inputs are illustrative assumptions, not measured effect sizes. Strength is an uncalibrated intervention knob, not probability, confidence, prevalence, or an empirical claim. The model does not infer expectations or cues from behavior or text. It does not simulate observer-biased scoring, the mere performance effect of being watched, or any particular real-world population. Alternative causes of performance, cue interpretation, and the ethical or beneficial meaning of an expectation are outside its scope. The plugin is synthetic only and has not been empirically validated.
