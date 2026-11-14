# Impact Bias — illustrative implementation

## Process and task metric

This synthetic task accepts one explicitly matched forecast/outcome pair per chronological context. A forecast provides peak emotional intensity `F` (0–10) and duration `D` (positive discrete steps). The complete observed trajectory `O[1…T]` gives intensity by step, including trailing zeroes after the response ends. Its peak is `P = max(O)`, positive duration is `L = count(O[t] > 0)`, and observed area is `A = sum(O[t])`.

The strength-zero reference leaves the supplied forecast unchanged: modeled burden `B₀ = F × D`. The illustrative intervention amplifies only positive excesses over the matched observed dimensions: `Fₛ = F + s × max(0, F − P)` and `Dₛ = D + s × max(0, D − L)`, where `s ∈ [0,1]` is an uncalibrated intervention setting. Per-event burden error is `Fₛ × Dₛ − A`; the primary metric is the running mean across unique matched events, in **intensity-steps per matched event**. The state carries event IDs, count, and cumulative error so chronological contexts contribute exactly once.

## Conditions and scenarios

The mechanism requires a nonempty event ID, a finite peak on the 0–10 scale, a positive integer forecast duration, and a nonempty complete trajectory of finite 0–10 intensities with only trailing zeroes after response cessation. The trajectory must be a suitable comparison for that particular forecast; absent or invalid evidence is rejected, not treated as no bias. The strength-zero reference is an explicit unamplified forecast policy, not an assertion of perfect rationality.

The positive scenario contains two distinct matched emotional courses for which forecast peak and duration both exceed their observed counterparts; strength .8 therefore raises modeled burden error relative to strength zero. The boundary scenario contains two courses where forecast peak and duration do not exceed observed values, so the necessary overestimation condition is absent and intervention equals the reference. Both contexts are chronological and state records each matched event.

## Assumptions and limitations

Peak, duration, discrete time steps, and intensity-times-duration burden are simplified user-set task variables. The separate peak/duration amplification and linear strength response are illustrative assumptions, not published effect sizes, calibrated coefficients, or an empirical claim. Trajectory comparisons may be unsuitable across different people, emotion types, contexts, or events, and this model omits those factors, expectation calibration, and possible underestimation. A large emotional forecast or observed response alone does not establish impact bias. The module consumes structured, explicitly matched inputs; it is not a text detector, diagnosis, or population model. Passing software checks is not empirical validation.
