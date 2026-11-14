# Noble Edge Effect — implementation note

## Process and task measure

This is a compact illustrative product-choice process for the supplied concept: perceived corporate social responsibility (CSR) can increase a product's favorable evaluation or purchase appeal. For each supplied option, the reference appeal is `quality_score - 0.35 × price_index`. If and only if that option has explicit `csr_evidence: true`, the intervention adds `20 × strength × perceived_csr_score`. The agent selects the option with the highest resulting appeal. The reported primary metric is the focal option's appeal in illustrative utility points; selection and the CSR premium are retained in state and explained in the trace. CSR never changes the quality input, and the model makes no inference about sound quality.

`strength` is an uncalibrated intervention setting from 0 to 1, not confidence, prevalence, or an estimated empirical coefficient. The zero-strength reference uses the same supplied quality and price task and omits the CSR premium.

## Necessary condition and scenarios

A positive CSR contribution requires both explicit CSR evidence and a positive perceived CSR score. The positive scenario supplies evidence and a score of 0.9 for the focal option, alongside a slightly higher-baseline-appeal alternative, so the CSR contribution raises focal appeal and can change the selected option. The boundary scenario removes the necessary evidence (and sets the score to zero); strength therefore has no effect and the result equals the zero-strength reference. Only `products` and `focal_option` are common top-level scenario inputs; product schemas and numeric ranges are validated within `evaluate`.

## Assumptions and limits

The product attributes and coefficients are hypothetical structured inputs, not detected from prose or a real market. The process isolates an ethical preference contribution; favoring a socially responsible product can be entirely reasonable and is not inherently an error. It does not model trade-offs beyond a simple quality/price utility, heterogeneous consumers, uncertainty about CSR claims, or real purchase behavior. Passing executable checks or synthetic tests is not empirical validation; no empirical validity or diagnostic claim is made.
