# IKEA Effect implementation note

This module is an explicitly hypothetical, synthetic reservation-value process, not an empirical psychology model or detector. For a hypothetical item, the reference value is `objective_value + objective_customization_benefit`. The primary metric is

`reference value + strength × 2 valuation points/hour × assembly_effort_hours`

when `self_assembled` is true; otherwise the assembly premium is zero. The coefficient is an illustrative assumption, not a published effect size. `strength=0` is the reference policy: count supplied objective value and explicit objective customization benefit, but add no personal-assembly premium. `owned` is validated and reported in the trace, but ownership alone has no valuation effect.

The primary metric is hypothetical reservation value in valuation points (objective-value points plus effort-linked points). The necessary condition for the modeled effect is personal assembly with positive supplied effort. The positive scenario holds objective value, customization benefit, and ownership fixed and varies only intervention strength for a self-assembled item. The boundary scenario describes an owned item assembled by someone else and therefore exactly matches the strength-zero reference value. An explicit customization benefit remains part of the baseline regardless of who assembled the item, separating genuine objective benefits from the modeled premium.

All facts are structured inputs; this module does not infer them. The simple linear effort rule cannot distinguish pride or labor from learning, enjoyment, or other benign explanations, does not represent heterogeneous preferences or changing valuations over time, and has no empirical validation. Tests establish software behavior only, not psychological validity.
