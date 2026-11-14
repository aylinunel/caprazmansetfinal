# Bundling Bias — illustrative mechanism note

## Process and metric

This single-step choice model asks whether a person uses one component after purchasing a bundle. The reference policy uses the component exactly when its stated use value is at least its marginal component price: `reference_use = 1[value >= component_marginal_price]`. The bias process is eligible only if a bundle was purchased, it contains the component, it has at least two components, and its total price exceeds the component's marginal price. When eligible, the perceived hurdle is `component_marginal_price + strength × (bundle_price - component_marginal_price)`; otherwise it remains the marginal price. The primary metric is the binary component-use decision (1 = use, 0 = do not use). `active` is true only when this choice differs from the reference. Strength zero therefore reproduces the stated reference rule; strength is an illustrative model setting, not a prevalence or confidence estimate.

## Scenarios and necessary conditions

The positive example sets component value to 4, its marginal price to 2, and bundle price to 8. At strength 0.8, the hurdle is 6.8, so the model declines use whereas the reference chooses use. The boundary example retains a purchased multi-item package but removes the included-component condition; the model then exactly matches the reference at strength 0.8. Purchase alone, a single-item package, or no bundle price contrast also cannot activate the effect.

## Assumptions and limitations

This assumes an aggregate bundle price can overshadow the item's marginal price and be treated as the hurdle for that item. Prices and component use value are assumed commensurable; the threshold and linear interpolation are task-specific illustrative assumptions, not fitted or empirically validated parameters. Real bundles may instead lower perceived costs, encourage use through sunk-cost or value-seeking responses, or involve complementary components, usage intensity, budgets, and access constraints absent here. The module is an explanatory toy process, not a classifier, psychological diagnosis, or NLP detector. A bundle purchase is not by itself evidence of underuse or bias.
