# Ostrich Effect — illustrative implementation

## Process and task measure

For each supplied report, the reference policy reads when its explicit task decision value is at least its reading cost. The intervention changes only that selection rule: for information explicitly marked threatening, and absent an explicitly justified practical delay, the read score becomes `decision_value - strength × discomfort`; the report is read when this score is at least `read_cost`. Thus avoidance is a choice to forgo information in a stated scenario, not a belief that the threat is absent. Strength in `[0, 1]` is an uncalibrated intervention setting, not a probability or empirical effect size. A choice counts as an active mechanism event only when this term flips a reference read into avoidance.

The primary metric is cumulative `decision_value` for reports read, in hypothetical task-utility points of information accessed. State carries cumulative accessed value, reports read, and mechanism-induced avoidance choices across chronological report contexts. The zero-strength comparator uses the same task inputs and reads at value-cost ties; it is an explicit reference rule, not a claim of perfect rationality.

## Required inputs and scenarios

`METADATA.required_inputs` contains the single common top-level key `information`. Each phase validates the nested fields `decision_value` (finite, nonnegative number), `read_cost` (finite, nonnegative number), `threatening` (boolean), `discomfort` (finite, nonnegative number), and `practical_delay` (boolean). The positive scenario supplies three threatening, uncomfortable reports for which reference reading is flipped at strength 0.8. The boundary scenario supplies uncomfortable but nonthreatening information; removing threat removes a necessary condition and yields equality with strength zero. The process also bypasses its term for an explicitly justified practical delay.

## Assumptions and limitations

All utility quantities are hypothetical and treated as commensurable. Structured inputs stand in for explicit simulated task facts; the mechanism does not infer a person's threat appraisal, motive, diagnosis, or beliefs from text. The model does not cover broader coping, incentives, social context, uncertainty, or downstream outcomes. It is an illustrative narrow process model only; neither software tests nor scenario direction establish empirical validity, prevalence, or predictive accuracy.
