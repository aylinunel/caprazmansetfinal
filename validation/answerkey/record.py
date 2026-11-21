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


def check_slot(coder: str) -> None:
    if not _SLOT.fullmatch(coder):
        raise ValueError(f"coder slot {coder!r} must be a letter and a digit, e.g. A1")


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


def allowed(categories) -> dict:
    return {"blame_level": BLAME_LEVELS + (UNSURE,), "present": ("yes", "no", UNSURE),
            "frame_category": tuple(categories) + (UNSURE,)}


def _check(c: Coding, categories: list[str]) -> None:
    try:
        check_slot(c.coder)
    except ValueError as e:
        raise ValueError(f"{e} ({c.item})") from None
    if c.field not in FIELDS:
        raise ValueError(f"unknown field {c.field!r} ({c.item})")
    if c.value not in allowed(categories)[c.field]:
        raise ValueError(f"value {c.value!r} not allowed for {c.field} ({c.item})")


def append(codings: list[Coding], path: Path = CODINGS) -> int:
    """Add records not yet present; raise ValueError (writing nothing) on a bad slot/value or a changed answer."""
    categories = load_codebook()["categories"]
    seen = {(c.item, c.coder, c.field): c.value for c in read(path)}
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
            f.write("".join(json.dumps(asdict(c), ensure_ascii=False) + "\n" for c in new))
    return len(new)


def from_core(core: dict, codebook: dict) -> list[Coding]:
    """Existing human narrative coding as slot CORE_SLOT (derived, never stored)."""
    return [Coding(f"{r['key']}__{r['s']}", CORE_SLOT, f, v) for r in human_rows(core)
            for f, v in (("blame_level", blame_level(r.get("blame", ""))),
                         ("frame_category", frame_category(r.get("frame", ""), codebook)))]


def _by_item(codings, field) -> dict[str, dict[str, str]]:
    d: dict[str, dict[str, str]] = {}
    for c in codings:
        if c.field == field:
            slot = d.setdefault(c.item, {})
            if slot.get(c.coder, c.value) != c.value:
                raise ValueError(f"{c.item}: slot {c.coder} has two values for {c.field}: {slot[c.coder]!r} and {c.value!r}")
            slot[c.coder] = c.value
    return d


def agreement(codings, field) -> dict:
    by_item = _by_item(codings, field)
    u = [[None if v == UNSURE else v for _, v in sorted(s.items())] for s in by_item.values()]
    double = [ks for ks in ({k for k, v in s.items() if v != UNSURE} for s in by_item.values()) if len(ks) >= 2]
    alpha = krippendorff_alpha(u)
    kind = None if not double else ("same coder" if len({k[0] for ks in double for k in ks}) == 1 else "between coders")
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
