"""Illustrative, evidence-gated CSR contribution to product purchase appeal."""
from __future__ import annotations

import math


METADATA = {
    "id": "noble_edge_effect",
    "name": "Noble Edge Effect",
    "kind": "cognitive_bias",
    "description": (
        "When a product has explicit perceived CSR evidence, its CSR score adds "
        "to purchase appeal and can change which otherwise comparable option is selected. "
        "The process does not alter or imply sound quality."
    ),
    # These are the only top-level scenario fields present in every phase.
    "required_inputs": ["products", "focal_option"],
    "state_fields": ["selected_option", "focal_appeal", "csr_premium"],
    "metric_name": "focal_purchase_appeal",
    "metric_units": "illustrative utility points (quality points minus price disutility plus CSR premium)",
    "assumptions": [
        "The supplied perceived_csr_score and csr_evidence flag are hypothetical task inputs, not inferred from text or hidden motives.",
        "Reference appeal is quality_score - 0.35 * price_index; eligible CSR adds 20 * strength * perceived_csr_score.",
        "Utility coefficients and strength are illustrative intervention settings, not estimated or calibrated effect sizes.",
    ],
    "limitations": [
        "This is a compact synthetic choice model, not a detector, diagnosis, population estimate, or empirical claim.",
        "Ethical preference can be reasonable; the model treats favorable CSR weighting as the named effect, not as irrationality.",
        "No sound-quality inference follows from CSR; scores, evidence, price, and quality are stipulated inputs.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Score the listed options; CSR enters only with explicit evidence and score."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    for key in METADATA["required_inputs"]:
        if key not in context:
            raise ValueError(f"missing required task input {key}")

    products = context["products"]
    if not isinstance(products, list) or not products:
        raise ValueError("products must be a nonempty list")
    by_id = {}
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            raise ValueError(f"products[{index}] must be an object")
        for key in ("id", "quality_score", "price_index", "perceived_csr_score", "csr_evidence"):
            if key not in product:
                raise ValueError(f"products[{index}] missing {key}")
        identifier = product["id"]
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"products[{index}].id must be a nonempty string")
        if identifier in by_id:
            raise ValueError("product ids must be unique")
        quality = _finite_number(product["quality_score"], f"{identifier}.quality_score")
        price = _finite_number(product["price_index"], f"{identifier}.price_index")
        csr_score = _finite_number(product["perceived_csr_score"], f"{identifier}.perceived_csr_score")
        if not 0 <= quality <= 100:
            raise ValueError(f"{identifier}.quality_score must be in [0, 100]")
        if not 0 <= price <= 100:
            raise ValueError(f"{identifier}.price_index must be in [0, 100]")
        if not 0 <= csr_score <= 1:
            raise ValueError(f"{identifier}.perceived_csr_score must be in [0, 1]")
        if not isinstance(product["csr_evidence"], bool):
            raise ValueError(f"{identifier}.csr_evidence must be boolean")
        by_id[identifier] = (quality, price, csr_score, product["csr_evidence"])

    focal = context["focal_option"]
    if not isinstance(focal, str) or focal not in by_id:
        raise ValueError("focal_option must identify one supplied product")
    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be an object when supplied")

    # Same reference policy at every strength: quality minus price disutility.
    # Only an explicitly evidenced positive CSR signal contributes a preference premium.
    appeals = {}
    for identifier, (quality, price, csr_score, has_evidence) in by_id.items():
        premium = 20.0 * strength * csr_score if has_evidence else 0.0
        appeals[identifier] = quality - 0.35 * price + premium
    chosen = max(by_id, key=lambda identifier: (appeals[identifier], identifier == focal))
    quality, price, csr_score, has_evidence = by_id[focal]
    focal_premium = 20.0 * strength * csr_score if has_evidence else 0.0
    focal_appeal = quality - 0.35 * price + focal_premium
    active = bool(has_evidence and csr_score > 0 and strength > 0)
    return {
        "metric": focal_appeal,
        "active": active,
        "state": {
            "selected_option": chosen,
            "focal_appeal": focal_appeal,
            "csr_premium": focal_premium,
        },
        "trace": [
            f"For each option, appeal = quality_score - 0.35*price_index + 20*strength*perceived_csr_score when csr_evidence is true (otherwise premium=0); selected {chosen!r} with appeal {appeals[chosen]:.6g}.",
            f"Focal option {focal!r} has appeal {focal_appeal:.6g} and CSR premium {focal_premium:.6g}; CSR changes preference only and is not used as sound-quality evidence.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "focal_option": "ethical",
                "products": [
                    {"id": "ethical", "quality_score": 70, "price_index": 20,
                     "perceived_csr_score": 0.9, "csr_evidence": True},
                    {"id": "alternative", "quality_score": 72, "price_index": 20,
                     "perceived_csr_score": 0.0, "csr_evidence": False},
                ],
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "focal_option": "ethical",
                "products": [
                    # Required CSR evidence is removed: no score can affect appeal.
                    {"id": "ethical", "quality_score": 70, "price_index": 20,
                     "perceived_csr_score": 0.0, "csr_evidence": False},
                    {"id": "alternative", "quality_score": 72, "price_index": 20,
                     "perceived_csr_score": 0.0, "csr_evidence": False},
                ],
            }],
            "expectation": "equal",
        },
    ]
