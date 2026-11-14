# Nostalgia effect implementation

## Process and task

This is a synthetic two-phase single-item purchase task, not an NLP detector. In the first chronological phase, the participant supplies a structured autobiographical episode from an earlier year, when it is recalled, and its positive warmth on a 0–1 scale. In the later purchase phase, structured task inputs specify the item, its explicit link (or lack of link) to that episode, the link strength, baseline willingness-to-pay (WTP), item price, and spending sensitivity.

For a warm autobiographical memory whose ID matches the offered item's explicit memory link, the illustrative reservation-price process is:

`adjustment = strength × memory_warmth × association_strength × spend_sensitivity`

`adjusted_WTP = baseline_WTP + adjustment`

The task's metric is actual spend on the offered item in currency units: price if adjusted WTP is at least the price, otherwise zero. The strength-zero reference uses the same task and buys exactly when baseline WTP is at least price. The model therefore requires a specific spending context and a linked, positively felt past memory; simply having nostalgia does not trigger a purchase effect. Unmatched, non-autobiographical, or non-warm memories add no WTP.

## Scenarios

Both scenarios first record the same warm autobiographical episode from 1998, recalled in 2026, and then present an item priced at 10 with baseline WTP 8.5. In the positive scenario, the item is linked to that episode. At sensitivity 4.0 and strength 0.8, the adjustment is `0.8 × 0.9 × 0.8 × 4 = 2.304`, so WTP is 10.804 and the simulated purchase spends 10; the strength-zero reference spends zero. In the boundary scenario, the item links to a different episode ID, removing the necessary association; the adjustment is zero and spend equals the strength-zero reference. These are task-specific illustrative choices, not predictions about real consumers.

## Scope and limitations

All coefficients are explicit hypothetical inputs, not calibrated effects or empirical estimates. Strength is an uncalibrated intervention setting, not confidence, population prevalence, or evidence of validity. Explicit structured reports are assumed rather than inferred from keywords or hidden motives. This minimal choice task omits budgets, competing products, affordability, social influences, changing memories, and heterogeneous preferences; real spending is not implied by the model. Nostalgia is not classified as harmful, and software tests establish executable behavior only—not psychological validity.
