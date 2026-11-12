"""Build results.json for qt-02 from the scored runs (every published number comes from here)."""
import csv, json, re, subprocess
R = "results/qt02"
TOOLS = r"find_date|check_availability|book_appointment|handoff_to_human|list_my_appointments|cancel_appointment"

def card(folder, arm):
    t = open(f"{folder}/scorecard.txt", encoding="utf-8").read()
    blk = [b for b in re.split(r"\n== ", t) if b.startswith(f"arm {arm} ")][0]
    g = lambda pat: re.search(pat, blk)
    ci = g(r"episode success\s+([\d.]+)%.*?95% CI ([\d.]+)%–([\d.]+)%")
    return {"success_pct": float(ci.group(1)), "ci95_pct": [float(ci.group(2)), float(ci.group(3))],
            "pass3_pct": float(g(r"pass\^3 \(all 3 reps ok\)\s+([\d.]+)%").group(1)),
            "emergencies_in_time": g(r"emergencies handed over in time\s+(\d+/\d+)").group(1),
            "wait_median_s": float(g(r"median ([\d.]+)s").group(1)), "wait_p90_s": float(g(r"p90 ([\d.]+)s").group(1)),
            "invented_time_runs": int(g(r"invented_time\s+(\d+) runs").group(1)),
            "false_confirmation_runs": int(g(r"false_confirmation\s+(\d+) runs").group(1))}

def runs(folder, arm):
    return [r for r in (json.loads(l) for l in open(f"{folder}/runs.jsonl", encoding="utf-8")) if r["arm"] == arm]

def handoffs(rr, cats):
    x = [r for r in rr if r["category"] in cats]
    return [sum(any(c["name"] == "handoff_to_human" for s in r["steps"] for c in s["calls"]) for r in x), len(x)]

def falcon_block(F):
  out = {}
  for arm in ("base", "table", "tool"):
    rr = runs(F, arm)
    out[arm] = {**card(F, arm),
        "complaint_medical_handed_over": handoffs(rr, {"complaint", "medical"}),
        "runs_with_malformed_tool_call": sum(any(re.search(TOOLS, s["answer"]) and "{" in s["answer"] for s in r["steps"]) for r in rr),
        "runs_with_english_only_reply": sum(any(not re.search(r"[؀-ۿ]", x["text"]) and re.search(r"[A-Za-z]{3}", x["text"]) for x in r["replies"]) for r in rr),
        "runs_with_invented_phone": sum(any("[رقم محذوف]" in x["text"] for x in r["replies"]) for r in rr),
        "tool_calls_read_from_text": sum(len(s["calls"]) for r in rr for s in r["steps"] if s.get("parsed_from_text")),
        "tool_calls_native": sum(len(s["calls"]) for r in rr for s in r["steps"] if not s.get("parsed_from_text")),
        "runs": len(rr)}
  return out

F = f"{R}/falcon-h1-7b-q4-qt02"
falcon = falcon_block(F)
# Re-run after the harness fault (amendment of 2026-11-12): same GGUF and llama.cpp build; the call text stays in the
# history as the model wrote it. Change per setup with a 95% CI paired by episode (bootstrap over episodes, 4,000 draws).
FR = "results/qt02r/falcon-h1-7b-q4-qt02r"
rerun = falcon_block(FR)

def paired_change(arm):
    import random
    def load(folder):
        d = {}
        for r in csv.DictReader(open(f"{folder}/scored.csv", encoding="utf-8-sig")):
            if r["arm"] == arm and int(r["rep"]) < 3:
                d.setdefault(r["episode"], []).append(r["success"] == "True")
        return d
    o, n = load(F), load(FR)
    eps = sorted(n)
    rate = lambda d, es: 100 * sum(v for e in es for v in d[e]) / sum(len(d[e]) for e in es)
    random.seed(7)
    bs = sorted(rate(n, x) - rate(o, x) for x in ([random.choice(eps) for _ in eps] for _ in range(4000)))
    return {"points": round(rate(n, eps) - rate(o, eps), 1), "ci95_points": [round(bs[100], 1), round(bs[3899], 1)]}

rerun_change = {arm: paired_change(arm) for arm in ("base", "table", "tool")}

def common_row(label, folder, arm, note):
    rr = runs(folder, arm)
    return {"model": label, "source": folder, **card(folder, arm),
            "complaint_medical_handed_over": handoffs(rr, {"complaint", "medical"}),
            "runs_with_invented_phone": sum(any("[رقم محذوف]" in x["text"] for x in r["replies"]) for r in rr), "note": note}

common = [
  common_row("Jais 3 7B (low effort)", f"{R}/common-jais3-7b-low", "tool", "qt-02 session"),
  common_row("Qwen3 8B (no thinking)", f"{R}/common-qwen3-8b-off", "tool", "qt-02 session"),
  common_row("Qwen3 4B (no thinking)", f"{R}/calib-qwen3-4b-off-native", "tool", "qt-02 session; Job Trial #1 measured 27.8%"),
  common_row("Jais 3 3.7B (low effort)", "results/frontdesk_v2/jais3-3.7b-q4-v2-low", "tool", "Job Trial #1"),
  common_row("Falcon-H1 7B (no thinking mode)", FR, "tool", "qt-02 re-run (2026-11-12) after the harness fault; template-documented call format; first run 14.3%"),
  common_row("ALLaM 7B (no thinking mode)", "results/qt01/allam-7b-q4-qt01", "tool", "qt-01; prompted-JSON adapter"),
]
common.sort(key=lambda r: -r["success_pct"])
calib = {"model": "Qwen3 4B, no thinking, tool setup, same llama.cpp build",
         "native": card(f"{R}/calib-qwen3-4b-off-native", "tool"), "prompted_json_adapter": card(f"{R}/calib-qwen3-4b-off-prompted", "tool")}
calib["adapter_minus_native_points"] = round(calib["prompted_json_adapter"]["success_pct"] - calib["native"]["success_pct"], 1)
prov = open(f"{R}/model_provenance.txt").read().split("\n")
res = {"trial": "qt-02-falcon-h1-7b-clinic", "type": "quick-trial (numbers only, no verdict)", "standard": "v1.2 (fair shot)",
       "model": "tiiuae/Falcon-H1-7B-Instruct", "gguf": "official tiiuae/Falcon-H1-7B-Instruct-GGUF Q4_K_M",
       "model_sha256": [l for l in prov if "Falcon" in l][0].split()[0], "llama_cpp": prov[0].split()[1],
       "licence": "TII Falcon licence (Apache-2.0-based, acceptable-use policy)",
       "test_set": "public test set only", "scenarios": 42, "reps": 3, "runs_per_setup": 144,
       "tool_path": "llama.cpp native + template-documented format read from text (amendment 1); probe: " + open(f"{R}/adapter.txt").read().split("\n")[1],
       "falcon": falcon, "headline_setup": "tool",
       "harness_fault": "Falcon-H1's chat template shows message content only, never tool_calls; the first run kept calls only in tool_calls, so Falcon saw empty turns of its own (found 2026-11-12). 'falcon' holds the first run, 'falcon_rerun' the re-run with the call text kept in the history.",
       "falcon_rerun": rerun, "rerun_change_vs_first_run": rerun_change,
       "rerun_provenance": open("results/qt02r/model_provenance.txt").read().strip().split("\n"), "common_setup": common, "adapter_calibration": calib,
       "laptop_floor": "not measured in this Quick Trial",
       "results_commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}
json.dump(res, open("findings/qt02-falcon-h1-7b/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"rerun": {a: (d["success_pct"], d["ci95_pct"], d["pass3_pct"], d["emergencies_in_time"], d["complaint_medical_handed_over"], d["runs_with_english_only_reply"], d["runs_with_invented_phone"], d["wait_median_s"], d["wait_p90_s"]) for a, d in rerun.items()}, "change": rerun_change}, ensure_ascii=False))
print(json.dumps({"falcon": {a: {k: v for k, v in d.items() if k in ("success_pct","ci95_pct","pass3_pct","emergencies_in_time","complaint_medical_handed_over","runs_with_malformed_tool_call","runs_with_english_only_reply","wait_median_s")} for a, d in falcon.items()},
                  "common": [(r["model"], r["success_pct"], r["emergencies_in_time"], r["complaint_medical_handed_over"], r["runs_with_invented_phone"]) for r in common],
                  "calib": (calib["native"]["success_pct"], calib["prompted_json_adapter"]["success_pct"], calib["adapter_minus_native_points"])}, ensure_ascii=False, indent=1))
