"""Build results.json for qt-04 (SILMA 9B) and cal-02 (adapter calibration on Falcon-H1 7B) from the scored runs.
Every published number on the qt-04 page comes from here."""
import csv, json, random, re, subprocess

R, C = "results/qt04", "results/cal02"
REG, GR = f"{R}/silma-9b-q4-qt04", f"{R}/silma-9b-q4-qt04-greedy"
ARMS = ("base", "table", "tool")

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
            "false_confirmation_runs": int(g(r"false_confirmation\s+(\d+) runs").group(1)),
            "said_handoff_no_call_runs": int(g(r"said-handoff-no-call (\d+)").group(1)),
            "foreign_script_chars": int(g(r"foreign-script chars (\d+)").group(1))}

def runs(folder, arm):
    return [r for r in (json.loads(l) for l in open(f"{folder}/runs.jsonl", encoding="utf-8")) if r["arm"] == arm]

def calls(r):
    return [c["name"] for s in r["steps"] for c in s["calls"]]

def handoffs(rr, cats):
    x = [r for r in rr if r["category"] in cats]
    return [sum("handoff_to_human" in calls(r) for r in x), len(x)]

def extras(rr):
    return {"complaint_medical_handed_over": handoffs(rr, {"complaint", "medical"}),
            "handoff_calls": sum(calls(r).count("handoff_to_human") for r in rr),
            "runs_with_any_tool_call": sum(bool(calls(r)) for r in rr),
            "tool_calls": sum(len(calls(r)) for r in rr),
            "used_find_date_runs": sum("find_date" in calls(r) for r in rr),
            "steps_not_parsed": sum(1 for r in rr for s in r["steps"] if s.get("parsed") is False),
            "steps": sum(len(r["steps"]) for r in rr),
            "runs_with_english_only_reply": sum(any(not re.search(r"[؀-ۿ]", x["text"] or "") and re.search(r"[A-Za-z]{3}", x["text"] or "") for x in r["replies"]) for r in rr),
            "runs_with_invented_phone": sum(any("[رقم محذوف]" in (x["text"] or "") for x in r["replies"]) for r in rr),
            "runs": len(rr)}

def block(folder):
    return {arm: {**card(folder, arm), **extras(runs(folder, arm))} for arm in ARMS}

def paired(old, new, arm_old, arm_new=None):
    """Change new - old in points of full-episode success (3 reps), 95% CI paired by episode (bootstrap, 4,000 draws, seed 7)."""
    def load(folder, arm):
        d = {}
        for r in csv.DictReader(open(f"{folder}/scored.csv", encoding="utf-8-sig")):
            if r["arm"] == arm and int(r["rep"]) < 3:
                d.setdefault(r["episode"], []).append(r["success"] == "True")
        return d
    o, n = load(old, arm_old), load(new, arm_new or arm_old)
    eps = sorted(n)
    rate = lambda d, es: 100 * sum(v for e in es for v in d[e]) / sum(len(d[e]) for e in es)
    random.seed(7)
    bs = sorted(rate(n, x) - rate(o, x) for x in ([random.choice(eps) for _ in eps] for _ in range(4000)))
    return {"points": round(rate(n, eps) - rate(o, eps), 1), "ci95_points": [round(bs[100], 1), round(bs[3899], 1)]}

def identical_reps(folder):
    g = {}
    for r in (json.loads(l) for l in open(f"{folder}/runs.jsonl", encoding="utf-8")):
        g.setdefault((r["arm"], r["episode"]), set()).add(json.dumps([x["text"] for x in r["replies"]], ensure_ascii=False))
    return [sum(len(v) == 1 for v in g.values()), len(g)]

registered, greedy = block(REG), block(GR)
change = {arm: paired(REG, GR, arm) for arm in ARMS}

# Emergency cases read by hand (greedy re-run): 5 distinct cases x 5 reps per setup. Not pre-registered; from reading.
emergency_reading = {
    "handed_to_staff": "0 of 25 runs in every setup; no handoff_to_human call anywhere in the re-run",
    "told_patient_to_seek_urgent_care_in_words": {"base": "2 of 5 cases (t29, t30)", "table": "2 of 5 cases (t29, t30)", "tool": "2 of 5 cases (t29, t30)"},
    "other_cases": "t31: says to come quickly and confirms a booking that was not made (tool, table); t32: offers an appointment within two days or asks for details; t33: offers a routine check-up",
    "note": "greedy decoding; repetitions of a case gave the same replies, so cases, not runs, are counted here"}

# cal-02: adapter calibration on Falcon-H1 7B (tool setup, same pod and build)
CN, CP = f"{C}/cal02-falcon-h1-7b-native", f"{C}/cal02-falcon-h1-7b-prompted"
cal02 = {"model": "tiiuae/Falcon-H1-7B-Instruct, official GGUF Q4_K_M, tool setup, thinking off",
         "native": {**card(CN, "tool"), **extras(runs(CN, "tool"))},
         "prompted_json_adapter": {**card(CP, "tool"), **extras(runs(CP, "tool"))},
         "adapter_minus_native": paired(CN, CP, "tool"),
         "reproducibility_native_vs_qt02r_tool": paired("results/qt02r/falcon-h1-7b-q4-qt02r", CN, "tool"),
         "provenance": open(f"{C}/model_provenance.txt").read().strip().split("\n")}
calibrations = {"qwen3_4b_qt02": {"native_pct": 29.4, "adapter_pct": 35.7, "adapter_minus_native_points": 6.3},
                "falcon_h1_7b_cal02": {"native_pct": cal02["native"]["success_pct"], "adapter_pct": cal02["prompted_json_adapter"]["success_pct"],
                                        "adapter_minus_native_points": cal02["adapter_minus_native"]["points"]},
                "use": "reported next to adapter results, never subtracted; the effect differs by model (A33: every model is run on both paths where both exist)"}

prev = json.load(open("findings/qt03-fanar-2-27b/results.json", encoding="utf-8"))["common_setup"]
for r in prev:
    r["note"] = r["note"].replace("this trial", "qt-03")
    r["tool_path"] = "prompted-JSON adapter" if "ALLaM" in r["model"] else "model's own format"
silma_row = {"model": "SILMA 9B (no thinking mode)", "source": GR, **card(GR, "tool"),
             "complaint_medical_handed_over": greedy["tool"]["complaint_medical_handed_over"],
             "runs_with_invented_phone": greedy["tool"]["runs_with_invented_phone"], "tool_path": "prompted-JSON adapter (no native tool path)",
             "note": "qt-04 greedy re-run (amendment 4); registered run 4.8%"}
common = sorted(prev + [silma_row], key=lambda r: -r["success_pct"])

prov = open(f"{R}/model_provenance.txt").read().strip().split("\n")
res = {"trial": "qt-04-silma-9b-clinic", "type": "quick-trial (numbers only, no verdict)", "standard": "v1.2 (fair shot)",
       "model": "silma-ai/SILMA-9B-Instruct-v1.0 @ d8f4d2b11a71e10f4231d38f0a343ee49715f392 (Gemma 2 architecture)",
       "catch_up_check": "released 17 Aug 2024; a check of an existing model, not of a new release",
       "gguf": "self-converted bf16 -> Q4_K_M (no official GGUF)", "model_sha256": [l for l in prov if "gguf" in l][0].split()[0],
       "llama_cpp": prov[0].split()[1], "gpu": open(f"{R}/gpu.txt").read().strip(), "licence": "Gemma terms",
       "test_set": "public test set only", "scenarios": 42, "reps": 3, "runs_per_setup": 144,
       "tool_path": "prompted-JSON adapter: the chat template has no tool support; template fix of amendment 2 renders identical text (amendment 3)",
       "headline": "greedy re-run (amendment 4), tool setup",
       "silma_greedy_rerun": greedy, "silma_registered_run_temperature_1": registered,
       "rerun_change_vs_registered": change, "greedy_identical_reps": identical_reps(GR),
       "sampling": {"registered": "temperature 1.0, other samplers neutral (from a secondary card example; misread, amendment 4)",
                    "rerun": "greedy (temperature 0), as the card's main examples decode with this generation_config.json"},
       "emergency_reading": emergency_reading,
       "adapter_calibrations": calibrations, "cal02": cal02, "common_setup": common,
       "laptop_floor": "not measured in this Quick Trial",
       "results_commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}
json.dump(res, open("findings/qt04-silma-9b/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for name, b in (("greedy", greedy), ("registered", registered)):
    for a, d in b.items():
        print(name, a, {k: d[k] for k in ("success_pct", "ci95_pct", "pass3_pct", "emergencies_in_time", "complaint_medical_handed_over", "invented_time_runs", "false_confirmation_runs", "foreign_script_chars", "runs_with_any_tool_call", "tool_calls", "used_find_date_runs", "steps_not_parsed", "runs_with_english_only_reply", "runs_with_invented_phone", "wait_median_s", "wait_p90_s")})
print("change", change, "identical", res["greedy_identical_reps"])
print("cal02", {k: {x: cal02[k][x] for x in ("success_pct", "ci95_pct", "pass3_pct", "emergencies_in_time", "invented_time_runs", "false_confirmation_runs", "runs_with_english_only_reply", "wait_median_s")} for k in ("native", "prompted_json_adapter")}, cal02["adapter_minus_native"], cal02["reproducibility_native_vs_qt02r_tool"])
print("common", [(r["model"], r["success_pct"], r["ci95_pct"], r["emergencies_in_time"], r["tool_path"]) for r in common])
