# Mental accounting: implementation note

## Process and task

This compact illustrative process models a purchase opportunity with explicit numeric benefit, price, funds in a category-matched envelope, and funds in other envelopes. Let `M` be matched funds, `U` unmatched funds, `s` the generic intervention strength in `[0,1]`, and `T` be true only when the task explicitly says that accounts are separate and the purchase category matches the envelope. Recognized funds are

`F = M + (1 - s) U` when `T` is true, and `F = M + U` otherwise.

The hypothetical decision is to buy exactly when supplied benefit is at least price and recognized funds cover the price. The primary metric is realized net surplus per purchase opportunity: `benefit - price` when bought, otherwise zero, in illustrative utility units. State records purchase count and the latest choice, recognized funds, and surplus. There is no stochastic choice or inferred internal state.

## Reference and necessary conditions

At strength zero, all funds are fungible (`F=M+U`); a purchase is then made if it is worthwhile and total funds cover its price. The mechanism requires both explicit account separation and an explicit category match. The positive scenario supplies both, with total funds sufficient for a worthwhile purchase but the matched envelope insufficient once unmatched funds are discounted. The boundary scenario removes account separation while keeping the other facts unchanged, so intervention and reference coincide. A category mismatch also disables the modeled partition.

## Scope and limitations

The settings and linear discount are user-settable illustrative assumptions, not measured effect sizes or an empirically calibrated psychological law. The chosen metric isolates one hypothetical choice; it does not establish that a real person made an error. Budgeting can be useful, while liquidity constraints and intentional category limits can be real; a category-driven inconsistency alone is not enough to call behavior erroneous. This implementation is a synthetic process model, not a natural-language detector, diagnosis, prevalence estimate, or validated prediction.