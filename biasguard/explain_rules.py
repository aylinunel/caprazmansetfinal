"""Public texts for a finding, composed from what the reviewers already wrote (no extra model call).

noticed = the advocate's observation (else the skeptic's, else the verified quotes with their outlets)
means   = what the concept means for a reader, plus which outlets' readers saw it
why     = the skeptic's non-bias explanation (else the advocate's, else the first missing context)

Each candidate goes through news.validate_explain; the first one that passes is used, so every
quote shown is verbatim from the event text and every field is 1-2 sentences of 40-320 characters.

    python -m biasguard.explain_rules --run runs/bg82 --core public/data/core.bin [--catalog media]
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path
from typing import Any

from .news import _inputs, explain_dir, validate_explain

# What each media technique means for a reader (kept in step with MEDIA_TR in site/js/v7/bulgu82.js).
MEDIA_MEANS = {
    "ad-hominem": "Okura iddianın kendisi yerine onu söyleyen kişi hakkında bir yargı veriliyor.",
    "causal-overclaim": "Okura, metnin kanıtlamadığı bir neden-sonuç bağı hazır sunuluyor.",
    "cherry-picking": "Okur olayın bir yanını görüyor; o yanı zayıflatan bilgi başlığa girmiyor.",
    "consequence-framing": "Okur olayı, kime ne kazandırıp kaybettireceği üzerinden okuyor.",
    "emphasis-framing": "Okurun olaydan aklında kalan şey, kurumun başa koyduğu ayrıntı oluyor.",
    "episodic-framing": "Okur olayı tek bir vaka olarak görüyor; arkasındaki genel sorun görünmüyor.",
    "false-dilemma": "Okura durum, başka seçenek yokmuş gibi iki seçeneğe indirilmiş olarak sunuluyor.",
    "fear-appeal": "Okurun olaya tepkisi bilgiden çok korku ve tehdit duygusuyla şekilleniyor.",
    "labeling": "Okur aynı kişiyi ya da grubu, yargı taşıyan bir adla tanıyor.",
    "loaded-language": "Okur olayı yansız bir sözcük yerine duygu yüklü bir sözcükle öğreniyor.",
    "metaphorical-framing": "Okur olayı bir mecazla okuyor; mecaz bir yorumu da beraberinde getiriyor.",
    "responsibility-framing": "Okura olaydan kimin sorumlu olduğu ima ediliyor ya da sorumlu gizleniyor.",
    "selective-statistics": "Okur bir sayıyı, karşılaştırma ya da tabanı olmadan görüyor.",
    "spin": "Okur olayı, kurumun genel çizgisine uyan bir yöne eğilmiş olarak görüyor.",
    "strawman": "Okur bir tarafın görüşünü, çürütmesi kolay bir biçimde öğreniyor.",
    "thematic-framing": "Okur olayı tek vakadan çok genel bir eğilimin parçası olarak görüyor.",
    "word-choice": "Okurun olaya bakışını, kurumun aynı olgu için seçtiği sözcüğün tonu belirliyor.",
}
# Behavioural concepts that have no Turkish definition in the concept registry (core.bin key BR)
BEHAVIOURAL_MEANS = {
    "framing-effect": "Aynı olgu farklı sunulunca okurun ondan çıkardığı yargı da değişebilir.",
    "leveling-and-sharpening": "Aktarıldıkça bazı ayrıntılar silinip bazıları keskinleşir; okur olayın sadeleşmiş bir sürümünü görür.",
    "illusory-correlation": "Okura, aslında aralarında bağ kanıtlanmamış iki şey birbirine bağlıymış gibi görünür.",
    "fundamental-attribution-error": "Okur olayı koşullardan çok kişilerin karakterine bağlamaya yönlendirilir.",
    "optimism-bias": "Okura gelecek, verilerin desteklediğinden daha iyimser gösterilir.",
    "outcome-bias": "Okur bir kararı, verildiği andaki bilgiye göre değil sonucuna göre değerlendirmeye yönlendirilir.",
    "belief-perseverance": "Okurun eski kanaati, onu çürüten bilgi gelse de korunur.",
    "priming": "Başlıkta önce verilen bir öğe, okurun gerisini nasıl yorumlayacağını önceden belirler.",
    "hindsight-bias": "Olay olduktan sonra, olacağı baştan belliymiş gibi anlatılır.",
    "messenger-effect": "Okur bilgiyi içeriğinden çok onu kimin söylediğine göre tartmaya yönlendirilir.",
    "recency-effect": "Okurun aklında olayın en son gelişmesi kalır; önceki bağlam geri planda kalır.",
    "illusory-truth-effect": "Bir iddia sık tekrarlandıkça okura doğruymuş gibi gelmeye başlar.",
    "automation-bias": "Okur, bir makine ya da algoritmanın verdiği sonuca fazla güvenmeye yönlendirilir.",
    "source-confusion": "Okur bir bilginin nereden geldiğini (iddia mı, resmî açıklama mı) karıştırabilir.",
    "peak-end-rule": "Okurun olaydan aklında kalan, en çarpıcı anı ve sonu olur.",
    "affect-heuristic": "Okurun olay hakkındaki yargısını bilgiden çok uyandırılan duygu belirler.",
    "bikeshedding": "Okurun dikkati önemli konudan, tartışması kolay bir ayrıntıya kayar.",
}
# BiasGuard card ids that the concept registry (core.bin key BR) stores under an older key (BG7ALIAS in app.js)
BR_ALIAS = {"base-rate-fallacy": "base-rate", "gamblers-fallacy": "gambler-s-fallacy",
            "identifiable-victim-effect": "identifiable-victim", "just-world-hypothesis": "just-world",
            "belief-perseverance": "belief-perseverance-the-backfire-effect", "choice-overload-bias": "choice-overload",
            "levels-of-processing-effect": "levels-of-processing", "illusory-truth-effect": "illusory-truth"}
MAX, MIN = 320, 40
_SENT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÇĞİÖŞÜ0-9“\"'])")


def _first_sentence(text: str) -> str:
    return _SENT.split((text or "").strip(), 1)[0].strip()


def _fit(text: str) -> str:
    """One sentence, at most MAX characters, cut at a clause or word boundary."""
    s = _first_sentence(text)
    if len(s) <= MAX:
        return s
    cut = s[:MAX - 1]
    for sep in ("; ", ", ", " "):
        if cut.rfind(sep) > MIN:
            cut = cut[:cut.rfind(sep)]
            break
    return cut.rstrip(" ,;:") + "."


def _role(items: list[dict], role: str) -> str:
    return next((m["text"] for m in items or [] if m.get("role") == role and m.get("text")), "")


def _outlets(f: dict, names: dict[str, str]) -> list[str]:
    seen: list[str] = []
    for e in f.get("evidence", []):
        for o in e.get("o", []):
            if names.get(o, o) not in seen:
                seen.append(names.get(o, o))
    return seen


def _join(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " ve " + xs[-1]


def _quote_line(f: dict, names: dict[str, str]) -> str:
    parts = []
    for e in f.get("evidence", []):
        q = re.sub(r"^\[[^\]]+\]\s*", "", e["q"]).strip()  # drop the "[outlet · HH:MM]" prefix
        if e.get("o") and q and len(q) <= 110:
            parts.append(f"{names.get(e['o'][0], e['o'][0])} “{q}”")
        if len(parts) == 2:
            break
    return ("Başlıklarda " + " ve ".join(parts) + " diye yazdı.") if parts else ""


def compose(f: dict, text: str, names: dict[str, str], concept_means: str) -> dict[str, str] | None:
    """The first valid {noticed, means, why} from the reviewer fields, or None."""
    outs = _outlets(f, names)
    who = "" if not outs else _join(outs) if len(outs) <= 3 else ", ".join(outs[:3]) + " ve başka kurumların"
    reader = (f"Bu bulgu {who} okurlarının gördüğü başlıklara dayanıyor."
              if outs else "")
    options = {
        "noticed": [_fit(_role(f.get("mechanisms"), "advocate")), _fit(_role(f.get("mechanisms"), "skeptic")),
                    _quote_line(f, names)],
        "means": [f"{concept_means} {reader}".strip(), concept_means],
        "why": [_fit(_role(f.get("alternatives"), "skeptic")), _fit(_role(f.get("alternatives"), "advocate")),
                _fit("Eksik bilgi: " + f["missing"][0]) if f.get("missing") else ""],
    }
    out = {}
    for k, cands in options.items():
        ok = [c for c in cands if c and not validate_explain({"noticed": c, "why": c}, text)]
        if not ok:
            return None
        out[k] = ok[0]
    return out


def concept_means(f: dict, catalog: str, registry: dict[str, dict]) -> str:
    if catalog == "media":
        return MEDIA_MEANS.get(f["id"], "")
    if f["id"] in BEHAVIOURAL_MEANS:
        return BEHAVIOURAL_MEANS[f["id"]]
    r = registry.get(BR_ALIAS.get(f["id"], f["id"]))
    if r and r.get("df"):
        return f"{r.get('tr') or f['name']}: {r['df'].rstrip('.')}."
    return ""


def run(run_dir: Path, core: Path, catalog: str) -> dict[str, int]:
    c = json.loads(gzip.decompress(core.read_bytes()))
    names = {**c.get("SN", {}), **{s["s"]: s.get("n") or s["s"] for s in c.get("S", [])}}  # as srcName() in app.js
    registry = {b["k"]: b for b in c.get("BR", [])}
    texts = {it["event"]: it["text"] for it in _inputs(run_dir)}
    res = json.loads((run_dir / "biasguard.json").read_text())
    d = explain_dir(run_dir)
    d.mkdir(parents=True, exist_ok=True)
    written = skipped = 0
    for ev in res["events"]:
        for f in ev.get("supported", []) + ev.get("uncertain", []):
            x = compose(f, texts.get(ev["event"], ""), names, concept_means(f, catalog, registry))
            if x is None:
                skipped += 1
                continue
            (d / f"{ev['event']}__{f['id']}.json").write_text(json.dumps(x, ensure_ascii=False))
            written += 1
    return {"written": written, "skipped": skipped}


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m biasguard.explain_rules")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--core", type=Path, required=True, help="core.bin with outlet names (S) and concept registry (BR)")
    p.add_argument("--catalog", choices=["behavioural", "media"], default="behavioural")
    a = p.parse_args()
    print(json.dumps(run(a.run, a.core, a.catalog)))


if __name__ == "__main__":
    main()
