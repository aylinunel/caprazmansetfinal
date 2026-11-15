# Error analysis — 2026-11-14_behavioural_627740d135b3

Reviews are verify-pass labels: the reviewer saw the AI's finding first, and only shown findings can be
reviewed. These numbers say nothing about findings the detector missed.

## Reviewed and unreviewed findings

| Tier | Kept | Rejected | Unreviewed |
|---|---|---|---|
| ai_confident | 0 | 0 | 257 |
| needs_human | 0 | 0 | 182 |

Events whose review failed: 0 of 150.

No finding has been reviewed yet, so there are no error clusters.

## Why findings stay uncertain

For each card: of the reviewer assessments that examined its conditions, how many left each
condition satisfied / unknown / contradicted. A condition that is mostly unknown asks for evidence a
headline and lede do not contain.

| Card | Assessments | Conditions (satisfied/unknown/contradicted) | Most-stuck condition |
|---|---|---|---|
| framing-effect | 250 | #1: 129/120/1; #2: 0/250/0; #3: 0/250/0 | #2: 250/250 not satisfied |
| salience-bias | 230 | #1: 2/228/0; #2: 0/230/0; #3: 32/198/0 | #2: 230/230 not satisfied |
| leveling-and-sharpening | 178 | #1: 164/14/0; #2: 0/176/2; #3: 22/156/0 | #2: 178/178 not satisfied |
| negativity-bias | 66 | #1: 1/65/0; #2: 0/64/2 | #2: 66/66 not satisfied |
| authority-bias | 60 | #1: 55/5/0; #2: 0/60/0; #3: 0/59/1 | #2: 60/60 not satisfied |
| in-group-bias | 50 | #1: 16/34/0; #2: 0/49/1; #3: 0/50/0 | #2: 50/50 not satisfied |
| affect-heuristic | 36 | #1: 0/36/0; #2: 0/36/0; #3: 0/36/0 | #1: 36/36 not satisfied |
| anchoring-bias | 34 | #1: 18/16/0; #2: 3/31/0; #3: 0/33/1 | #3: 34/34 not satisfied |
| source-confusion | 30 | #1: 8/22/0; #2: 1/29/0; #3: 0/30/0 | #3: 30/30 not satisfied |
| illusion-of-transparency | 20 | #1: 0/20/0; #2: 0/20/0; #3: 0/20/0 | #1: 20/20 not satisfied |
| ai-literacy-gap | 18 | #1: 1/17/0; #2: 0/18/0; #3: 0/18/0 | #2: 18/18 not satisfied |
| accountability-diffusion-in-ai | 16 | #1: 0/16/0; #2: 0/16/0; #3: 0/16/0 | #1: 16/16 not satisfied |
| action-bias | 16 | #1: 0/15/1; #2: 0/16/0; #3: 0/16/0 | #1: 16/16 not satisfied |
| ambiguity-effect | 16 | #1: 0/16/0; #2: 0/16/0; #3: 0/16/0 | #1: 16/16 not satisfied |
| incentivization | 14 | #1: 0/14/0; #2: 0/14/0; #3: 0/14/0 | #1: 14/14 not satisfied |
