"""Article URLs leave the startup packs: a-YYYY-MM.bin keeps what the first screen needs, u-YYYY-MM.bin holds the
URLs and is fetched after the page is up (loader.js window.cmUrls). The only startup logic that read a URL, the
notice rule (turkish-layer.js ruleHits), gets its answer precomputed per article in column "nu":
bit 1 = NOTICE_URL[0] (PARAMS.noticeRules.url), bit 2 = NOTICE_URL[1] (PARAMS.noticeRulesV1.url).

    python -m capraz_pipeline.urlpack --data ../public/data    # convert existing packs in place
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

# Must equal PARAMS.noticeRules.url and PARAMS.noticeRulesV1.url in site/js/turkish-layer.js (tests/test_urlpack.py).
NOTICE_URL = [r"\/(resmi-?ilan(lar)?|ilan|ilanlar)(\/|$)", r"resmi-?ilan|\/ilan\/|\/ilanlar"]
_RX = [re.compile(r, re.I) for r in NOTICE_URL]


def split(pack: dict) -> tuple[dict, dict]:
    """(startup pack without hosts/h/u, plus nu) and (url pack: i, hosts, h, u)."""
    hosts, h, u = pack["hosts"], pack["h"], pack["u"]
    nu = []
    for k in range(len(u)):
        url = "https://" + hosts[h[k]] + "/" + u[k]
        nu.append(sum(1 << b for b, rx in enumerate(_RX) if rx.search(url)))
    slim = {k: v for k, v in pack.items() if k not in ("hosts", "h", "u")}
    slim["nu"] = nu
    return slim, {"i": pack["i"], "hosts": hosts, "h": h, "u": u}


def _dump(path: Path, obj) -> None:
    path.write_bytes(gzip.compress(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), mtime=0))


def convert(data: Path) -> list[str]:
    done = []
    for p in sorted(data.glob("a-*.bin")):
        pack = json.loads(gzip.decompress(p.read_bytes()))
        if "u" not in pack:
            continue
        slim, urls = split(pack)
        _dump(p, slim)
        _dump(p.with_name("u-" + p.name[2:]), urls)
        done.append(p.name)
    return done


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m capraz_pipeline.urlpack")
    ap.add_argument("--data", type=Path, required=True)
    print(convert(ap.parse_args().data))


if __name__ == "__main__":
    main()
