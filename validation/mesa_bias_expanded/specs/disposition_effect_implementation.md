# Disposition Effect — illustrative mechanism

For each supplied position, the reference retention margin is

`M = (expected_hold_value + hold_strategy_adjustment) - (sell_value - sell_tax + sell_strategy_adjustment)`.

The reference retains when `M >= 0` and sells otherwise (ties retain). This is a forward-value comparison; purchase price does not enter it. For an owned position with nonzero unrealized return `r = (current_value - cost_basis) / cost_basis`, the illustrative mechanism instead uses `M' = M - sign(r) * strength * 0.25 * abs(r) * current_value`. Thus loss status shifts the choice toward retention, while gain status shifts it toward sale. Unowned and break-even positions receive no status pressure. Tax and strategy effects are explicit inputs to the reference policy.

**Task and metric.** The task is choosing whether to retain or sell each supplied position. The primary metric is the count of owned positions whose simulated choice differs from the forward-value reference, in positions per evaluation. `active` is true exactly when at least one such choice changes. The returned state appends each round's decision records to `decision_history`.

**Scenarios and boundary.** The positive example supplies an owned losing position the reference would sell and an owned winning position the reference would retain; at strength 0.8 each can flip in the disposition-effect direction. The boundary example removes unrealized gain/loss status with a break-even owned position and also includes a losing position that is not owned; the status mechanism then has no effect and the metric equals the strength-zero reference.

**Assumptions and limitations.** All values are explicit synthetic inputs on a comparable scale and horizon. The 0.25 sensitivity is an illustrative coefficient, not a published or fitted effect size; strength is a simulation setting, not prevalence or confidence. The deterministic model is not an NLP detector, diagnosis, motive inference, empirical psychology, or investment advice. Actual portfolios involve risk, liquidity, taxes, strategy, and interactions simplified here. The module and tests are not empirically validated, and no detection accuracy has been measured.
