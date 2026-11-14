"""Whitelist renderer: simulation facts in, exactly (text, context) out.

Inputs follow the shape BiasGuard already receives for news events: `text` is lines of
`[Kurum X · HH:MM] <headline> — <lede>` and `context` starts with `Olay: …`.
Nothing about the simulation (strength, draw, trace, label) may reach the output.
"""
from __future__ import annotations

import dataclasses
import json
import re

from .cases import PERTURBATIONS, DetectorInput
from .sim import Realized


class Leak(ValueError):
    """A detector-visible object contains something only the evaluator may know."""


FORBIDDEN = ("positive", "boundary", "strength", "seed", "split", "expected", "active",
             "inactive_control", "boundary_control", "missing_context", "quoted_control")


def _num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:.1f}".replace(".", ",")


# --- selective_statistics -------------------------------------------------------------------------

_SS = (
    {"time": "09:00", "event": "Denetim raporu açıklandı",
     "head": "Denetimde ihlal oranı yüzde {r}",
     "lede": "İncelenen {d} dosyanın {n} tanesinde ihlal saptandı; rapor benzer tüm dosyalar için uyarıyor.",
     "ctx": "benzer nitelikteki {R} dosyanın {n} tanesinde ihlal var; ihlallerin tümü incelenen dosyalar arasında.",
     "quote_head": 'Muhalefet "ihlal oranı yüzde {r}" dedi, Sayıştay rakamı düzeltti',
     "quote_lede": "Kurum, oranın benzer {R} dosyada yüzde {rr} olduğunu açıkladı."},
    {"time": "10:30", "event": "Hastane verileri yayımlandı",
     "head": "Hastanede komplikasyon oranı yüzde {r}",
     "lede": "İzlenen {d} hastanın {n} tanesinde komplikasyon görüldü; uzmanlar benzer tüm hastalar için dikkat çekiyor.",
     "ctx": "benzer durumdaki {R} hastanın {n} tanesinde komplikasyon var; komplikasyonların tümü izlenen hastalar arasında.",
     "quote_head": 'Dernek başkanı "komplikasyon oranı yüzde {r}" dedi, Bakanlık yalanladı',
     "quote_lede": "Bakanlık, oranın benzer {R} hastada yüzde {rr} olduğunu bildirdi."},
    {"time": "08:15", "event": "Sınav sonuçları açıklandı",
     "head": "Skandal tablo: okullarda başarısızlık oranı yüzde {r}",
     "lede": "Sınava giren {d} öğrencinin {n} tanesi başarısız oldu; tablo ülkedeki benzer tüm öğrenciler için alarm veriyor.",
     "ctx": "aynı sınava giren {R} öğrencinin {n} tanesi başarısız; başarısızların tümü bu grubun içinde.",
     "quote_head": 'Sendika "Skandal: başarısızlık yüzde {r}" dedi, kurul rakamı düzeltti',
     "quote_lede": "Kurul, oranın aynı sınava giren {R} öğrencide yüzde {rr} olduğunu açıkladı."},
)


def _selective_statistics(realized: Realized, kind: str, variant: int) -> DetectorInput:
    task = realized.scenario["contexts"][-1]
    n, R = task["event_count"], task["relevant_denominator"]
    d = realized.state["last_denominator_used"]
    v = _SS[variant]
    values = {"n": n, "R": R, "d": d, "r": _num(n * 100 / d), "rr": _num(n * 100 / R)}
    comparison = f"\nKarşılaştırma verisi: {v['ctx'].format(**values)}"
    if kind == "quoted_control":
        text = f"[Kurum A · {v['time']}] {v['quote_head'].format(**values)} — {v['quote_lede'].format(**values)}"
        return DetectorInput(text, f"Olay: {v['event']}{comparison}")
    text = f"[Kurum A · {v['time']}] {v['head'].format(**values)} — {v['lede'].format(**values)}"
    return DetectorInput(text, f"Olay: {v['event']}" + ("" if kind == "missing_context" else comparison))


# --- illusory_truth_effect ------------------------------------------------------------------------

_IT = (
    {"event": "Şebeke suyu tartışması", "source": "laboratuvar",
     "claims": ("Bakanlık: Şebeke suyu güvenli", "Bakanlık yineledi: Şebeke suyu güvenli",
                "Şebeke suyu güvenli açıklaması bir kez daha yapıldı"),
     "plain": "Açıklamada yeni bir veri paylaşılmadı.",
     "quote": 'Uzmanlar: "Şebeke suyu güvenli" sözü kanıt sunulmadan tekrarlanıyor'},
    {"event": "Köprü güvenliği tartışması", "source": "mühendislik",
     "claims": ("Belediye: Köprü sağlam", "Belediye tekrarladı: Köprü sağlam",
                "Köprü sağlam açıklaması yeniden yapıldı"),
     "plain": "Açıklamada yeni bir inceleme sonucu yer almadı.",
     "quote": 'Oda başkanı: "Köprü sağlam" sözü yeni bir inceleme olmadan yineleniyor'},
)


def _clock(step: int) -> str:
    minutes = 9 * 60 + 30 * step
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _illusory_truth_effect(realized: Realized, kind: str, variant: int) -> DetectorInput:
    v = _IT[variant]
    lines, reports = [], 0
    for i, ctx in enumerate(realized.scenario["contexts"]):
        outlet = "Kurum A" if i % 2 == 0 else "Kurum B"
        claim = v["claims"][i % len(v["claims"])]
        if kind == "quoted_control":
            lines.append(f"[{outlet} · {_clock(i)}] {v['quote']} — {v['plain']}")
            continue
        if ctx.get("evidence"):
            reports += len(ctx["evidence"])
            lede = f"{reports}. bağımsız {v['source']} raporu yayımlandı."
        else:
            lede = v["plain"]
        lines.append(f"[{outlet} · {_clock(i)}] {claim} — {lede}")
    return DetectorInput("\n".join(lines), f"Olay: {v['event']}")


_RENDERERS = {
    "selective_statistics": (_selective_statistics, len(_SS),
                             ("positive", "inactive_control", "boundary_control", "missing_context", "quoted_control")),
    "illusory_truth_effect": (_illusory_truth_effect, len(_IT),
                              ("positive", "boundary_control", "quoted_control")),
}


def variants(concept: str) -> int:
    return _RENDERERS[concept][1]


def kinds(concept: str) -> tuple[str, ...]:
    return _RENDERERS[concept][2]


def _perturb(d: DetectorInput, perturbation: str) -> DetectorInput:
    if perturbation == "none":
        return d
    if perturbation == "reverse_outlets":
        return DetectorInput("\n".join(d.text.splitlines()[::-1]), d.context)
    if perturbation == "relabel_outlets":
        return DetectorInput(d.text.replace("Kurum A", "Kurum X").replace("Kurum B", "Kurum Y"), d.context)
    return DetectorInput(d.text + " Açıklama Ankara'da yapıldı.", d.context)


def render(realized: Realized, kind: str, variant: int, perturbation: str = "none") -> DetectorInput:
    fn, count, allowed = _RENDERERS[realized.concept]
    if kind not in allowed:
        raise KeyError(f"{realized.concept} has no {kind!r} rendering")
    if not 0 <= variant < count:
        raise KeyError(f"{realized.concept} has no variant {variant}")
    if perturbation not in PERTURBATIONS:
        raise ValueError(f"unknown perturbation: {perturbation}")
    return _perturb(fn(realized, kind, variant), perturbation)


def assert_no_leak(obj: object, concept: str, detector_id: str | None, family: str) -> None:
    """Raise Leak if a detector-visible object carries evaluator-only information."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        obj = dataclasses.asdict(obj)
    blob = json.dumps(obj, ensure_ascii=False, default=str).casefold()
    for token in FORBIDDEN:
        if re.search(rf"(?<![\w]){re.escape(token)}(?![\w])", blob):
            raise Leak(f"detector-visible content contains the evaluator word {token!r}")
    needles = {concept, concept.replace("_", "-"), concept.replace("_", " "), family}
    if detector_id:
        needles.add(detector_id)
    for needle in needles:
        if needle and needle.casefold() in blob:
            raise Leak("detector-visible content contains a concept, card or family identifier")
