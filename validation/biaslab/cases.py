"""Cases, families and expectations. Nothing here is visible to the detector except DetectorInput."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

KINDS = ("positive", "inactive_control", "boundary_control", "missing_context", "quoted_control")
PERTURBATIONS = ("none", "reverse_outlets", "relabel_outlets", "irrelevant_detail")
STATUSES = ("supported", "contextual_effect", "not_supported", "uncertain", "unassessed", "ineligible", "error")
_POSITIVE = frozenset({"supported", "contextual_effect"})


@dataclass(frozen=True)
class DetectorInput:
    text: str
    context: str = ""


@dataclass(frozen=True)
class Expected:
    acceptable: frozenset[str]
    forbidden: frozenset[str]


@dataclass(frozen=True)
class Case:
    case_id: str
    input: DetectorInput
    private: dict


def family_id(concept: str, facts: dict) -> str:
    canonical = json.dumps(facts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(f"{concept}\0{canonical}".encode("utf-8")).hexdigest()[:16]


def split_of(family: str) -> Literal["dev", "test"]:
    return "test" if int(family, 16) % 5 == 0 else "dev"


def case_id(input: DetectorInput, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}\0{input.text}\0{input.context}".encode("utf-8")).hexdigest()
    return "c-" + digest[:12]


def expected(kind: str, resolvable: bool) -> Expected:
    if kind not in KINDS:
        raise ValueError(f"unknown case kind: {kind}")
    if not resolvable:
        return Expected(frozenset({"ineligible"}), _POSITIVE | {"not_supported"})
    if kind == "positive":
        return Expected(_POSITIVE, frozenset())
    return Expected(frozenset({"not_supported", "uncertain"}), _POSITIVE)
