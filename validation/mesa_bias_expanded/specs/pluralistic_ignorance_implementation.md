# Pluralistic Ignorance — illustrative implementation

## Process and task

This toy binary-choice task makes the annotation boundary observable rather than inferring hidden views. Each phase supplies a full hypothetical group's private positions (`1` = support, `0` = oppose) and a perceived support fraction for each member. A strict actual majority is calculated from the private-position vector; a perceived strict majority is support above 0.5 or opposition below 0.5 (a tie is indeterminate).

For agent *i*, the necessary gate is true only when their private position agrees with the strict actual group majority and their perceived strict majority is the opposite. If that gate holds, the intervention selects public expression of the perceived majority when the supplied exogenous uniform draw is below `strength`; otherwise the agent expresses their private position. The primary metric is a realized binary mismatch between public and private position, in mismatch-indicator units per agent-step. State records the current private/public positions, mismatch, and cumulative conforming steps.

## Reference and scenarios

Strength zero is the explicit private-expression reference (`public position = private position`), not a claim of perfect rationality. The positive scenario has a unanimous private support view and a perceived opposition majority, so the required shared misperception can create public/private mismatch. The boundary scenario keeps that same actual group but supplies perceptions matching its actual majority, removing the necessary misperception condition; intervention and reference therefore agree.

## Assumptions and limitations

Strength is an uncalibrated intervention probability, not confidence, prevalence, or an empirical effect size. The supplied complete private-view vector and agent-specific perceptions are stipulated task facts, not inferred observations. The model is a compact one-step binary selection process; it omits uncertainty, costs, relationships, strategic speech, plural group subgroups, and alternative explanations for public/private differences. A simulated mismatch is not evidence that any real person or group experiences pluralistic ignorance, and the implementation is neither an NLP detector nor a diagnosis. Software contract tests do not validate psychological accuracy.

## Population-aware teaching scenario

The three-member scenario remains the default for direct plugin contract tests. `scenarios_for_population(n_agents)` creates a full, explicitly hypothetical group of the requested size using the same teaching assumptions: every member privately supports, while perceived support is 0.2 in the positive case or 0.8 in the boundary case. The Mesa runner uses this opt-in factory only for built-in scenarios; it does not estimate or infer group views, change empirical facts, replicate a custom group's members, or wrap agent indexes. Custom group vectors must still identify every simulated member and remain strictly validated.

The factory fixes a discovered 12-agent sweep integration failure: the old fixed three-person teaching vector could not identify agents beyond index two. New 12- and 50-agent regressions test full-strength expression, zero-strength private expression, the no-misperception boundary, and rejection of mismatched custom groups. This is a population-size software repair, not evidence of psychological validity.
