# Illusion of Control — illustrative implementation

## Process and observable

This hypothetical task asks an agent to choose among discrete effort levels to improve a valued outcome. Each candidate effort `e` has linear effort cost `c*e`, outcome value `v`, and actual outcome-probability effect per effort `a`. The strength-zero reference chooses the available effort maximizing `v*a*e - c*e`, with ties broken toward lower effort.

The modeled illusion is deliberately narrow: it can change the decision estimate only when the action has **zero actual causal effect** (`a == 0`) and the supplied explicit perceived effect `p` is greater than zero. In that case, estimated efficacy is `a + strength*(p-a)`; otherwise it remains `a`. The selected effort maximizes `v*estimated_efficacy*e - c*e`, again breaking ties toward lower effort. The primary metric is selected effort in effort units. State retains chronological decisions, cumulative effort, and the last choice and utility values. This is a real choice-rule change under explicit hypothetical evidence, not a language detector or a general belief offset.

## Scenarios and boundary

The positive example offers effort levels `[0, 1, 2]`, no actual effect, perceived efficacy `0.4`, outcome value `100`, and per-unit cost `30`. With strength `0.8`, the estimated efficacy is `0.32`, making the marginal estimated return `32-30=2`; effort 2 is selected, versus effort 0 under the reference. The boundary example supplies positive actual efficacy (`0.4`), so the action really can influence the outcome. This removes the necessary no-causal-influence condition; the false-efficacy rule is suppressed and the choice equals the strength-zero reference.

## Assumptions and limitations

Effort levels are feasible, efficacy is a per-effort increase in outcome probability, and the supplied values and costs share commensurable utility units. The scenarios validate only the code's behavior under these stipulated inputs. Strength is an uncalibrated intervention parameter, not a confidence, prevalence, or effect-size estimate. The model cannot determine whether a real person's control belief is mistaken, infer causal structure, accommodate unmodeled causal pathways, or represent richer uncertainty, feedback, social context, or nonlinear effort. An observed high-effort choice could have many benign or rational explanations. This synthetic mechanism makes no empirical validity or diagnostic claim.
