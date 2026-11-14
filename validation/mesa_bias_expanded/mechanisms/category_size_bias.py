"""Illustrative category-to-member probability substitution; not a detector."""
import math
from copy import deepcopy
from numbers import Real


METADATA = {
    "id": "category_size_bias",
    "name": "Category Size Bias",
    "kind": "cognitive_bias",
    "description": (
        "Models an individual outcome being judged by its category's aggregate "
        "probability, despite equal supplied probabilities for individual outcomes."
    ),
    "required_inputs": ["outcomes", "focal_outcome_id"],
    "state_fields": ["steps", "last_judged_probability", "last_reference_probability"],
    "metric_name": "judged_probability_of_focal_individual",
    "metric_units": "probability from 0 to 1, not the aggregate category probability",
    "assumptions": [
        "The outcomes list exhaustively partitions a single mutually exclusive outcome space; each outcome has a unique id, category_id, and supplied individual probability.",
        "Individual probabilities are externally supplied and sum to one. Category probability is their sum within that category.",
        "The strength-zero reference reports the focal individual's supplied probability. When all individual probabilities are equal, the illustrative bias interpolates toward reporting its category's aggregate probability as if it were the individual's probability.",
        "If individual probabilities are not all equal, the necessary equal-individual-probability condition is absent and the model reports the supplied focal probability at every strength.",
        "Strength is a user-settable illustrative intervention parameter, not an estimated effect size or prevalence.",
    ],
    "limitations": [
        "This is a hypothetical process model, not empirically validated and not a claim about actual people or populations.",
        "It assumes the outcome space and category assignments are complete and correct; it does not infer them from language or establish that a real judgment occurred.",
        "It represents one category-to-member substitution only; it omits uncertainty, task incentives, learning, and alternative interpretations of the question.",
        "A larger category can genuinely have greater aggregate probability. Only reporting that aggregate as the chance of one equally likely member is treated as the modeled error.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicit categorical outcome space without mutating inputs."""
    s = _finite_number(strength, "strength")
    if not 0.0 <= s <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required inputs: {', '.join(missing)}")

    outcomes = context["outcomes"]
    if not isinstance(outcomes, list) or len(outcomes) < 2:
        raise ValueError("outcomes must be a list with at least two individuals")
    identifiers = []
    categories = []
    probabilities = []
    for index, outcome in enumerate(outcomes):
        if not isinstance(outcome, dict):
            raise ValueError(f"outcomes[{index}] must be a dictionary")
        outcome_id = outcome.get("id")
        category_id = outcome.get("category_id")
        if not isinstance(outcome_id, str) or not outcome_id.strip():
            raise ValueError(f"outcomes[{index}].id must be a non-empty string")
        if not isinstance(category_id, str) or not category_id.strip():
            raise ValueError(f"outcomes[{index}].category_id must be a non-empty string")
        if "individual_probability" not in outcome:
            raise ValueError(f"outcomes[{index}] is missing individual_probability evidence")
        probability = _finite_number(
            outcome["individual_probability"], f"outcomes[{index}].individual_probability"
        )
        if not 0.0 <= probability <= 1.0:
            raise ValueError("individual_probability values must be in [0, 1]")
        identifiers.append(outcome_id)
        categories.append(category_id)
        probabilities.append(probability)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("outcome ids must be unique")
    if not math.isclose(math.fsum(probabilities), 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("individual_probability values must sum to 1")

    focal_id = context["focal_outcome_id"]
    if not isinstance(focal_id, str) or focal_id not in identifiers:
        raise ValueError("focal_outcome_id must identify a supplied individual outcome")
    focal_index = identifiers.index(focal_id)
    focal_probability = probabilities[focal_index]
    focal_category = categories[focal_index]
    category_probability = math.fsum(
        probability
        for category, probability in zip(categories, probabilities)
        if category == focal_category
    )
    equal_individual_chances = all(
        math.isclose(probability, probabilities[0], rel_tol=1e-12, abs_tol=1e-12)
        for probability in probabilities[1:]
    )

    # A category's aggregate mass is substituted for a member's chance only if
    # the specified necessary condition (equal chances for individuals) holds.
    # Otherwise the reference probability is preserved, not distorted.
    if equal_individual_chances:
        metric = (1.0 - s) * focal_probability + s * category_probability
    else:
        metric = focal_probability
    active = equal_individual_chances and not math.isclose(
        category_probability, focal_probability, rel_tol=1e-12, abs_tol=1e-12
    ) and s != 0.0

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dictionary")
    steps = prior.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    next_state = deepcopy(prior)
    next_state.update({
        "steps": steps + 1,
        "last_judged_probability": metric,
        "last_reference_probability": focal_probability,
        "last_category_probability": category_probability,
        "last_equal_individual_chances": equal_individual_chances,
    })
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            "Reference rule: judged probability of the focal individual equals its supplied individual_probability.",
            "When all individual chances are equal, category-size substitution is "
            "metric = (1-strength)*focal_individual_probability + "
            "strength*sum(probabilities in focal category); when chances are unequal, "
            "the necessary condition is absent and the reference is used unchanged.",
            f"Focal={focal_id!r} in category={focal_category!r}; individual="
            f"{focal_probability:.12g}, category aggregate={category_probability:.12g}, "
            f"equal_individual_chances={equal_individual_chances}, strength={s:g}, "
            f"metric={metric:.12g}, active={active}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"steps": 0},
            "contexts": [{
                "outcomes": [
                    {"id": "a1", "category_id": "large", "individual_probability": 0.2},
                    {"id": "a2", "category_id": "large", "individual_probability": 0.2},
                    {"id": "a3", "category_id": "large", "individual_probability": 0.2},
                    {"id": "b1", "category_id": "small", "individual_probability": 0.2},
                    {"id": "b2", "category_id": "small", "individual_probability": 0.2},
                ],
                "focal_outcome_id": "a1",
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"steps": 0},
            # Unequal individual chances remove the specified necessary condition;
            # category aggregation remains distinct from the focal chance.
            "contexts": [{
                "outcomes": [
                    {"id": "a1", "category_id": "large", "individual_probability": 0.4},
                    {"id": "a2", "category_id": "large", "individual_probability": 0.3},
                    {"id": "b1", "category_id": "small", "individual_probability": 0.2},
                    {"id": "b2", "category_id": "small", "individual_probability": 0.1},
                ],
                "focal_outcome_id": "a1",
            }],
            "expectation": "equal",
        },
    ]
