"""python -m validation.mlbench run --coded runs/narr-eval/coded"""
import argparse
import json
from pathlib import Path

from biasguard.news import _load
from validation.answerkey.codebook import blame_level, frame_category, load_codebook
from validation.answerkey.narrative_eval import read_coded
from validation.answerkey.record import agreement, from_core, read

from .data import rows
from .evaluate import cross_validate, score_fixed
from .models import Majority, TfidfLogReg

REPO = Path(__file__).resolve().parents[2]
LABELS = ("blame_level", "frame_category")
MODELS = ("majority", "tfidf_logreg", "agent")


def agent_predictions(coded: dict, codebook: dict) -> dict[str, dict]:
    out = {"blame_level": {}, "frame_category": {}}
    for key, c in coded.items():
        for r in c.get("rows", []):
            out["blame_level"][(key, r.get("s"))] = blame_level(r.get("blame"))
            out["frame_category"][(key, r.get("s"))] = frame_category(r.get("frame"), codebook)
    return out


def run(core: dict, coded: dict, codebook: dict) -> dict:
    rs, agent = rows(core, codebook), agent_predictions(coded, codebook)
    return {lab: {"majority": cross_validate(Majority, rs, lab), "tfidf_logreg": cross_validate(TfidfLogReg, rs, lab),
                  "agent": score_fixed(agent[lab], rs, lab)} for lab in LABELS}


def report(res: dict, approved: bool, unmapped: int, total: int, agree: dict | None = None) -> str:
    lines = ["# Temel modeller: anlatı kodlaması (mlbench)", "",
             "İnsan kodlamasına karşı 5 katlı, olay bazında gruplanmış çapraz doğrulama; ajan sabit tahmin olarak puanlanır.", "",
             "| Etiket | Model | n | Doğruluk | Makro F1 |", "|---|---|---|---|---|"]
    for lab in LABELS:
        for m in MODELS:
            r = res[lab][m]
            lines.append(f"| {lab} | {m} | {r['n']} | {r['accuracy']:.3f} | {r['macro_f1']:.3f} |")
    lines += [""]
    for lab, a in (agree or {}).items():
        lines.append(f"- {lab}: alan {'kullanılabilir' if a['usable'] else 'henüz kullanılabilir değil (not usable yet)'} "
                     f"(iki kez kodlanan {a['items_double']} öğe)")
    lines += ["", ("" if approved else "Çerçeve kod kitabı henüz onaylı değil (approved=false). ") +
              f"Ajanın {total} çerçevesinden {unmapped} tanesi kod kitabının dışında; bunlar Diğer sayılır, dolayısıyla "
              "ajanın çerçeve sayısı çoğunlukla sözcük dağarcığını yansıtır.", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="validation.mlbench")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--core", type=Path, default=REPO / "public" / "data" / "core.bin")
    r.add_argument("--coded", type=Path, required=True)
    a = ap.parse_args(argv)
    codebook, coded = load_codebook(), read_coded(a.coded)
    core = _load(a.core)
    res = run(core, coded, codebook)
    (REPO / "validation" / "reference" / "mlbench.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frames = [(r.get("frame") or "").strip() for c in coded.values() for r in c.get("rows", [])]
    unmapped = sum(bool(f) and f not in codebook["frames"] for f in frames)
    codings = read() + from_core(core, codebook)
    md = report(res, bool(codebook.get("approved")), unmapped, len(frames), {lab: agreement(codings, lab) for lab in LABELS})
    (REPO / "docs" / "validation" / "reports" / "mlbench.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
