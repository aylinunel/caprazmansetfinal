# Commitment bias — illustrative implementation

## Process and task

This synthetic sequential decision process chooses between **stay** and **exit** using supplied current prospective utility values. At strength zero the reference is `stay` iff `stay_value >= exit_value` (ties favor staying); otherwise it is `exit`. Past expenditure is not included. After a stay choice is explicitly announced, state records a public commitment and its round. On later decisions only, the modeled public-consistency credit is:

`credit = strength × 3.0 utility points × public_visibility`

The credit is added to current `stay_value` only when the state records a prior public commitment to stay **and** current evidence favors exit (`stay_value < exit_value`). The process chooses stay iff `stay_value + credit >= exit_value`. `public_visibility` is supplied in `[0, 1]`. `strength` is an intervention setting in `[0, 1]`, not prevalence or calibrated confidence. The primary metric is `stay_choice`: binary `1` for stay and `0` for exit, not a probability or accuracy estimate. `active` indicates whether this step's choice differs from the strength-zero reference.

## Scenarios and necessary conditions

The positive sequence first chooses and announces stay (values 4 versus 2), then faces adverse comparative evidence (3 versus 4) with full visibility. At strength 0.8 the illustrative credit is 2.4, making adjusted stay value 5.4, so the final choice remains stay; at strength zero it exits. The boundary sequence is identical except the first stay was not publicly announced. Since the necessary prior public commitment is absent, its later choice equals the reference at both strengths. Removing visibility likewise removes the modeled effect.

## Assumptions and limitations

The 3.0-point consistency utility is a transparent illustrative parameter, not a published effect size or fitted coefficient. The model covers maintenance of a prior public commitment, not escalation, hidden motives, free-text detection, or population behavior. Supplied utilities may omit legitimate switching costs, information quality, or other reasons to stay; the process infers none of these. Public consistency is deliberately distinct from an appeal to unrecoverable expenditure. This implementation is synthetic-only and explicitly **not empirically validated**; software tests establish behavior of the code, not psychological validity or detection accuracy.
