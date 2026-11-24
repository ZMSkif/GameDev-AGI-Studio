#!/usr/bin/env python3
"""The studio's catalogue of free game assets: sources and exact packs with links.

Reads reference/asset-catalog.json (sources, avoid lists) and reference/asset-packs.json
(packs). It never downloads anything.

  asset_catalog.py list [--kind K] [--dim 3D] [--get direct] [--commercial yes] [--json]
  asset_catalog.py packs [--kind K] [--source S] [--find TEXT] [--json]
  asset_catalog.py check      validate both files
  asset_catalog.py markdown   rewrite reference/asset-catalog.md from the two JSON files
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import console_io  # noqa: E402,F401  (UTF-8 output on Windows)

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "reference" / "asset-catalog.json"
PACKS = ROOT / "reference" / "asset-packs.json"
TABLE = ROOT / "reference" / "asset-catalog.md"
KINDS = {
    "characters": "Персонажи", "clothes": "Одежда", "hair": "Волосы", "animation": "Анимации", "models": "Модели",
    "materials": "Материалы", "hdri": "Свет (HDRI)", "vfx": "Эффекты", "2d": "2D и интерфейс", "fonts": "Шрифты",
    "sound": "Звуки", "music": "Музыка", "tools": "Программы",
}
PACK_KINDS = {
    "blender-library": "Онлайн-библиотеки Blender", "blender-addon": "Дополнения Blender", "characters": "Персонажи и одежда",
    "animations": "Анимации", "materials": "Материалы", "models": "Модели", "hdri": "Свет (HDRI)", "vfx": "Эффекты",
    "2d": "2D и интерфейс", "fonts": "Шрифты с кириллицей", "sound": "Звуки", "music": "Музыка",
}
GET = {"direct": "по ссылке", "blender": "внутри Blender", "account": "нужен вход", "manual": "скачивает человек", "closed": "закрыт"}
COMMERCIAL = {"yes": "да", "check": "проверить", "paid": "только платно", "avoid": "не брать"}
CHECKED = {
    "page": "страница сайта", "pack": "файлы набора", "winget": "каталог winget",
    "not-confirmed": "страница открыта, лицензия не подтверждена", "not-opened": "страница не открывалась",
}
SOURCE_FIELDS = {"id", "name", "kinds", "dims", "gives", "url", "get", "licence", "credit", "commercial", "checked", "note"}
PACK_FIELDS = {"name", "kind", "use", "dims", "source", "licence", "page", "mb", "files", "note"}


def load():
    return (json.loads(CATALOG.read_text(encoding="utf-8")), json.loads(PACKS.read_text(encoding="utf-8")))


def problems(catalog, packs):
    out = []
    seen = set()
    for s in catalog["sources"]:
        name = s.get("id", "?")
        if set(s) != SOURCE_FIELDS:
            out.append(f"{name}: fields {sorted(set(s) ^ SOURCE_FIELDS)}")
            continue
        if name in seen:
            out.append(f"{name}: duplicate id")
        seen.add(name)
        for field, allowed in (("get", GET), ("commercial", COMMERCIAL), ("checked", CHECKED)):
            if s[field] not in allowed:
                out.append(f"{name}: {field} = {s[field]!r}")
        out += [f"{name}: kind {k!r}" for k in s["kinds"] if k not in KINDS]
        if not s["url"].startswith(("https://", "http://")):
            out.append(f"{name}: url")
        if s["commercial"] == "yes" and s["checked"] == "not-opened" and not s["note"]:
            out.append(f"{name}: usable but its licence page was never opened and no note says why")
    for i, p in enumerate(packs["packs"]):
        if set(p) != PACK_FIELDS:
            out.append(f"pack {i}: fields {sorted(set(p) ^ PACK_FIELDS)}")
            continue
        if p["kind"] not in PACK_KINDS:
            out.append(f"pack {p['name']}: kind {p['kind']!r}")
        if not p["licence"] or not p["page"].startswith("https://"):
            out.append(f"pack {p['name']}: licence or page missing")
    return out


def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def markdown(catalog, packs):
    o = ["# Каталог бесплатных ресурсов для игр", "",
         f"Проверено {catalog['checked']}. Файл собирает `scripts/asset_catalog.py markdown`, руками не править.", "",
         "Перед выпуском игры лицензию каждой вещи читать ещё раз (навык `asset-licensing`).", "", "## Где брать", ""]
    for k, title in KINDS.items():
        rows = [s for s in catalog["sources"] if s["kinds"][0] == k]
        if not rows:
            continue
        o += [f"### {title}", "", "| Название | Что даёт | Подходит | Как взять | Лицензия | В продаваемой игре | Чем проверено | Примечание |", "|---|---|---|---|---|---|---|---|"]
        for s in rows:
            o.append("| [%s](%s) | %s | %s | %s | %s | %s | %s | %s |" % (cell(s["name"]), s["url"], cell(s["gives"]), ", ".join(s["dims"]), GET[s["get"]], cell(s["licence"]), COMMERCIAL[s["commercial"]], CHECKED[s["checked"]], cell(s["note"])))
        o.append("")
    o += ["## Конкретные наборы", "", "Прямые ссылки на файлы лежат в `asset-packs.json`.", ""]
    for k, title in PACK_KINDS.items():
        rows = sorted((p for p in packs["packs"] if p["kind"] == k), key=lambda p: (p["source"], p["use"], p["name"]))
        if not rows:
            continue
        o += [f"### {title}: {len(rows)}", "", "| Название | Что это | Источник | Лицензия | МБ | Примечание |", "|---|---|---|---|---:|---|"]
        for p in rows:
            o.append("| [%s](%s) | %s | %s | %s | %s | %s |" % (cell(p["name"]), p["page"], cell(p["use"]), cell(p["source"]), cell(p["licence"]), p["mb"] or "", cell(p["note"])))
        o.append("")
    a = catalog["avoid"]
    o += ["## Не брать", "", "Чужие персонажи в паках MakeHuman: " + ", ".join(a["third_party_characters"]) + ".", "",
          "В файле указана AGPL, а в каталоге CC0 или CC BY, не использовать без проверки: " + ", ".join(a["makehuman_agpl_in_header"]) + ".", ""]
    return "\n".join(o)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--kind", choices=sorted(KINDS))
    p.add_argument("--dim", choices=["2D", "2.5D", "3D"])
    p.add_argument("--get", choices=sorted(GET))
    p.add_argument("--commercial", choices=sorted(COMMERCIAL))
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("packs")
    p.add_argument("--kind", choices=sorted(PACK_KINDS))
    p.add_argument("--source")
    p.add_argument("--find")
    p.add_argument("--json", action="store_true")
    sub.add_parser("check")
    sub.add_parser("markdown")
    a = ap.parse_args(argv)
    catalog, packs = load()
    if a.cmd == "check":
        bad = problems(catalog, packs)
        for b in bad:
            print("ERROR", b)
        if not bad and (not TABLE.exists() or TABLE.read_text(encoding="utf-8") != markdown(catalog, packs)):
            bad = ["table"]
            print("ERROR reference/asset-catalog.md is out of date: run asset_catalog.py markdown")
        print(f"{len(catalog['sources'])} sources, {len(packs['packs'])} packs, {len(bad)} problems")
        return 1 if bad else 0
    if a.cmd == "markdown":
        bad = problems(catalog, packs)
        if bad:
            print("\n".join("ERROR " + b for b in bad))
            return 1
        TABLE.write_text(markdown(catalog, packs), encoding="utf-8", newline="\n")
        print(TABLE)
        return 0
    if a.cmd == "list":
        rows = [s for s in catalog["sources"] if (not a.kind or a.kind in s["kinds"]) and (not a.dim or a.dim in s["dims"]) and (not a.get or s["get"] == a.get) and (not a.commercial or s["commercial"] == a.commercial)]
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for s in rows:
                print(f"{s['id']}: {s['name']} | {s['licence']} | {GET[s['get']]} | {COMMERCIAL[s['commercial']]} | {s['url']}")
        return 0
    text = (a.find or "").lower()
    rows = [x for x in packs["packs"] if (not a.kind or x["kind"] == a.kind) and (not a.source or a.source.lower() in x["source"].lower()) and text in (x["name"] + " " + x["use"]).lower()]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for x in rows:
            print(f"{x['kind']}: {x['name']} | {x['use']} | {x['licence']} | {x['mb']} MB | {x['page']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
