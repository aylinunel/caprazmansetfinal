# Restraint Bias — illustrative implementation

## Process and metric

This plugin models one hypothetical choice between a tempting option and a safe alternative. Inputs supply temptation load and reward, a safe payoff, lapse cost, task-specific actual resistance, and the agent's explicit self-assessed resistance. The mechanism requires **overestimated self-control** (`self_assessed_resistance > actual_resistance`); neither optimism in general nor a single indulgence is treated as evidence of the concept.

For intervention strength `s` in `[0,1]`, perceived resistance is

`estimated = actual + s * max(0, self_assessed - actual)`.

The model predicts lapse probability as `p = clamp(temptation_load - estimated, 0, 1)`, then values the temptation option as `(1-p) * temptation_reward - p * lapse_cost`. It selects temptation only when this expected payoff is strictly greater than `safe_reward`; ties select the safe option. The primary metric is a binary choice indicator (1 for temptation, 0 for safe), not a belief score or diagnosis. State retains estimated resistance, predicted lapse probability, and the choice.

## Reference, scenarios, and assumptions

At strength zero, the explicit reference policy values temptation using the supplied actual resistance, without the overconfidence adjustment. The positive scenario makes the same risky option appear unattractive under actual resistance and attractive under an inflated self-assessment. The boundary scenario retains temptation and possible difficulty but sets self-assessed resistance equal to actual resistance, removing the necessary overconfidence condition; the intervention therefore matches the reference.

All numeric parameters are hypothetical task facts, not inferred personal traits. The linear lapse-risk mapping, payoff equation, and intervention strength are illustrative user-settable assumptions, not measured or calibrated psychological effects. A chosen temptation can be benign depending on the task; the model does not classify conduct as harmful. It omits changing contexts, learning, fatigue, habits, precommitment, external supports, and stochastic lapse outcomes, and is not an NLP detector, diagnosis, or population model. Software contract checks are not empirical validation.
