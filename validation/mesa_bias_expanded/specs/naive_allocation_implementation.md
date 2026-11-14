# Naive Allocation — illustrative implementation

## Process and task metric

The task supplies a positive budget `B` and at least two uniquely named options with nonnegative, commensurable linear utility coefficients `u_i`, with a positive total. The strength-zero reference allocates in proportion to supplied utilities: `a_i(0) = B u_i / Σu`. At setting `s ∈ [0,1]`, the modeled equal-spread process is `a_i(s) = B[(1−s)u_i/Σu + s/n]`, where `n` is the number of listed options. This is a concrete mixture of the task-specific reference and the superficial rule of spreading resources evenly across listed options.

The primary observable is utility-weighted resource yield, `Σ(a_i u_i)`, in utility units. Under this deliberately linear, known-utility task, equal spreading lowers yield when option utilities differ and `s > 0`; the strength-zero comparator is a stated proportional-allocation policy, not a claim that it is universally rational. State records the latest allocations, yield, and cumulative task-step count while preserving other supplied state fields. Trace text records the equation components and supplied utilities. The active flag is true only when heterogeneous utilities and positive strength make an allocation differ from the reference.

## Necessary condition and annotation boundary

Evidence is explicit and structured: utility coefficients are provided by the task; this module does not infer them from text or behavior. Utility heterogeneity is necessary for this implementation to represent naive allocation as an error against its stated yield objective. If all utilities are equal, equal allocation is exactly the proportional reference, and the boundary metric is equal at every strength. Equal allocation may also be appropriate for fairness, diversification, uncertainty, or objectives omitted from the toy task; this implementation must not label those alternatives as errors.

## Scenarios and assumptions

The positive scenario allocates a budget of 100 between utilities 9 and 1. At strength 0 it yields 820 utility units; at strength 0.8 it allocates 58 and 42 and yields 564. The boundary scenario has utilities 4 and 4, so both policies allocate 50/50 and yield 400. Both scenarios supply the same required top-level keys, `budget` and `options`; option structure is validated in `evaluate`.

All coefficients are illustrative assumptions. This compact process omits uncertain or nonlinear returns, interactions, costs, minimum allocations, alternative objectives, and any empirical account of how actual people allocate resources. Strength is an uncalibrated intervention setting. Neither implementation tests nor simulated outputs establish empirical validity, prevalence, or diagnostic accuracy.