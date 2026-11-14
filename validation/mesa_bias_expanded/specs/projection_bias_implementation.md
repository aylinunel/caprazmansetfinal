# Projection Bias — illustrative implementation

## Process and task

The task is to choose one of at least two named options for an explicit future decision. Each context supplies `current_utilities` and `future_utilities`, maps over the same options and expressed on a common 0-to-1 utility scale. The mechanism computes, for each option \(i\),

\[
U_i^{projected}=(1-s)U_i^{future}+sU_i^{current},
\]

where \(s\in[0,1]\) is the generic intervention setting. It selects the greatest projected utility. The deterministic tie-break uses higher future utility, then option name. This models the specific overprojection of present taste onto a future preference estimate; it does not infer either profile from behavior or text.

## Observable and baseline

The primary metric is the selected option's supplied future utility, in units of the supplied 0-to-1 future-utility scale. The strength-zero reference chooses the option with the greatest future utility (ties by option name), so the intervention is evaluated against an explicit future-task policy rather than against an assumed perfect person. `active` is true only when a nonzero setting changes the selected option from that reference. The returned state preserves prior fields and records the most recent choice, reference choice, projected utilities, future satisfaction, and cumulative choice count.

## Necessary conditions and scenarios

The task requires at least two options and paired current/future utility maps with identical option names and finite values in [0, 1]. A projection effect on the choice requires the present and future utilities to differ enough to change the maximizing option. The positive scenario reverses the favorite across current and future profiles; at strength 0.8 the current favorite wins, reducing future-task utility relative to the future-only reference. The boundary scenario supplies identical current and future profiles, removing preference-state divergence; projection then leaves the selected option and metric unchanged.

## Assumptions and limitations

The utility profiles are explicit hypothetical task inputs, assumed comparable and relevant; they are not observations of a person's hidden mental state. A current preference may persist into the future and be an appropriate forecast, especially when profiles agree. This single-choice blend omits uncertainty, transitions, learning, changing options, and other planning strategies. Strength is an uncalibrated intervention parameter, not an effect estimate, prevalence, or confidence. The plugin is synthetic and not empirically validated; passing its software checks is not evidence of psychological validity and it is not a detector or diagnosis.
