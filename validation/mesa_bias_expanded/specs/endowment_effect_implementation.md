# Endowment Effect: illustrative mechanism

This synthetic, task-specific model evaluates a sale offer for an explicitly identical item before and after ownership. Its primary metric is a binary decision: `1` means accept the offer; `0` means retain the item. It does not infer ownership, preference, or psychological state from text.

Let `v_pre` be the supplied pre-ownership valuation, `m_pre` and `m_now` the item's pre-ownership and current market values, `c` the sale transaction cost, and `a` the explicit acquisition reference value. The strength-zero reference reservation value is

`r0 = max(0, v_pre + (m_now - m_pre) + c)`.

For an owner, the hypothetical ownership premium is `p = strength * max(0, a - r0)`; otherwise `p = 0`. The current reservation threshold is `r = r0 + p`. The agent accepts when `sale_offer >= r` (ties accepted). Thus this is a state/choice process tied to an ownership reference gap, not a generic penalty. Market-price movement and transaction cost affect the ordinary reference value separately from the ownership-specific increment.

The strength-zero baseline is the transparent market-adjusted pre-ownership valuation plus transaction cost, with no ownership premium. In the positive scenario, the same item is owned, `r0=10`, acquisition reference is 16, and offer is 13; at strength .8 the threshold becomes 14.8 and the offer is rejected, while the reference accepts. The boundary scenario changes only `is_owner` to false, removing a necessary condition; the premium is zero and the strength-.8 decision equals the reference decision.

The assumptions are deliberately narrow: the supplied acquisition reference is treated as the owner's relinquishment reference, and the offer decision is a deterministic threshold. An acquisition price or high reference may instead reflect legitimate quality information, changed preferences, strategy, or other factors. The model omits many relevant motives and market details. Inputs and coefficients are hypothetical; this mechanism is not empirically validated and does not establish that any real valuation gap is biased.
