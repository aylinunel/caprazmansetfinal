# Planning Fallacy: illustrative implementation

## Process and task measure

This hypothetical task model forecasts completion hours. For a current task with explicit class `c` and inside-view plan `P`, it finds previous completed tasks of exactly that class in the agent's chronological state. For each, it computes `actual_hours / planned_hours`; let `R` be the median of those ratios. The mechanism is active only when at least one comparable task exists and `R > 1`, a concrete record of underestimation rather than a short plan by itself. In that case its strength-`s` forecast is

`forecast = P × [1 + (1 − s) × (R − 1)]`.

At strength zero this is the explicit outside-view reference policy: apply the full observed same-class median ratio to the current plan. Increasing strength discounts this correction and retains more of the current inside-view plan. With no comparable overrun evidence, the forecast is `P` at every strength. The primary metric is `max(0, actual_hours − forecast)` in hours: the amount by which the supplied realized duration exceeds the forecast, floored at zero. Realized duration scores the hypothetical forecast and enters history only after that task step; it does not determine that step's forecast. Each step carries task-class, planned, and realized records forward in state.

## Evidence boundary and scenarios

Required task fields are `task_class`, `planned_hours`, and `actual_hours` in every phase. The positive scenario first records a small-software-change planned at 8 hours and realized at 12, then estimates a same-class task at 20 hours with a 30-hour realization. Its prior ratio is 1.5; strength .8 forecasts 22 hours and produces an 8-hour undershoot, while strength zero forecasts 30 and produces none. The boundary scenario records an overrun only for a different class before the 20-hour software-change plan. With no same-class experience, it forecasts the plan at both strengths and has equal metrics. This boundary removes the necessary comparable-history condition rather than forcing a zero result.

## Assumptions and limitations

Task classes are supplied hypothetical labels, not inferred from text. The same-class median is a deliberately simple outside-view reference and may not predict future tasks; one past case can be unrepresentative, and classes can be misspecified. Strength is an uncalibrated intervention knob, not confidence, prevalence, or an empirical effect size. This compact model is not a detector, diagnosis, population claim, or empirically validated account of human planning.
