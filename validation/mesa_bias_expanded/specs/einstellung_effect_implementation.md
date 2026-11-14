# Einstellung effect implementation note

This plugin is an explicitly hypothetical, synthetic task-process illustration. It is not empirically validated and does not detect human Einstellung effects.

## Process and task measure

Each supplied solution is a valid way to complete the same abstract task, with an `action_count` and a `retrieval_cost`. On each chronological round, the designated learned solution is directly retrievable. Alternatives are admitted only if their retrieval cost fits the remaining search capacity. For a matching `task_family` and `learned_solution_id`, let `n` be the number of prior rounds in which the learned procedure was selected and `B` the supplied search budget. The model uses

`effective alternative-search budget = B / (1 + strength * n)`.

Among the learned solution and alternatives with retrieval cost no greater than that effective budget, it chooses the solution with the fewest actions (ID breaks ties). A chosen learned procedure increments its history only after the current choice; practice therefore affects later rounds, not itself. The primary metric is the selected solution's action count (actions per task). `active` is true exactly when the mechanism's selected solution differs from the reference selection.

## Reference and necessary conditions

At strength zero, the explicit reference retrieves all supplied solutions whose retrieval costs are within the full budget `B` and chooses the one with the fewest actions. This is a task-cost-minimizing reference, not a claim of universal rationality. The modeled effect requires repeated prior selection of the designated learned solution in the same task family, a lower-action alternative, and a budget/cost configuration where the alternative is within the full budget but outside the reduced budget. A familiar tool preference alone is not modeled.

## Scenarios

The positive scenario has two rounds where only the eight-action learned procedure is supplied, then a target round with a two-action alternative (retrieval cost 4) and full budget 5. At strength 0, the alternative is selected; at strength 0.8, two prior learned uses reduce alternative-search capacity to `5 / (1 + 0.8 * 2)`, so the learned eight-action method remains selected.

The boundary scenario carries the same prior practice but changes the target's task family. Its matching-family history is therefore absent; the two-action alternative remains retrievable and strength 0.8 matches the strength-zero metric and choice.

## Assumptions and limitations

Action counts are treated as comparable task costs, each supplied option is assumed valid, and task-family IDs and histories are assumed reliable. The equation and settings are illustrative assumptions, not published effect sizes or calibrated psychology. The model omits partial retrieval, uncertainty, feedback, insight, and possible beneficial reasons for using a familiar procedure. Tests validate code behavior only, not psychological validity.
