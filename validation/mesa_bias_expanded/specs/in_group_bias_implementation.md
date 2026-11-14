# In-group Bias — illustrative mechanism

This plugin models one narrow task: choosing one candidate for a credibility or evaluation decision from supplied structured qualification scores and explicit shared-group tags. For candidate *i*, it computes

`adjusted_i = qualification_i + strength × group_bonus × 1[same_group_i]`.

The strength-zero reference policy selects the candidate with the highest supplied qualification score; original list order resolves ties. The plugin reports the chosen candidate's **qualification points on the input 0–100 scale**, not the adjusted score. Thus the metric reveals when a group-driven choice selects a less-qualified candidate while leaving the qualification evidence itself distinct from the assumed preference. The supplied `group_bonus` is an illustrative score-point assumption, not an estimated effect size.

The necessary condition is an explicit difference in shared-group membership between candidates. With no in-group candidate (or no out-group comparison), the bonus cannot change the ranking relative to the reference; the required boundary scenario includes no in-group candidate. In the positive example, an 82-point in-group candidate competes with a 90-point out-group candidate, with a 15-point bonus: at strength 0.8 the adjusted in-group score is 94 and the choice shifts, so the reported metric falls from 90 to 82.

This is a synthetic choice process, not an NLP detector, empirical psychology model, or claim about populations. It presumes the task's scores, candidate list, and group memberships are valid and comparable. Group membership could correlate with relevant qualifications not represented by the supplied score, so observed unequal treatment alone does not establish bias; real decisions can include context, uncertainty, procedural safeguards, and legitimate eligibility differences absent here. Tests check software behavior and the stated arithmetic only, not empirical validity.
