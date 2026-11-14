# `causal_overclaim` implementation note

This is a hypothetical structured editorial-decision model, not an NLP detector. A scenario supplies an explicit causal-claim flag, a bounded baseline claim-force score, the number of plausible alternative explanations and how many were addressed, and structured evidence. Covariation evidence must contain at least two numeric pairs with non-zero covariance; time-order evidence must contain at least two named events with strictly increasing timestamps. These checks validate the supplied task facts; they do not prove or disprove causality.

The primary metric is `reported_causal_force`, a unit-interval rhetorical-force score (not a probability or measured audience effect). The strength-zero reference preserves `claim_force` for an explicit causal statement and reports zero when there is no such statement. At nonzero strength, the illustrative transition is

`force = reference_force + strength × (1 − reference_force) × (unaddressed_alternatives / plausible_alternatives)`

only when a causal statement is explicit and at least one plausible alternative remains unaddressed. Otherwise the reference force is retained. This allocates remaining causal-force headroom according to the share of alternatives the assertion leaves unexplained; it is an assumed, task-specific rhetorical process, not a fitted coefficient.

The positive scenario has explicit causal wording, observed covariation, and three of four alternatives left unaddressed (force rises from 0.40 to 0.76 at strength 0.8). The boundary scenario gives event chronology but no explicit causal statement, so its metric remains zero: chronology alone is not annotated as an overclaim. Addressing every listed alternative is also tested as a condition-removing boundary.

All examples and coefficients are synthetic. The model assumes alternatives are complete and equally weighted, accepts structured evidence at face value, and represents neither actual editorial intent nor audience interpretation. It is not empirically validated, and passing software tests is not empirical validation.