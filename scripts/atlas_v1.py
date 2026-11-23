#!/usr/bin/env python3
"""
miqyas · Failure Atlas v1 for the clinic front desk (Job Trial #1): every failing run, tagged by rule.

Run from the repository root:  python3 scripts/atlas_v1.py
Scores every run of the six published setups with scripts/score_v2.py, applies the recorded human review of every
critical flag (results/frontdesk_v2/flags_review_v2.py), and gives each failing run one or more CAUSE tags from its
evidence (the clinic's final state against the accepted end states, the tool calls, the reviewed flags) and one
SITUATION tag from its episode's category, under atlas/taxonomy_v1.yaml. A failure no rule explains is marked
needs_review, never guessed. Writes findings/frontdesk-v2/failures.jsonl (one row per failing run).
"""
import datetime as dt
import json
import os
import sys
from collections import Counter

os.environ.setdefault("MIQYAS_CLINIC", "dubai")
sys.path.insert(0, "scripts")
import score_v2 as S  # noqa: E402
import yaml  # noqa: E402

FOLDERS = {
    "jais3-3.7b-q4-v2": ("Jais 3 3.7B", "results/frontdesk_v2/jais3-3.7b-q4-v2"),
    "jais3-7b-q4-v2": ("Jais 3 7B", "results/frontdesk_v2/jais3-7b-q4-v2"),
    "qwen3-8b-q4-v2": ("Qwen3-8B", "results/frontdesk_v2/qwen3-8b-q4-v2"),
    "qwen3-4b-q4-v2": ("Qwen3-4B", "results/frontdesk_v2/qwen3-4b-q4-v2"),
    "jais3-3.7b-q4-v2-low": ("Jais 3 3.7B, low effort", "results/frontdesk_v2/jais3-3.7b-q4-v2-low"),
    "qwen3-4b-q4-v2-off": ("Qwen3-4B, thinking off", "results/frontdesk_v2/qwen3-4b-q4-v2-off"),
}
CRITICAL = ("invented_time", "false_confirmation", "cap", "loop", "silent_turn")
TAX = yaml.safe_load(open("atlas/taxonomy_v1.yaml", encoding="utf-8"))
ns = {}
exec(open("results/frontdesk_v2/flags_review_v2.py", encoding="utf-8").read(), ns)
REVIEW = ns["REVIEW"]
EPS = {json.loads(l)["id"]: json.loads(l) for l in open("corpus/frontdesk_v2.jsonl", encoding="utf-8") if l.strip()}


def booking_gap(ep, run):
    added = run["final"]["added"]
    wants = [w for opt in ep["accept"] for w in opt["book"]]
    if not wants:
        return set()
    if not added:
        return {"none"}
    best = None
    for w in wants:
        for g in added:
            d = set()
            if g["service"] != w["service"]:
                d.add("service")
            if g["date"] not in w["date"]:
                d.add("date")
            if w["time"] != "*" and g["time"] != w["time"]:
                d.add("time")
            if not any(S.name_ok(n, g["patient_name"]) for n in w["names"]):
                d.add("name")
            if best is None or len(d) < len(best):
                best = d
    return best or set()


def relevant_dates(ep, wanted):
    """Days a correct receptionist might look up: the day wanted, a day the episode makes full or taken, Fridays."""
    out = set(wanted)
    for key in ("full", "taken"):
        out |= {x[0] for x in (ep.get("clinic") or {}).get(key, [])}
    start = dt.date(2026, 11, 5)
    out |= {(start + dt.timedelta(days=i)).isoformat() for i in range(31) if (start + dt.timedelta(days=i)).weekday() == 4}
    return out


def causes(ep, run, row):
    why, ok = row["why"], row["state_ok"]
    tools = [e["tool"] for e in run["events"]]
    booked_ok = any(e["tool"] == "book_appointment" and e["result"].get("ok") for e in run["events"])
    out = []
    if not ok and why.startswith("missing/wrong booking"):
        gap = booking_gap(ep, run)
        if gap == {"none"}:
            out.append("tool_discipline" if "book_appointment" in tools and not booked_ok else "unfinished")
        else:
            if gap & {"date", "time"}:
                out.append("dates_times")
            if gap & {"service", "name"}:
                out.append("wrong_details")
    if not ok and why.startswith("wrong cancellation"):
        removed, added = run["final"]["removed"], run["final"]["added"]
        wanted_cancel = {c for opt in ep["accept"] for c in opt["cancel"]}
        out.append("state_tracking" if (removed or added or not wanted_cancel) else "unfinished")
    if not ok and why.startswith("unexpected booking"):
        out.append("state_tracking")
    if not ok and (why.startswith("no handoff") or why.startswith("handoff ") or why.startswith("unneeded handoff")):
        out.append("safety_handover")
    if not ok and why.startswith("required info missing"):
        out.append("missing_information")
    if not ok and why.startswith("forbidden content"):
        out.append("wrong_content")
    if row["invented_time"]:
        out.append("dates_times")
    wanted = {d for opt in ep["accept"] for w in opt["book"] for d in w["date"]}
    used = [e["args"].get("date") for e in run["events"]
            if e["tool"] in ("check_availability", "book_appointment") and e.get("args", {}).get("date")]
    if wanted and used and not (set(used) & relevant_dates(ep, wanted)):
        out.append("dates_times")
    if row["false_confirmation"] or row.get("said_handoff_no_call"):
        out.append("false_claim")
    if row.get("booked_unverified") or row["loop"] or row["cap"] or row.get("unknown_tool") or row.get("tool_errors_bad_args"):
        out.append("tool_discipline")
    if row["silent_turn"]:
        out.append("unfinished")
    return sorted(set(out))


def situation(category):
    return next((n for n, s in TAX["situations"].items() if category in s["categories"]), "unknown")


rows_out, total = [], 0
for cfg, (model, folder) in FOLDERS.items():
    _, _, rows = S.load(folder)
    runs = {}
    for l in open(f"{folder}/runs.jsonl", encoding="utf-8"):
        r = json.loads(l)
        runs[(r["episode"], r["arm"], r["effort"], r["rep"])] = r
    for row in rows:
        if "error" in row:
            continue
        for f in ("invented_time", "false_confirmation"):
            d = REVIEW.get((cfg, row["episode"], row["arm"], row["rep"], f))
            if row[f] and d and d[0] == "cleared":
                row[f] = False
        row["success"] = row["state_ok"] and not any(row[c] for c in CRITICAL)
        total += 1
        if row["success"]:
            continue
        run = runs[(row["episode"], row["arm"], row["effort"], row["rep"])]
        ep = EPS[row["episode"]]
        tags = causes(ep, run, row)
        rows_out.append({"job": "clinic-frontdesk", "trial": "jt-01-frontdesk-v2", "taxonomy": TAX["version"],
                         "model": model, "config": cfg, "machine": "NVIDIA GeForce RTX 4090", "arm": row["arm"],
                         "effort": row["effort"], "episode": row["episode"], "rep": row["rep"],
                         "category": row["category"], "situation": situation(row["category"]), "causes": tags,
                         "needs_review": not tags, "scorer_reason": row["why"],
                         "state": {"booked": run["final"]["added"], "cancelled": run["final"]["removed"],
                                   "handoffs": run["final"]["handoffs"], "accepted": ep["accept"]},
                         "transcript": f"{folder}/runs.jsonl", "page": "https://miqyaslab.com/findings/frontdesk-v2/"})
with open("findings/frontdesk-v2/failures.jsonl", "w", encoding="utf-8") as f:
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows_out)
c = Counter(t for r in rows_out for t in r["causes"])
print(f"{total} runs, {len(rows_out)} failures, {sum(r['needs_review'] for r in rows_out)} need review; "
      + ", ".join(f"{k} {v}" for k, v in c.most_common()))
