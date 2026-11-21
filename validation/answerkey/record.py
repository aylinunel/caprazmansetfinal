"""Answer-key record: human codings by coder slot, gold labels and agreement."""
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .agreement import krippendorff_alpha, percent_agreement
from .codebook import BLAME_LEVELS, blame_level, frame_category, human_rows, load_codebook

FIELDS = ("blame_level", "frame_category", "present")
CORE_SLOT = "A1"
CODINGS = Path(__file__).resolve().parents[1] / "reference" / "answerkey" / "codings.jsonl"
UNSURE = "unsure"
_SLOT = re.compile(r"[A-Z][1-9]")
MIN_ITEMS, MIN_ALPHA = 30, 0.67


@dataclass(frozen=True, order=True)
class Coding:
    item: str
    coder: str
    field: str
    value: str


def read(path: Path = CODINGS) -> list[Coding]:
    p = Path(path)
    if not p.exists():
        return []
    return [Coding(**json.loads(line)) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _check(c: Coding, categories: list[str]) -> None:
    if not _SLOT.fullmatch(c.coder):
        raise ValueError(f"coder slot {c.coder!r} must be a letter and a digit, e.g. A1 ({c.item})")
    if c.field not in FIELDS:
        raise ValueError(f"unknown field {c.field!r} ({c.item})")
    allowed = {"blame_level": BLAME_LEVELS + (UNSURE,), "present": ("yes", "no", UNSURE),
               "frame_category": tuple(categories) + (UNSURE,)}[c.field]
    if c.value not in allowed:
        raise ValueError(f"value {c.value!r} not allowed for {c.field} ({c.item})")


def append(codings: list[Coding], path: Path = CODINGS) -> int:
    """Add records not yet present; raise ValueError (writing nothing) on a bad slot/value or a changed answer."""
    categories = load_codebook()["categories"]
    existing = read(path)
    seen = {(c.item, c.coder, c.field): c.value for c in existing}
    new: list[Coding] = []
    for c in codings:
        _check(c, categories)
        key = (c.item, c.coder, c.field)
        if key in seen:
            if seen[key] != c.value:
                raise ValueError(f"{c.item}: slot {c.coder} already coded {c.field} as {seen[key]!r}, not {c.value!r}")
            continue
        seen[key] = c.value
        new.append(c)
    if new:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            for c in new:
                f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    return len(new)


def from_core(core: dict, codebook: dict) -> list[Coding]:
    """Existing human narrative coding as slot CORE_SLOT (derived, never stored)."""
    out = []
    for r in human_rows(core):
        item = f"{r['key']}__{r['s']}"
        out.append(Coding(item, CORE_SLOT, "blame_level", blame_level(r.get("blame", ""))))
        out.append(Coding(item, CORE_SLOT, "frame_category", frame_category(r.get("frame", ""), codebook)))
    return out


def _by_item(codings, field) -> dict[str, dict[str, str]]:
    d: dict[str, dict[str, str]] = {}
    for c in codings:
        if c.field == field:
            slot = d.setdefault(c.item, {})
            if slot.get(c.coder, c.value) != c.value:
                raise ValueError(f"{c.item}: slot {c.coder} has two values for {c.field}: {slot[c.coder]!r} and {c.value!r}")
            slot[c.coder] = c.value
    return d


def units(codings, field) -> dict[str, list[str | None]]:
    return {i: [None if v == UNSURE else v for _, v in sorted(s.items())] for i, s in _by_item(codings, field).items()}


def agreement(codings, field) -> dict:
    by_item = _by_item(codings, field)
    double = {i: {k: v for k, v in s.items() if v != UNSURE} for i, s in by_item.items()}
    double = {i: s for i, s in double.items() if len(s) >= 2}
    u = list(units(codings, field).values())
    alpha = krippendorff_alpha(u)
    letters = {k[0] for s in double.values() for k in s}
    kind = None if not double else ("same coder" if len(letters) == 1 else "between coders")
    return {"items_double": len(double), "alpha": alpha, "percent": percent_agreement(u), "kind": kind,
            "usable": len(double) >= MIN_ITEMS and alpha is not None and alpha >= MIN_ALPHA}


def gold(codings, field) -> tuple[dict[str, str], list[str]]:
    agreed, disputed = {}, []
    for i, s in sorted(_by_item(codings, field).items()):
        vals = {v for v in s.values() if v != UNSURE}
        if len(vals) == 1:
            agreed[i] = vals.pop()
        elif vals:
            disputed.append(i)
    return agreed, disputed
