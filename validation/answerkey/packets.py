"""Blind packets: fixed item lists a coder codes in the desk without seeing the AI verdict, and the export import."""
import json
import os
import random
from datetime import date, timedelta
from pathlib import Path

from .codebook import human_rows
from .record import UNSURE, Coding, allowed

REPO = Path(__file__).resolve().parents[2]
PACKETS = REPO / "data" / "reference" / "blind-packets.json"
PREFIX = "blind__"
ANSWERS = {"narrative": ("blame_level", "frame_category"), "behaviour": ("present",)}


def narrative_packet(core: dict, n_events: int, seed: int, pid: str, coder: str, today: date) -> dict:
    rng = random.Random(seed)
    rows = [r for r in human_rows(core) if r.get("hl")]
    keys = set(rng.sample(sorted({r["key"] for r in rows}), n_events))
    outlets = {s["s"]: s["n"] for s in core["S"]}
    items = [{"item": f"{r['key']}__{r['s']}", "event": r["key"], "kurum": outlets.get(r["s"], r["s"]), "baslik": r["hl"]}
             for r in rows if r["key"] in keys]
    rng.shuffle(items)
    return {"id": pid, "kind": "narrative", "coder": coder, "created": today.isoformat(), "not_before": None,
            "events": {k: {"olay": core["N"][k]["q"]["happened"]} for k in sorted(keys)}, "items": items}


def behaviour_packet(results: dict, inputs: dict, cards: list, n_events: int, seed: int, pid: str, coder: str,
                     today: date) -> tuple[dict, dict]:
    rng = random.Random(seed)
    done = sorted((e for e in results["events"] if e["status"] == "review_complete"), key=lambda e: e["event"])
    chosen = rng.sample(done, n_events)
    by_id = {c["id"]: c for c in cards}
    items, key, unflagged, events = [], {}, {}, {}
    for e in sorted(chosen, key=lambda e: e["event"]):
        ev = e["event"]
        shown = list(dict.fromkeys(f["id"] for f in e["supported"] + e["uncertain"]))
        pool = sorted(c for c in by_id if c not in e["selected"])
        extra = rng.sample(pool, min(max(len(shown), 2), len(pool)))
        unflagged[ev] = {"sampled": len(extra), "total": len(pool)}
        events[ev] = {"baslik": inputs[ev]["title"], "metin": inputs[ev]["text"]}
        for cid, ai in [(c, True) for c in shown] + [(c, False) for c in extra]:
            c = by_id[cid]
            item = f"{ev}__{cid}"
            items.append({"item": item, "event": ev, "card": cid, "ad": c["name"], "tanim": c["definition"],
                          "kosullar": c["necessary_conditions"]})
            key[item] = {"event": ev, "card": cid, "ai_shown": ai}
    rng.shuffle(items)
    packet = {"id": pid, "kind": "behaviour", "coder": coder, "created": today.isoformat(), "not_before": None,
              "events": events, "items": items}
    return packet, {**key, "_unflagged": unflagged}


def repeat_packet(first: dict, codings: list, n_items: int, seed: int, pid: str, coder: str, today: date,
                  gap_days: int = 14) -> dict:
    coded = {c.item for c in codings if c.coder == first["coder"] and c.value != UNSURE}
    pool = sorted(i["item"] for i in first["items"] if i["item"] in coded)
    if len(pool) < n_items:
        raise ValueError(f"{first['id']}: only {len(pool)} items are coded by {first['coder']}, {n_items} asked")
    rng = random.Random(seed)
    take = set(rng.sample(pool, n_items))
    items = [i for i in first["items"] if i["item"] in take]
    rng.shuffle(items)
    return {"id": pid, "kind": first["kind"], "coder": coder, "created": today.isoformat(),
            "not_before": (today + timedelta(days=gap_days)).isoformat(),
            "events": first["events"], "items": items}


def upsert(packet: dict, categories: list, path=PACKETS) -> None:
    if "__" in packet["id"]:
        raise ValueError(f"packet id {packet['id']!r} must not contain '__'")
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"categories": categories, "packets": []}
    old = next((x for x in data["packets"] if x["id"] == packet["id"]), None)
    if old is not None:
        if old["items"] != packet["items"]:
            raise ValueError(f"packet {packet['id']} already exists with different items; a packet never changes")
        return
    data["categories"] = categories
    data["packets"].append(packet)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def read_export(export: dict, packets: dict) -> list:
    out, ok = [], allowed(packets.get("categories", []))
    items = {x["id"]: {i["item"] for i in x["items"]} for x in packets.get("packets", [])}
    for r in export.get("reviews", []):
        k = r.get("key", "")
        if not k.startswith(PREFIX):
            continue
        pk = next((x for x in packets["packets"] if k.startswith(f"{PREFIX}{x['id']}__")), None)
        if pk is None:
            raise ValueError(f"{k}: unknown packet")
        item = k[len(PREFIX) + len(pk["id"]) + 2:]
        if item not in items[pk["id"]]:
            raise ValueError(f"{k}: item not in packet {pk['id']}")
        answers = r.get("answers") or {}
        fields = ANSWERS[pk["kind"]]
        if set(answers) != set(fields):
            raise ValueError(f"{k}: answers must have exactly {list(fields)}, got {sorted(answers)}")
        for f in fields:
            if answers[f] not in ok[f]:
                raise ValueError(f"{k}: value {answers[f]!r} not allowed for {f}")
            out.append(Coding(item, pk["coder"], f, answers[f]))
    return out
