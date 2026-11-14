# Affect Heuristic — illustrative implementation

## Process and task

For a structured **factual option-evaluation** task, each option has supplied benefit \(b_i\), risk \(r_i\), and affect valence \(a_i\). This module defines task utility as \(u_i=b_i-r_i\), with benefit and risk each constrained to \([0,1]\) and affect to \([-1,1]\). The reference policy chooses the option with greatest \(u_i\). At strength \(s\), the modeled affect-substitution policy chooses the option with greatest

\[
q_i=(1-s)u_i+s a_i.
\]

The returned primary metric is the chosen option's **actual task utility** \(u_i\), not the blended choice score. Its factual-task units are benefit-minus-risk units on \([-1,1]\). A displaced choice can therefore lower the metric when the affect signal conflicts with utility; affect is not presumed wrong merely because it is emotional.

For the annotation boundary, `decision_frame="subjective_preference"` instead selects the highest explicit preference score on \([0,1]\), irrespective of strength or affect; the returned metric is that score. This expresses a user's stated subjective preference rather than recasting it as distorted factual judgment. In this frame affect substitution is inactive by definition. Thus metric units are frame-specific: factual utility or stated preference-score units.

## Necessary conditions and state

A factual affect-substitution step requires at least two alternatives and explicit finite benefit, risk, affect, and preference-score fields, with valid ranges and unique nonempty option IDs. No affect, risk, or motive is inferred from words or missing values; missing or impossible evidence raises `ValueError`. Strength must be finite and in `[0,1]`. Ties follow the supplied option order. The returned state preserves prior fields and appends the latest frame, choice, and metric to `decision_history`.

## Scenarios and reference

- **Positive:** In a factual-evaluation choice, `steady` has utility 0.6 and affect -0.8; `thrilling` has utility 0.1 and affect 0.9. The utility-maximizing reference selects `steady` (metric 0.6). At strength 0.8 their blended scores are -0.52 and 0.74, so the modeled choice selects `thrilling` and returns utility 0.1 (decrease).
- **Boundary:** In a subjective-preference task, `calm` has stated preference 0.9 and `thrilling` 0.2, despite opposing affect signals. Both the reference and strength-0.8 process choose `calm` and return 0.9 (equal). The removed necessary condition is factual evaluation: an emotion-linked preference does not by itself establish a distorted factual judgment.
- **Strength zero:** In factual evaluation \(s=0\), so \(q_i=u_i\); the process exactly reproduces the stated maximum-benefit-minus-risk reference rule.

## Assumptions and limitations

The normalized scales and linear blend are user-settable illustrative assumptions, not published effect sizes, fitted parameters, or measured psychological laws. The module models one explicit structured choice and does not simulate population prevalence, infer private emotional states, classify text, or assess overall welfare. Affect may contain useful information in real settings, and the subjective-preference rule is deliberately not treated as an error. **This implementation is hypothetical and not empirically validated; software tests establish only behavior of the specified code.**
