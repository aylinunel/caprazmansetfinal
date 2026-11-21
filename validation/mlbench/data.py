"""Human-coded headline rows as learning examples."""
from dataclasses import dataclass

from validation.answerkey.codebook import blame_level, frame_category, human_rows


@dataclass(frozen=True)
class Row:
    group: str
    outlet: str
    text: str
    blame_level: str
    frame_category: str


def rows(core: dict, codebook: dict) -> list[Row]:
    return [Row(r["key"], r["s"], r["hl"], blame_level(r.get("blame")), frame_category(r.get("frame"), codebook))
            for r in human_rows(core) if (r.get("hl") or "").strip()]
