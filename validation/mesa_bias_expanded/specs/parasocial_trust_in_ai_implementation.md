# Parasocial Trust in AI: illustrative implementation

## Task and process

This plugin models one structured hypothetical decision: whether to disclose sensitive information for a task involving an AI assistant. It does not inspect text or infer a person's hidden motives. Every scenario explicitly supplies AI capability, task requirement and value, disclosure cost, relational trust, and interaction warmth on normalized 0–1 scales.

Let capability adequacy be `a = min(ai_capability / task_requirement, 1)` and relative capability shortfall be `g = max(task_requirement - ai_capability, 0) / task_requirement`. The zero-strength reference utility for disclosure is `U0 = task_value * a - disclosure_cost`. At intervention strength `s`, the additional relational utility is `B = s * relational_trust * interaction_warmth * g * task_value`; final utility is `U = U0 + B`. The simulated choice is disclose when utility is strictly positive, otherwise withhold. The primary metric is that binary choice (1/0); the trace reports adequacy, shortfall, reference utility, bonus, and decisions. State preserves the number of decisions and disclosures and the most recent decision diagnostics.

This is deliberately an explicit process model rather than a classifier. Relational trust and warmth must both be nonzero, and capability must be below the task requirement, for the proposed parasocial uplift to operate. Warm interaction alone is not evidence of parasocial trust. With sufficient capability, the shortfall term is zero; with no relational trust, the relationship term is zero. The model treats unsupported reliance/disclosure as an illustrative choice, not a finding that trust or disclosure is inherently wrong.

## Reference and scenarios

The reference policy at strength zero makes the same capability-adjusted task-value versus disclosure-cost comparison, but adds no relationship-based uplift. It is a simple task-specific comparator, not a claim of perfect rationality.

The positive scenario combines substantial unmet capability, high task value, high explicit relational trust and warmth, and a disclosure cost that makes the reference withhold. At strength 0.8 the proposed bonus crosses the choice threshold and increases disclosure. The boundary scenario retains warmth, capability shortfall, task value, and cost but removes explicit relational trust; it therefore has no relationship bonus and matches the reference choice. A separate programmatic boundary also tests sufficient capability, which eliminates the unsupported shortfall condition.

## Assumptions and limitations

All coefficients and normalized values are hypothetical user-settable assumptions; strength is an uncalibrated intervention setting, not a probability, prevalence, or empirical effect size. The linear utility rule and binary threshold simplify a complex, contextual decision. The implementation omits consent design, data safeguards, privacy norms, task-specific capability uncertainty, individual differences, and many benign reasons to trust or disclose. It makes no empirical validity claim and is not a diagnosis, population model, or detector of real-world AI relationships.
