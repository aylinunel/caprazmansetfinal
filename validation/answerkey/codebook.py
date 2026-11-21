"""Narrative codebook: collapses free-text human narrative coding into two learnable targets."""
import json
from pathlib import Path

HUMAN_STATUSES = ("hand_coded", "headline_coded")
BLAME_LEVELS = ("none", "implied", "explicit")
CODEBOOK_PATH = Path(__file__).resolve().parents[2] / "data" / "reference" / "narrative_codebook.json"
OTHER = "Diğer"


def load_codebook(path: Path = CODEBOOK_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def blame_level(raw: str) -> str:
    v = (raw or "").strip()
    if not v or v == "—" or v.startswith(("Belirtilmiyor", "Belirsiz")):
        return "none"
    return "implied" if "(ima)" in v else "explicit"


def frame_category(raw: str, codebook: dict) -> str:
    return codebook["frames"].get((raw or "").strip(), OTHER)


def human_rows(core: dict) -> list[dict]:
    return [{"key": k, **r} for k, e in core["N"].items() if e.get("status") in HUMAN_STATUSES for r in e["rows"]]
