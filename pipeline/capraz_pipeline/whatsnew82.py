"""8.2 "Yeni": the AI review before (8.0 events, behavioural only) and after the rerun (8.1 data, both passes).

    python -m capraz_pipeline.whatsnew82 --old runs/bg/biasguard.json --new runs/bg82/biasguard.json \
        --media runs/bgm82/biasguard.json

Writes data/reference/whatsnew-82.json; narratives.merge() puts it into core.bin as key W82.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .config import REPO

OUT = REPO / "data" / "reference" / "whatsnew-82.json"
COLS = ["Önceki 8.2", "Yeni 8.2"]


def _tr(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}".replace(".", ",")


def _done(bg: dict) -> list[dict]:
    return [e for e in bg["events"] if e["status"] == "review_complete"]


def _findings(bg: dict) -> list[tuple[str, dict]]:
    # the findings the site shows (bg7Live, aix._live): contextual effects are kept in the pack but not shown
    return [(e["event"], f) for e in _done(bg) for k in ("supported", "uncertain") for f in e.get(k, [])]


def _top(fs: list[tuple[str, dict]], n: int | None = 5) -> list[tuple[str, int]]:
    return Counter(f["name"] for _, f in fs).most_common(n)


def compare(old: dict, new: dict, media: dict | None, aix: dict | None = None) -> dict:
    so, sn = old["summary"], new["summary"]
    ev_old, ev_new = {e["event"] for e in old["events"]}, {e["event"] for e in new["events"]}
    both = ev_old & ev_new
    fo, fn = _findings(old), _findings(new)
    fm = _findings(media) if media else []
    old_top = dict(_top(fo, None))
    hit = lambda fs: len({e for e, _ in fs})
    out = []
    out.append({"id": "olaylar", "tag": "değişti", "title": "İncelenen olaylar 8.1 verisinden yeniden seçildi",
                "claim": f"Önceki inceleme 8.0’ın en çok kurumun verdiği {len(ev_old)} olayına bakıyordu. Yeni inceleme 8.1 verisinin "
                         f"(51 kurum, 13 Kasım’a kadar) en geniş {len(ev_new)} olayına bakıyor; iki listede ortak {len(both)} olay var.",
                "cols": COLS, "rows": [["İncelenen olay", len(ev_old), len(ev_new)], ["Tamamlanan inceleme", so["completed"], sn["completed"]],
                                       ["İki listede ortak olay", len(both), len(both)]],
                "note": "Ortak olaylarda bile başlık seti farklı: 8.1’de olayı veren kurum sayısı arttı, metin yeniden kuruldu."})
    pend = (media or {}).get("pending", {})
    fp = [(e["event"], f) for e in pend.get("events", []) for k in ("supported", "uncertain") for f in e.get(k, [])]
    if media:
        sm = media["summary"]
        out.append({"id": "medya", "tag": "yeni", "title": "Medyanın oyunları: yalnızca laboratuvardan geçen kartlar canlı",
                    "claim": f"{sm['catalog'] + len(pend.get('cards', []))} medya tekniği kartı ayrı bir AI incelemesiyle {sm['completed']} olayda çalıştırıldı. "
                             f"Sahip onayı ve laboratuvar sınamasından {sm['catalog']} kart geçti; canlıda {len(fm)} bulgusu var, {hit(fm)} olayda. "
                             f"Geçemeyen {len(pend.get('cards', []))} kartın {len(fp)} bulgusu karar verilene kadar Yönetim’de bekliyor.",
                    "cols": COLS, "rows": [["Canlı medya kartı", "—", sm["catalog"]], ["Canlı medya bulgusu", "—", len(fm)],
                                           ["Yönetim’de bekleyen kart", "—", len(pend.get("cards", []))], ["Yönetim’de bekleyen bulgu", "—", len(fp)]] +
                                          [[f"En sık: {n}", "—", k] for n, k in _top(fm)],
                    "note": "Laboratuvar her kartı yapay vakalarda sınar: olumlu vakada tekniği bulmalı, alıntı ve sınır vakalarında bulmamalı. "
                            "Bekleyen kartların çoğu, kontrol vakalarında hiç incelenmediği için “tamamlanmadı” sayıldı; yanlış bir cevap yüzünden değil." +
                            (f" {sm['incomplete'] + sm['notAttempted']} olayın medya incelemesi tamamlanmadı; o olaylarda grup “incelenemedi” yazar."
                             if sm["incomplete"] + sm["notAttempted"] else "")})
    out.append({"id": "davranis", "tag": "değişti", "title": "Davranışsal yanlılıklar yeniden ölçüldü",
                "claim": f"Bulgu sayısı önce {len(fo)}, şimdi {len(fn)}; en az bir bulgusu olan olay önce {hit(fo)}, şimdi {hit(fn)}.",
                "cols": COLS, "rows": [["Bulgu", len(fo), len(fn)], ["Bulgulu olay", hit(fo), hit(fn)],
                                       ["Doğrulanmış alıntı", so["quotesVerified"], sn["quotesVerified"]]] +
                                      [[f"En sık: {n}", old_top.get(n, 0), k] for n, k in _top(fn)]})
    keep = [(e, f["id"]) for e, f in fo if e in both]
    new_ids = {(e, f["id"]) for e, f in fn}
    again = sum(k in new_ids for k in keep)
    if keep:
        out.append({"id": "tekrar", "tag": "sürüyor", "title": "Aynı olaylarda aynı kavramlar ne kadar tekrar çıktı?",
                    "claim": f"Ortak {len(both)} olayda önceki incelemenin bulduğu {len(keep)} kavramın {again} tanesi (%{round(100 * again / len(keep))}) "
                             "yeniden incelemede de bulundu.",
                    "note": "Ayrışma, kısmen yeni kurumların eklenen başlıklarından, kısmen AI incelemesinin kendi oynaklığından gelir; bu oran bir doğruluk ölçüsü değildir."})
    out.append({"id": "ayrim", "tag": "değişti", "title": "“AI onaylı / insan kontrolü bekliyor” ayrımı kamu sayfalarından kalktı",
                "claim": f"Önceki sürümde {so.get('aiConfident', 0)} bulgu “AI onaylı”, {so.get('needsHuman', 0)} bulgu “insan kontrolü bekliyor” "
                         "etiketiyle ayrılıyordu. Artık bulunan her şey aynı biçimde yayında; durum etiketi yalnızca Yönetim’de duruyor.",
                "cols": COLS, "rows": [["Kamuda etiketle ayrılan bulgu", so.get("aiConfident", 0) + so.get("needsHuman", 0), 0],
                                       ["Kamuda gösterilen bulgu", len(fo), len(fn) + len(fm)]]})
    expl = lambda bg: sum(1 for _, f in _findings(bg) if f.get("explain", {}).get("means"))
    out.append({"id": "anlam", "tag": "yeni", "title": "Her bulgunun yanında “Ne anlama geliyor”",
                "claim": "Bulgular artık üç kısa metinle gelir: ne fark edildi, okur için ne anlama geliyor, neden kesin değil. "
                         "Örüntüler › Nasıl anlatıyor iki grubun bütün bulgularını kavram kavram listeler.",
                "cols": COLS, "rows": [["“Ne anlama geliyor” metni olan bulgu", 0, expl(new) + (expl(media) if media else 0)]]})
    if aix:
        w, b = aix["wording"], aix["blame"]
        compared = w["headlines"]["auc"] is not None and b is not None
        out.append({"id": "kural", "tag": "yeni", "title": "AI bulguları sitenin kural tabanlı ölçümleriyle karşılaştırıldı",
                    "claim": "Örüntüler yeniden düzenlendi: “Genel bakış” her kurumu kural tabanlı ve AI imzalı bütün ölçülerde yan yana gösteriyor; AI bulguları konusuna göre öteki sayfalara yerleşti. " +
                             (f"AI’nin sözcük tekniği alıntıları kural tabanlı yüklü dil puanıyla neredeyse ilişkisiz (başlık düzeyinde AUC {_tr(w['headlines']['auc'])}, "
                              f"yazı tura 0,50); sorumluluk çerçevesi ile anlatı haritasının ‘sorumlu tutulan’ kodu da az örtüşüyor (κ {_tr(b['kappa'])})."
                              if compared else
                              "Sözcük tekniği ve sorumluluk çerçevesi karşılaştırmaları, bu kartlar laboratuvardan geçene kadar yayında değil."),
                    "rows": [["AI ile karşılaştırılan kurum", "—", len(w["outlets"])], ["Karşılaştırılan başlık", "—", w["headlines"]["cited"] + w["headlines"]["notCited"]]] +
                            ([["Anlatı haritasıyla ortak olay", "—", b["events"]]] if b else []), "cols": COLS,
                    "note": "İki ölçünün az örtüşmesi birinin yanlış olduğunu göstermez: kural tabanlı puan sözcüğe, AI kurumlar arasındaki farka bakar."
                            if compared else "Karşılaştırmalar Yönetim’de bekleyen medya kartlarının bulgularına dayanıyordu."})
        out.append({"id": "tasarim", "tag": "değişti", "title": "Görünüm marka kurallarına döndü",
                    "claim": "Gazete kâğıdı zemini, Newsreader başlıklar ve IBM Plex rakamlar geri geldi; AI bulguları kanıt kartlarında, “AI imzalı” damgasıyla. "
                             "Kırmızı ve mavi yalnızca bir kurum hakkında, sarı yalnızca bir sözcüğün arkasında."})
    out.append({"id": "sinir", "tag": "uyarı", "title": "Bu bir deneme sürümü",
                "claim": "Medya kartları canlıya yalnızca sahip onayı ve laboratuvar sınamasıyla çıkar. Hiçbir bulgu insan tarafından doğrulanmadı; "
                         "bir olayda bulgu olmaması o olayda teknik ya da yanlılık olmadığı anlamına gelmez."})
    n_all = len(fn) + len(fm)
    return {"lede": f"8.2’nin AI incelemesi güncellenen algoritmayla baştan çalıştırıldı: laboratuvardan geçen medya teknikleri canlı, bütün bulgular ayrımsız yayında, "
                    f"her bulgu ne anlama geldiğiyle birlikte veriliyor. Aşağıda önceki 8.2 incelemesi (8.0 olayları) ile yenisi (8.1 verisi) yan yana.",
            "band": f"Yeniden çalışan AI incelemesi: {n_all} bulgu, laboratuvardan geçen medya teknikleri canlı, önceki sürümle karşılaştırma.",
            "findings": out}


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m capraz_pipeline.whatsnew82")
    p.add_argument("--old", type=Path, required=True)
    p.add_argument("--new", type=Path, required=True)
    p.add_argument("--media", type=Path)
    p.add_argument("--aix", type=Path, help="data/reference/aix-82.json (python -m capraz_pipeline.aix)")
    a = p.parse_args()
    load = lambda x: json.loads(Path(x).read_text())
    res = compare(load(a.old), load(a.new), load(a.media) if a.media else None, load(a.aix) if a.aix else None)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(OUT, len(res["findings"]))


if __name__ == "__main__":
    main()
