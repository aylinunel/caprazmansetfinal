# Optimism Bias — illustrative implementation

## Process and task

This plugin models one narrow hypothetical task: forecast whether a project succeeds from supplied counts of comparable successes and failures. The strength-zero reference is the symmetric Laplace estimate

\[p_0 = (S+1)/(S+F+2),\]

where `S` and `F` are nonnegative comparable-outcome counts. At intervention strength \(\lambda\in[0,1]\), the process selectively discounts failures while retaining successes:

\[F_\lambda=(1-\lambda)F,\qquad p_\lambda=(S+1)/(S+F_\lambda+2).\]

The primary metric is `project_success_forecast`, a probability from 0 to 1. The process is active only when strength is positive and at least one comparable failure exists. It is not a generic additive optimism offset: its effect depends on adverse evidence available to discount.

## Evidence and scenarios

Both scenario phases require exactly the top-level task inputs `comparable_successes` and `comparable_failures`; each must be a nonnegative integer and their sum must be positive. The positive scenario supplies six successes and four failures, so strength .8 yields \(7/9\) versus the reference \(7/12\). The boundary scenario supplies eight successes and no failures. With no adverse case to discount, the intervention and reference are equal by the same equation; this is a structural boundary, not a forced zero outcome.

Hope, a favorable forecast supported by the available evidence, or strong success counts alone do not establish bias. This process represents only an explicit hypothetical selective discount of comparable failures.

## Assumptions and limitations

The supplied outcomes are assumed comparable and exhaustive for this toy task; a symmetric unit prior is an explicit reference choice, not a claim of perfect rationality. The linear strength setting is an uncalibrated intervention parameter, not a human effect size, prevalence estimate, or confidence score. The model does not infer motives, assess real people or forecasts, handle changing base rates/covariates, or establish empirical validity. Tests and runner checks are software-contract checks only.
