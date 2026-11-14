# AI Literacy Gap — illustrative mechanism

## Process and measure

For one task, the inputs are explicit hypothetical AI comfort `C`, AI competence `K`, task-specific AI advantage `A` over the non-AI option, and the task's validation demand `D`. At strength `s`, the model sets perceived validation capacity to `K* = min(1, K + s·max(0, C−K))`. It selects AI only if `A > 0` and `K* ≥ D`. The primary metric is **unverified AI reliance per task step**, `1` when AI is selected while `K < D`, and `0` otherwise. The trace reports the reference choice, adjusted capacity, actual choice and metric. State counts rounds, AI selections and unverified selections and records the last choice.

## Reference and necessary conditions

At `s=0`, the stated reference policy uses actual competence: select AI if and only if `A > 0` and `K ≥ D`. This is a simple task-specific reference, not a claim of perfect rationality. A positive unverified-reliance effect requires (i) a comfort-over-competence gap, (ii) a positive AI advantage, (iii) competence below validation demand, and (iv) the strength-adjusted capacity to meet that demand. Frequent use is optional context only and never substitutes for competence evidence. Missing required measurements and out-of-range values raise `ValueError`.

## Scenarios and assumptions

The positive scenario uses `C=.9`, `K=.4`, `A=.5`, `D=.7`: at `s=.8`, `K*=.8` and the model selects AI despite insufficient actual validation competence; the reference does not. The boundary scenario has no comfort-competence gap (`C=K=.6`) despite `use_frequency=1`; with `D=.8`, neither policy selects AI, so the primary metric is equal to baseline. Coefficients, scales and task advantage are illustrative user-settable assumptions, not measured effect sizes.

## Limitations

This is a compact synthetic one-step choice model, not an empirically validated psychology theory, classifier, diagnosis, or population estimate. It does not infer literacy from frequency or language, model learning over time, or represent external verification, expert review, task-specific trust calibration, and other reasonable safeguards. Test success verifies code behavior only, not psychological validity or detection accuracy.
