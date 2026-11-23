"""Assemble the static site: one HTML page (styles, logo, loader, app scripts) + the data packs.

The page has no build-time data in it; everything the app shows comes from data/*.bin, so a new
build (older dates, a live run) only replaces the data folder.
"""
from __future__ import annotations

import base64
import shutil
from pathlib import Path

from .config import REPO, SCORER

SITE = REPO / "site"
V7_ORDER = ["logic", "core", "graph", "viz", "dots", "fog", "press", "motion", "home", "anlati", "anlativ", "olay", "oruntu", "kurum", "parti", "yontem", "ilan", "yenilikler", "aiimza", "lens", "desk"]


PART = 12_000_000  # base64 chars per artifact file (a multiple of 4, so parts join back exactly)


def assemble(data_dir: Path, dest: Path, title: str = "Çapraz Manşet 9", fragment: bool = False) -> Path:
    """fragment=True: no doctype/html/head/body wrapper (claude.ai artifacts add their own)."""
    rules = SCORER.read_text(encoding="utf-8")
    app = (SITE / "js" / "app.js").read_text(encoding="utf-8")
    assert "/*@@RULES@@*/" in app, "app.js lost its shared-rules marker"
    app = app.replace("/*@@RULES@@*/", rules)
    assert "/*@@V7@@*/" in app, "app.js lost its v7 marker"
    v7 = [SITE / "js" / "v7" / (n + ".js") for n in V7_ORDER]
    app = app.replace("/*@@V7@@*/", "\n".join(f.read_text(encoding="utf-8") for f in v7 if f.exists()))
    code = lambda s: s.replace("</script", "<\\/script")  # keep inline code from closing its tag
    html = "\n".join([
        "<!doctype html>", '<html lang="tr">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
        f"<title>{title}</title>", (SITE / "head.html").read_text(encoding="utf-8"),
        "<style>", (SITE / "styles.css").read_text(encoding="utf-8"), "</style>", "</head>", "<body>",
        '<div id="app"></div>', '<div class="tip" id="tip"></div>',
        '<script type="application/json" id="cm-logo">' + (SITE / "logo.json").read_text(encoding="utf-8").strip() + "</script>",
        ('<script>window.CM_PACK_SUFFIX = ".txt";</script>' if fragment else ""),
        "<script>" + code((SITE / "js" / "loader.js").read_text(encoding="utf-8")) + "</script>",
        '<script type="text/x-cm">' + code((SITE / "js" / "turkish-layer.js").read_text(encoding="utf-8")) + "</script>",
        '<script type="text/x-cm">' + code(app) + "</script>",
        "</body>", "</html>", ""])
    if fragment:
        for tag in ("<!doctype html>", '<html lang="tr">', "<head>", "</head>", "<body>", "</body>", "</html>"):
            html = html.replace(tag + "\n", "", 1)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "index.html").write_text(html, encoding="utf-8")
    (dest / "data").mkdir(exist_ok=True)
    for f in sorted(data_dir.glob("*.bin")):
        if fragment:
            # shortcut: claude.ai artifacts serve no binary files, so packs go as base64 text (+33 %).
            # The artifact takes text files up to 16 MB: a bigger pack goes in parts named by a one-line index.
            b, name = base64.b64encode(f.read_bytes()), dest / "data" / (f.name + ".txt")
            parts = [b[i:i + PART] for i in range(0, len(b), PART)]
            for i, part in enumerate(parts if len(parts) > 1 else []):
                (dest / "data" / f"{name.name}.{i}").write_bytes(part)
            name.write_bytes(b if len(parts) == 1 else f"PARTS:{len(parts)}".encode())
        elif f.resolve() != (dest / "data" / f.name).resolve():
            shutil.copy2(f, dest / "data" / f.name)
    return dest / "index.html"
