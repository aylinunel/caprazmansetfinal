# Recency Effect — implementation note

## Process and metric

This hypothetical task asks which of two labels (A or B) is more represented in a supplied chronological stream. Each step appends its explicit `observation` to the agent's `state.history`; the sequence is not inferred from prose. For an item at age `a` (0 = newest), the intervention assigns

`w(a) = (1 - strength) + strength * 0.55**a`.

The process selects the label with the larger sum of its item weights. Ties retain the prior choice, or choose A when no prior choice exists. The strength-zero reference is the same explicit task with equal weight `w(a)=1` for every observation, i.e. the equal-count majority (ties use the same rule). The primary metric is `choice_is_B`, a binary indicator (1 if B is selected, otherwise 0); it is a task choice, not a prevalence estimate or general belief score.

## Necessary condition and scenarios

The necessary condition is an explicitly ordered sequence (`sequence_ordered=True`). In the positive scenario, four A observations are followed chronologically by three B observations. At strength 0.8, recent B observations can outweigh the older A majority, producing a higher final `choice_is_B` than the equal-count reference. In the boundary scenario the same supplied labels are explicitly unordered (`sequence_ordered=False`); position-based weights are inapplicable and the equal-count choice is used, yielding equality with strength zero. Contexts are successive observations, and each step carries the updated history and choice.

## Assumptions and limitations

The 0.55 age-decay factor is an illustrative, user-settable assumption. Strength is an uncalibrated intervention control, not an empirical effect size, confidence, or estimate of how common this process is. The model intentionally represents a narrow serial-position judgment over explicit symbolic observations; it is not an NLP detector, diagnosis, general account of memory, or claim about human populations. Real-world anecdotes used to infer how prevalent something is may instead involve availability or other processes; that task is outside this implementation. A small synthetic test establishes software behavior only, not empirical validity.
