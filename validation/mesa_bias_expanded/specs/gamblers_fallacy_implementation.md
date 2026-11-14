# Gambler's Fallacy implementation note

This is an explicitly hypothetical, synthetic process model—not empirically validated and not a text detector. Each chronological context supplies a binary observed outcome, a base probability for outcome 1, and an explicit `independent` fact. State carries the complete sequence of observed outcomes and the stable base probability. Forecasting occurs before the current context's outcome is added.

For a prior run of length `r` ending in outcome `y`, the reference policy predicts 1 iff `p1 >= 0.5` (ties predict 1). If the supplied process is independent and odds have remained stable, the mechanism uses

`p1_adjusted = clamp(p1 - sign(y) * strength * 0.12 * min(r, 4), 0, 1)`,

where `sign(1)=+1` and `sign(0)=-1`; it predicts 1 iff `p1_adjusted >= 0.5`. The returned primary metric is the binary forecast (1 or 0), not accuracy or belief confidence. The coefficient and cap are illustrative user-set assumptions, not effect-size estimates. Strength zero exactly reproduces the stated base-rate reference rule.

The positive scenario is a fair binary sequence with four prior 1 outcomes: at strength 0.8, adjusted p(1) is 0.116 and the next forecast reverses to 0, while the reference predicts 1. The boundary scenario supplies the same sequence but marks the process non-independent; the fallacy mechanism is disabled and the forecast matches the reference. Base probability changes within a carried sequence are rejected rather than misrepresented as a stable-odds process.

Limitations: inputs, independence, and probability are supplied facts rather than inferred evidence; the reversal coefficient, cap, and threshold are not calibrated; and binary forecasts omit confidence, payoffs, richer outcome spaces, and legitimate prediction from changing odds. A run can be informative when the generating process changes or sampling is without replacement, so this model suppresses the fallacy effect when independence is absent and should not treat every streak-based judgment as an error.
