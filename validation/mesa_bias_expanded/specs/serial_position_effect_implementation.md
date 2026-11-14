# Serial Position Effect: illustrative implementation

## Process and metric

The plugin stores each presented item and its one-based ordinal position in chronological state. A probe is accepted only after the entire declared list has been encoded and must name one of its items. For list length \(n\), it computes a combined edge kernel at each position \(p\):

\[
w_p = e^{-0.9(p-1)} + e^{-0.9(n-p)}, \qquad
z_p = w_p - \frac{1}{n}\sum_{j=1}^{n}w_j.
\]

The probe score is \(\sigma(s\cdot1.2\cdot z_p)\), where \(\sigma\) is the logistic function and \(s\in[0,1]\) is the intervention strength. The two terms encode the beginning and end contributions jointly; centering makes the effect relative to the list and avoids a generic uplift. This compact shape ordinarily raises edge-item scores relative to the midpoint. Coefficients are hypothetical assumptions, not estimated psychological effect sizes.

**Task and units:** score the model’s illustrative recallability for one specified item after a single complete ordered list. The metric is a unit-interval probability-like score, not a calibrated recall probability or observed recall outcome. A single list and probe are supported per state history.

## Reference and necessary conditions

At strength zero, the explicit reference policy assigns every presented target a score of 0.5, independent of position. It is a neutral comparator, not a claim of perfect recall or rationality. A serial-position contribution requires at least one position to differ from another; with a one-item list, the only position equals the list mean, so the centered positional term is exactly zero.

The positive scenario presents five distinct items in order and probes the first item, testing a beginning-of-list increase against the reference. The boundary scenario presents one item and probes it; because there is no positional variation, strength .8 and strength zero yield equal scores. Both scenarios contain chronological presentation and probe phases.

## Assumptions and limitations

The model combines primacy and recency as one umbrella serial-position pattern, consistent with the annotation boundary: it does not report them as independent findings or infer their causes. It assumes a fixed decaying edge-kernel shape and uses a logistic score only to keep values bounded. Real recall can depend on rehearsal, delay, list length, interference, distinctiveness, output order, task instructions, and individual differences; none are represented. The task has no empirical calibration, validation, detection accuracy, or population inference. The strength parameter is an uncalibrated intervention control, not confidence or prevalence. Software tests establish executable behavior only, not psychological validity.
