# Barnum effect implementation note

This synthetic one-step process model scores **unique-personal attribution** on a unitless 0–1 scale for one description. The strength-zero reference policy is `agreement × verified_individual_fit`; agreement alone therefore does not imply uniqueness. With strength `s`, the implemented score is:

`reference + s × cue × (1 − reference)`, where `cue = vagueness × population_applicability × perceived_personal_specificity` only when the reader agrees and perceived personal specificity is at least 0.5; otherwise `cue = 0`.

Required inputs are explicit hypothetical ratings in [0, 1], plus a Boolean agreement and independently supplied fit. The gate represents the spec's necessary boundary condition: merely agreeing with a general statement is insufficient. At strength zero, the score is exactly the reference. The positive scenario uses high vagueness, broad applicability, agreement, and perceived specificity; the boundary scenario lowers perceived specificity below the gate and must match the reference score.

The state records evaluation count, last attribution, and count of scores at least 0.5, while preserving other state entries. Coefficients and the threshold are illustrative assumptions, not empirical effect sizes. This is not a validated psychology model, text detector, diagnosis, or claim about population behavior; it assumes that supplied ratings faithfully represent the scenario and omits context and individual differences. Media practices that present general statements are not themselves classified as errors by this mechanism.
