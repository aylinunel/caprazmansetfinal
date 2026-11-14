# Reactive devaluation: implementation note

## Illustrative process

This plugin models one hypothetical choice between a proposal and the status quo. Each task context supplies normalized values in `[0,1]`: proposal utility `U`, status-quo utility `Q`, explicit source dislike `D`, and credible strategic risk `R`. The strength-zero reference is source-neutral: accept the proposal exactly when `U - R > Q`; a tie retains the status quo. At strength `s`, the illustrative process instead compares `U - R - s × 0.5 × D` with `Q`. The coefficient `0.5` is an explicit toy assumption, not an estimated human effect. The primary metric is binary proposal acceptance (1) versus status-quo retention (0). `active` is true only when the source term changes the reference choice.

The equation separates source-driven devaluation (`D`) from credible substantive risk (`R`): risk affects both policies, whereas the source term requires an explicit positive dislike attribution. The model does not infer that attribution from a name, phrase, identity, or document. Its state records the current choice, reference choice, adjusted score, and whether the choice changed; no fictitious history is required for this single-step task.

## Scenario checks

- **Positive:** `U=.78`, `Q=.45`, `D=.90`, `R=.08`. The reference value is `.70`, so it accepts. At strength `.8`, the source penalty is `.36`, leaving `.34`; it retains the status quo. This is a direction check on the illustrative equation, not evidence about people.
- **Boundary:** identical substantive values but `D=0`, meaning no disliked/adversarial source attribution is supplied. The necessary source condition is absent, the source term is zero at every strength, and both policies accept the proposal. This is an equality boundary, not a hardcoded zero outcome.

## Scope and limitations

This is a compact, deterministic toy process for the specification's source-based devaluation boundary. Utilities, risk, and source attribution are stipulated structured inputs; it is not an NLP detector, diagnosis, or population model. A proposal may rationally be rejected because of credible strategic risk or inferior substantive utility, independent of source identity. Real decisions can involve uncertainty, negotiation, changing utilities, trustworthiness evidence, and strategic incentives omitted here. Strength is an uncalibrated intervention setting, and software-contract tests do not establish empirical validity or detection accuracy.
