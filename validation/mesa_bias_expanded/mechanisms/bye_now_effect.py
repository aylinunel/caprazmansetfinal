"""Illustrative, explicitly hypothetical bye-to-buy sound-priming process."""

from copy import deepcopy
import math


# All coefficients are transparent modeling assumptions, not empirical estimates.
_RETENTION = 0.5
_MAX_SOUND_UTILITY_SHIFT = 0.75

METADATA = {
    "id": "bye_now_effect",
    "name": "Bye-Now Effect",
    "kind": "cognitive_bias",
    "description": (
        "A hypothetical residual sound-activation state raises the supplied utility "
        "of an explicitly sound-linked purchase option after explicit bye exposure."
    ),
    "required_inputs": ["bye_exposure", "options"],
    "state_fields": ["activation", "cumulative_spend", "last_choice", "exposure_count"],
    "metric_name": "selected_option_spend",
    "metric_units": "nonnegative currency units spent in the current choice step",
    "assumptions": [
        "Exposure and sound association are supplied as structured facts, not inferred from text.",
        "Activation decays by one half per step and a fully activated option can gain at most 0.75 utility units at strength 1.",
        "The reference policy selects the highest supplied utility; ties preserve option order.",
        "The numeric coefficients are illustrative and not fitted or empirically validated.",
    ],
    "limitations": [
        "This is a task-specific demonstration, not a detector, diagnosis, or population claim.",
        "The proposed bye/buy priming effect is explicitly hypothetical and empirically unvalidated.",
        "Utilities, explicit sound-association values, currency values, and decay are user-supplied assumptions.",
        "It omits context, individual differences, deliberation, and benign reasons for choosing to buy.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def _read_state(context):
    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dictionary")
    state = deepcopy(prior)
    activation = _finite_number(state.get("activation", 0.0), "state.activation")
    if not 0.0 <= activation <= 1.0:
        raise ValueError("state.activation must be within [0, 1]")
    cumulative_spend = _finite_number(state.get("cumulative_spend", 0.0), "state.cumulative_spend")
    if cumulative_spend < 0.0:
        raise ValueError("state.cumulative_spend must be nonnegative")
    exposure_count = state.get("exposure_count", 0)
    if isinstance(exposure_count, bool) or not isinstance(exposure_count, int) or exposure_count < 0:
        raise ValueError("state.exposure_count must be a nonnegative integer")
    last_choice = state.get("last_choice")
    if last_choice is not None and not isinstance(last_choice, str):
        raise ValueError("state.last_choice must be a string or None")
    state.update(
        activation=activation,
        cumulative_spend=cumulative_spend,
        last_choice=last_choice,
        exposure_count=exposure_count,
    )
    return state


def _validate_options(options):
    if not isinstance(options, list) or not options:
        raise ValueError("options must be a nonempty list")
    validated = []
    seen_ids = set()
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f"options[{index}] must be a dictionary")
        option_id = option.get("id")
        if not isinstance(option_id, str) or not option_id:
            raise ValueError(f"options[{index}].id must be a nonempty string")
        if option_id in seen_ids:
            raise ValueError("option ids must be unique")
        seen_ids.add(option_id)

        utility = _finite_number(option.get("utility"), f"options[{index}].utility")
        price = _finite_number(option.get("price"), f"options[{index}].price")
        if price < 0.0:
            raise ValueError(f"options[{index}].price must be nonnegative")
        purchase = option.get("purchase")
        if not isinstance(purchase, bool):
            raise ValueError(f"options[{index}].purchase must be boolean")
        sound_association = _finite_number(
            option.get("sound_association"), f"options[{index}].sound_association"
        )
        if not 0.0 <= sound_association <= 1.0:
            raise ValueError(f"options[{index}].sound_association must be within [0, 1]")
        if sound_association > 0.0 and not purchase:
            raise ValueError("a sound-associated buy target must be a purchase option")
        validated.append(
            {
                "id": option_id,
                "utility": utility,
                "price": price,
                "purchase": purchase,
                "sound_association": sound_association,
            }
        )
    return validated


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one chronological choice step without mutating the supplied context."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number within [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number within [0, 1]")
    if "bye_exposure" not in context:
        raise ValueError("missing required input: bye_exposure")
    if not isinstance(context["bye_exposure"], bool):
        raise ValueError("bye_exposure must be boolean")
    if "options" not in context:
        raise ValueError("missing required input: options")

    state = _read_state(context)
    options = _validate_options(context["options"])

    # A real chronology: activation from earlier exposure is retained, while each
    # explicit current-step exposure refreshes it to 1.
    activation_before = state["activation"]
    activation = min(1.0, _RETENTION * activation_before + (1.0 if context["bye_exposure"] else 0.0))
    exposure_count = state["exposure_count"] + int(context["bye_exposure"])

    # Strength zero is the stated reference: highest supplied base utility.
    # The proposed effect adds only an explicit bye-linked sound-association term.
    baseline = max(options, key=lambda item: item["utility"])
    adjusted = max(
        options,
        key=lambda item: item["utility"]
        + strength * _MAX_SOUND_UTILITY_SHIFT * activation * item["sound_association"],
    )
    spend = adjusted["price"] if adjusted["purchase"] else 0.0
    cumulative_spend = state["cumulative_spend"] + spend
    if not math.isfinite(spend) or not math.isfinite(cumulative_spend):
        raise ValueError("computed spend must remain finite")

    next_state = deepcopy(state)
    next_state.update(
        activation=activation,
        cumulative_spend=cumulative_spend,
        last_choice=adjusted["id"],
        exposure_count=exposure_count,
    )
    changed_choice = adjusted["id"] != baseline["id"]
    trace = [
        f"activation=min(1, 0.5*{activation_before:g} + exposure({int(context['bye_exposure'])}))={activation:g}; "
        f"exposure_count={exposure_count}.",
        f"Reference choice maximizes supplied utility: {baseline['id']} ({baseline['utility']:g}); "
        f"effect choice maximizes utility + strength({strength:g})*0.75*activation*sound_association: "
        f"{adjusted['id']} (adjusted utility "
        f"{adjusted['utility'] + strength * _MAX_SOUND_UTILITY_SHIFT * activation * adjusted['sound_association']:g}).",
        f"Current-step spend={spend:g}; active={changed_choice} because choice "
        f"{'changed' if changed_choice else 'did not change'} from the strength-zero reference.",
    ]
    return {"metric": spend, "active": changed_choice, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    """Return compact, chronological positive and necessary-condition boundary cases."""
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "bye_exposure": True,
                    "options": [
                        {"id": "wait", "utility": 0.0, "price": 0.0, "purchase": False, "sound_association": 0.0}
                    ],
                },
                {
                    "bye_exposure": False,
                    "options": [
                        {"id": "wait", "utility": 0.0, "price": 0.0, "purchase": False, "sound_association": 0.0},
                        {"id": "buy_item", "utility": -0.2, "price": 20.0, "purchase": True, "sound_association": 1.0},
                    ],
                },
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "bye_exposure": False,
                    "options": [
                        {"id": "wait", "utility": 0.0, "price": 0.0, "purchase": False, "sound_association": 0.0},
                        {"id": "buy_item", "utility": -0.2, "price": 20.0, "purchase": True, "sound_association": 1.0},
                    ],
                },
                {
                    "bye_exposure": False,
                    "options": [
                        {"id": "wait", "utility": 0.0, "price": 0.0, "purchase": False, "sound_association": 0.0},
                        {"id": "buy_item", "utility": -0.2, "price": 20.0, "purchase": True, "sound_association": 1.0},
                    ],
                },
            ],
            "expectation": "equal",
        },
    ]
