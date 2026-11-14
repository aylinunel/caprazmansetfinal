# Regret aversion: illustrative implementation

## Process and task metric

For an action and a status-quo option with matched outcomes, the process computes each option's expected payoff. It defines downside regret as

`R = comparison_feedback × Σ_s p(s) × max(0, payoff_status_quo(s) − payoff_action(s))`.

The action score is `EV(action) − strength × R`; the status-quo score remains `EV(status_quo)`. The higher score determines the choice (ties go to status quo). The primary metric is a binary task choice: 1 means action selected and 0 means status quo selected. The state records the last choice, decision count, and cumulative unscaled expected downside regret.

The strength-zero comparator chooses by expected payoff alone on the same options. This is an explicit reference policy, not a claim of perfect rationality. `active` is true only when the intervention changes the choice from that reference.

## Necessary conditions and scenarios

The model requires explicit action and status-quo options with the same named outcome states and probabilities, finite payoffs, and a supplied feedback-availability fraction in [0, 1]. It does not infer regret or motives from text. Its positive scenario has a higher expected payoff for the risky action but a matched bad-state shortfall; at strength .8 the downside deduction changes the choice. The boundary scenario removes observable counterfactual feedback (feedback fraction 0), so anticipated regret is unavailable and the intervention/reference choices are equal.

## Assumptions and limitations

The coefficient is an illustrative choice-process assumption; strength is an uncalibrated intervention setting, not a probability, prevalence, or person-level trait. The model is intentionally asymmetric (regret attached to action, not the status quo), uses supplied expected payoffs, and ignores nonlinear utility, changing preferences, learning, and many legitimate reasons to prefer either option. Regret can itself be a real preference; a choice is not labeled irrational by this simulation. The module is a compact hypothetical process, not a detector, diagnosis, fitted psychological model, or empirically validated claim.
