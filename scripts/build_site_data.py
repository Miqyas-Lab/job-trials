#!/usr/bin/env python3
"""Builds assets/site-data.json, the data the home page and the trials index draw (site revamp, 26 Nov 2026).

    python3 scripts/build_site_data.py           writes assets/site-data.json
    python3 scripts/build_site_data.py --check   fails if the committed file differs from a fresh build

Reads site/index.yaml and the trials' findings/<slug>/results.json. Every number is read from a results.json
through a path ("slug:path", [key=value] picks a list item); none is typed. Run it after a new trial is added.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "site-data.json"
_cache: dict[str, dict] = {}


def results(slug: str) -> dict:
    if slug not in _cache:
        _cache[slug] = json.loads((ROOT / "findings" / slug / "results.json").read_text(encoding="utf-8"))
    return _cache[slug]


def get(ref: str):
    slug, path = ref.split(":", 1)
    cur = results(slug)
    for part in re.findall(r"[^.\[\]]+(?:\[[^\]]+\])?", path):
        m = re.fullmatch(r"([^\[]+)(?:\[([^=\]]+)=([^\]]+)\])?", part)
        name, k, v = m.groups()
        cur = cur[name]
        if k:
            hits = [x for x in cur if str(x.get(k)) == v]
            if len(hits) != 1:
                raise KeyError(f"{ref}: {len(hits)} items with {k}={v}")
            cur = hits[0]
    return cur


def number(x):
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return x
    raise ValueError(f"not a number: {x!r}")


def build(spec: dict) -> dict:
    models = spec["models"]
    views = []
    for v in spec["explorer"]:
        cards = []
        for c in v["cards"]:
            bars = []
            for name, ref in v["rows"].items():
                node = get(ref)
                for part in c["field"].split("."):
                    node = node[part]
                if v.get("count"):
                    got, of = (int(n) for n in node[v["count"]].split("/"))
                    bars.append({"name": name, "v": got, "of": of})
                elif c.get("diff"):
                    lo, hi = node["ci95_points"]
                    bars.append({"name": name, "v": number(node["points"]), "lo": number(lo), "hi": number(hi)})
                else:
                    lo, hi = node["ci95_pct"]
                    bars.append({"name": name, "v": number(node["success_pct"]), "lo": number(lo), "hi": number(hi)})
            cards.append({"title": c["title"], "sub": c["sub"], "diff": bool(c.get("diff")), "bars": bars})
        views.append({"id": v["id"], "label": v["label"], "text": v["text"], "kind": "count" if v.get("count") else "pct",
                      "latest": v.get("latest"), "note": f"المصدر: {v['source']}", "cards": cards})
    trials = []
    for t in spec["trials"]:
        bars = [{"label": label, "v": number(get(ref))} for label, ref in (t.get("bars") or {}).items()]
        trials.append({"slug": t["slug"], "type": t["type"], "type_label": spec["types"][t["type"]], "date": t["date"],
                       "title": t["title"], "metric": t["metric"], "model": t.get("model"), "bars": bars,
                       "url": f"/findings/{t['slug']}/"})
    return {"models": models, "types": spec["types"], "explorer": views, "trials": trials}


def main(argv) -> int:
    spec = yaml.safe_load((ROOT / "site" / "index.yaml").read_text(encoding="utf-8"))
    text = json.dumps(build(spec), ensure_ascii=False, indent=1) + "\n"
    if "--check" in argv:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != text:
            print("assets/site-data.json is not up to date: run python3 scripts/build_site_data.py")
            return 1
        print("assets/site-data.json is up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(spec['explorer'])} explorer views, {len(spec['trials'])} trials")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
