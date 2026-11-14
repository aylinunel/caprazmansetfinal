# Primacy effect implementation

This plugin models a narrow serial-position process in a hypothetical task: a reader forms one bounded numeric impression from a chronological sequence of supplied item scores. It is an illustrative process model, not a detector, diagnosis, population claim, or fitted account of memory or judgment.

For each item at ordinal position \(p\) in a declared sequence of length \(L\), the reference mass is \(b_p=e_p d_p\), where \(e_p\) is exposure and \(d_p\) is distinctiveness. With an explicit serial-order cue, the intervention mass is

\[
w_p=b_p\left(1+0.6s\frac{L-p}{L-1}\right),
\]

where \(s\in[0,1]\) is an uncalibrated intervention setting and 0.6 is a hypothetical coefficient. If the order cue is absent, the position term is zero. The reported metric after each observed item is the cumulative weighted mean \(\sum_p w_p x_p/\sum_p w_p\), where \(x_p\in[0,1]\) is its supplied score. State retains the chronological count and both reference and intervention sums/masses. The strength-zero policy is the same task's exposure- and distinctiveness-weighted mean without a serial-position bonus; it is not presumed perfectly rational.

The positive scenario has equal exposure and distinctiveness, an explicitly ordered sequence, and a high-scoring first item followed by lower-scoring items, so the intervention gives the early score greater influence. The boundary scenario removes the necessary serial-order cue while keeping item observations and all other inputs; its metric therefore equals the strength-zero reference. Contexts represent one successive observation each, and the runner executes exactly the declared sequence length.

Scores, exposure, distinctiveness, and order-cue availability are explicit structured task inputs. Exposure and distinctiveness affect the reference as well as the intervention, preventing them from being silently mistaken for primacy. The coefficient and strength are illustrative controls, not empirical effect sizes, calibrated confidence, prevalence, or evidence about any person. Distinctiveness, contextual meaning, rehearsal, recency, and other serial-position processes can produce different outcomes; this plugin isolates only an early-position weighting rule and does not claim that altered impressions are harmful or errors in every context. Software tests establish interface/process behavior only, not empirical validity.
