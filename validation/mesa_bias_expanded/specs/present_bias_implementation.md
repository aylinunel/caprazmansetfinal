# Present Bias implementation (illustrative)

## Process and observable

The task supplies two options, each with an explicitly stated nonnegative payoff and delay, plus an exponential reference discount rate `r` and present weight `beta` in `(0, 1]`. At intervention strength `s`, the model uses `beta_s = 1 - s(1 - beta)`. Option `i` is assigned value

`V_i = payoff_i * exp(-r * delay_i) * (1 if delay_i == 0 else beta_s)`.

The selected option maximizes this value; the supplied option order resolves exact ties. Thus strength zero is an explicit exponential-discount reference (`beta_s=1`), not a claim of perfect rationality. The primary metric is a binary indicator for whether the selected option has delay zero. State stores the sequence of selected option IDs, delays, and payoffs by decision round. The intervention is active only when its selected option differs from the strength-zero reference selection.

## Necessary condition and scenarios

The positive scenario presents immediate and delayed options across two chronological decision rounds. At the stated illustrative parameters, increasing strength discounts delayed rewards further and increases immediate selections relative to strength zero. The boundary scenario gives each compared pair the same positive delay. There is then no immediate-versus-delayed timing contrast; multiplying both options by the same present weight cannot change their ranking or the immediate-choice metric. It remains a real choice task, rather than a hardcoded zero-effect case.

## Assumptions and limitations

Payoffs are treated as comparable and certain; the rate and present weight are task-supplied hypothetical coefficients. This narrow quasi-hyperbolic illustration can overlap with decreasing-impatience models. It omits liquidity constraints, uncertainty, changing circumstances, and many reasons to prefer an earlier outcome. It cannot infer motives, detect bias in real people, or establish that an immediate choice is erroneous. Strength is an uncalibrated intervention setting. Passing software checks is not empirical validation; no population or empirical-validity claim is made.
