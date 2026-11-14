"""The two detector configurations the lab compares.

baseline  = the production catalogue, unchanged.
candidate = baseline plus every lab-only proposed card. Proposed cards never enter
            biasguard/data/cards.json from here.
"""
from __future__ import annotations

import json
from pathlib import Path

from biasguard.catalog import card_hash, load_cards, validate_cards
from biasguard.providers import PROMPTS_VERSION

from . import crosswalk

PROPOSED_DIR = Path(__file__).with_name("proposed_cards")
CONFIGS = ("baseline", "candidate")


def _proposed() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(PROPOSED_DIR.glob("*.json"))]


def catalog(config: str) -> list[dict]:
    if config not in CONFIGS:
        raise ValueError(f"unknown lab config: {config}")
    cards = load_cards()
    return cards if config == "baseline" else validate_cards(cards + _proposed())


def target(simulation_id: str, config: str) -> str | None:
    resolved = crosswalk.resolve(simulation_id)
    if resolved or config == "baseline":
        return resolved
    proposed = simulation_id.replace("_", "-")
    return proposed if proposed in {c["id"] for c in _proposed()} else None


def manifest(config: str) -> dict:
    cards = catalog(config)
    return {"config": config, "card_hash": card_hash(cards), "prompts_version": PROMPTS_VERSION,
            "card_count": len(cards),
            "proposed_card_ids": [c["id"] for c in _proposed()] if config == "candidate" else []}
