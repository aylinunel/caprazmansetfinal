# Action Bias implementation note

## Process and task

This illustrative model selects between one immediate intervention (`act`) and waiting. Inputs are comparable expected task utilities in `[0, 1]`; the primary metric is `action_chosen`, a binary choice indicator (1 = act, 0 = wait). Let `g = action_utility - wait_utility`. The strength-zero reference rule acts iff `g > 0` and waits on a tie. When an explicit `evidence_supported` flag is false, an action-pressure term can change the choice: act iff `g > 0` or (`not evidence_supported` and `g + strength × action_pressure > 0`). `action_pressure` is supplied in utility-equivalent units in `[0, 1]`; it represents pressure to resolve this task by taking an immediately available action, not evidence that the action is beneficial. The model reports `active=true` only when this term changes the reference choice. State preserves the selected action, cumulative unsupported-action and decision counts, and the latest utility gap.

## Scenarios and boundary

The positive scenario has action utility 0.40, wait utility 0.50, unsupported evidence status, and pressure 0.30. At strength 0 the actor waits; at 0.8 the pressure (0.24) exceeds the 0.10 disadvantage, so the actor acts. The boundary scenario supplies an evidence-supported action with utility 0.70 against waiting at 0.50. Both the reference and strength-0.8 choice act; the action-pressure mechanism is suppressed. Thus an evidence-based beneficial intervention is not labeled as action bias.

## Assumptions and limitations

This is a hypothetical task-specific process model, explicitly not empirically validated. Strength and pressure are illustrative assumptions, not estimated effect sizes. Users must supply utilities and evidence status; the model cannot assess evidence quality or infer motive, and pressure-to-utility comparability is a substantial simplification. It models one binary choice at a time, not real-world multi-option decisions, outcomes, or population behavior. Passing software tests is not empirical validation.
