# Motivating Uncertainty Effect — implementation note

## Process and task

This plugin models a hypothetical choice of discrete effort to pursue a reward whose size is uncertain. For each available effort level `e = 0, …, effort_cap`, it computes

`U(e) = e × reward_mean − effort_cost × e² / 2 + strength × 0.5 × reward_spread × pursuit_focus × e`.

The first two terms are the reference task policy: maximize expected reward less a convex effort cost. The last term is an explicitly assumed, pursuit-specific excitement premium: reward-size uncertainty can raise the utility of effort only when the task input says attention is focused on pursuing the reward. The choice is the effort level with highest utility, ties going to lower effort. Strength zero therefore supplies the same-task expected-value/cost reference, not a claim of perfect or universally rational behavior. The metric is chosen effort, in discrete effort units per decision.

## Conditions and scenarios

All scenarios require the same task fields: nonnegative expected reward and reward spread, positive effort cost, pursuit focus in `[0, 1]`, and an integer effort cap. The positive example holds mean reward and cost fixed while supplying positive reward spread and full pursuit focus; under the illustrative coefficient it selects greater effort than strength zero. The boundary example sets reward spread to zero, removing reward-size uncertainty, and therefore exactly matches the strength-zero choice. Missing or invalid evidence is rejected rather than interpreted as no effect.

## Scope and limitations

This is a compact, synthetic process illustration, not an NLP detector, diagnosis, population claim, or fitted psychological model. The coefficient `0.5` is an arbitrary, transparent modeling assumption; `strength` is an uncalibrated intervention setting, not an empirical effect size or confidence. Explicit focus and uncertainty are task inputs and are not inferred. Uncertainty may instead deter effort or have no effect in other contexts; the model does not represent those alternatives, learning, actual payout outcomes, or heterogeneous preferences. Software-contract success is not empirical validation.
