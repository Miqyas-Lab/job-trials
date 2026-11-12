"""Build results.json for qt-03 from the scored runs (every published number comes from here)."""
import json, re, subprocess
R = "results/qt03"
N = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
TOOLS = r"find_date|check_availability|book_appointment|handoff_to_human|list_my_appointments|cancel_appointment"

def card(folder, arm, eff=None):
    t = open(f"{folder}/scorecard.txt", encoding="utf-8").read()
    blk = [b for b in re.split(r"\n== ", t) if b.startswith(f"arm {arm} ") and (eff is None or f"effort {eff}" in b.split("\n")[0])][0]
    g = lambda pat: re.search(pat, blk)
    ci = g(r"episode success\s+([\d.]+)%.*?95% CI ([\d.]+)%–([\d.]+)%")
    return {"success_pct": float(ci.group(1)), "ci95_pct": [float(ci.group(2)), float(ci.group(3))],
            "pass3_pct": float(g(r"pass\^3 \(all 3 reps ok\)\s+([\d.]+)%").group(1)),
            "emergencies_in_time": g(r"emergencies handed over in time\s+(\d+/\d+)").group(1),
            "wait_median_s": float(g(r"median ([\d.]+)s").group(1)), "wait_p90_s": float(g(r"p90 ([\d.]+)s").group(1)),
            "invented_time_runs": int(g(r"invented_time\s+(\d+) runs").group(1)),
            "false_confirmation_runs": int(g(r"false_confirmation\s+(\d+) runs").group(1)),
            "loop_runs": int(g(r"loop (\d+)").group(1)), "silent_turns": int(g(r"silent turns (\d+)").group(1))}

def runs(folder, arm):
    return [r for r in (json.loads(l) for l in open(f"{folder}/runs.jsonl", encoding="utf-8")) if r["arm"] == arm]

def handoffs(rr, cats):
    x = [r for r in rr if r["category"] in cats]
    return [sum(any(c["name"] == "handoff_to_human" for s in r["steps"] for c in s["calls"]) for r in x), len(x)]

def half_hour(rr):   # post-hoc observation: booking calls after a patient says «X ونص»
    tot = whole = indic = 0
    for r in rr:
        for t in r["turns"]:
            if "ونص" not in t["patient"]: continue
            bk = [c for s in r["steps"] if s.get("turn") == t["turn"] for c in s["calls"] if c["name"] == "book_appointment"]
            if not bk: continue
            raw = str(bk[-1]["args"].get("time", "")); tm = raw.translate(N); tot += 1
            indic += raw != tm; whole += not tm.endswith(":30")
    return {"booking_calls_after_wnus": tot, "booked_whole_hour": whole, "time_in_arabic_indic_digits": indic}

def extras(rr):
    return {"complaint_medical_handed_over": handoffs(rr, {"complaint", "medical"}),
            "runs_with_malformed_tag_in_reply": sum(any(re.search(r"</?(think|tool_call)[a-z_]*>", x["text"] or "") for x in r["replies"]) for r in rr),
            "runs_with_english_only_reply": sum(any(not re.search(r"[؀-ۿ]", x["text"] or "") and re.search(r"[A-Za-z]{3}", x["text"] or "") for x in r["replies"]) for r in rr),
            "runs_with_invented_phone": sum(any("[رقم محذوف]" in (x["text"] or "") for x in r["replies"]) for r in rr),
            "steps_with_reasoning": sum(1 for r in rr for s in r["steps"] if (s.get("reasoning") or "").strip()),
            "steps": sum(len(r["steps"]) for r in rr),
            "used_find_date_runs": sum(any(c["name"] == "find_date" for s in r["steps"] for c in s["calls"]) for r in rr),
            "runs": len(rr)}

F, FT = f"{R}/fanar-2-27b-q4-qt03", f"{R}/fanar-2-27b-q4-qt03-think"
fanar = {arm: {**card(F, arm), **extras(runs(F, arm))} for arm in ("base", "table", "tool")}
fanar["tool_thinking_on"] = {**card(FT, "tool", "on"), **extras(runs(FT, "tool"))}
obs = {"tool": half_hour(runs(F, "tool")), "tool_thinking_on": half_hour(runs(FT, "tool"))}

prev = json.load(open("findings/qt02-falcon-h1-7b/results.json", encoding="utf-8"))["common_setup"]
for r in prev:   # rows copied from qt-02 say "this trial" there; name the session here (fixed 2026-11-12)
    r["note"] = r["note"].replace("this trial", "qt-02")
fan_row = {"model": "Fanar 2 27B (thinking off)", "source": F, **card(F, "tool"),
           "complaint_medical_handed_over": handoffs(runs(F, "tool"), {"complaint", "medical"}),
           "runs_with_invented_phone": 0, "note": "this trial; template-documented call format; 27B (others 3.7-8B)"}
common = sorted(prev + [fan_row], key=lambda r: -r["success_pct"])

prov = open(f"{R}/model_provenance.txt").read().split("\n")
res = {"trial": "qt-03-fanar-2-27b-clinic", "type": "quick-trial (numbers only, no verdict)", "standard": "v1.2 (fair shot)",
       "model": "QCRI/Fanar-2-27B-Instruct @ 074005040e9c3511b1c43b4298bef09908285534 (Gemma-3-27B base, continually pretrained)",
       "gguf": "self-converted bf16 -> Q4_K_M", "model_sha256": [l for l in prov if "gguf" in l][0].split()[0],
       "llama_cpp": prov[0].split()[1], "gpu": open(f"{R}/gpu.txt").read().strip(), "licence": "Apache-2.0 (model card)",
       "sampling": "temperature 0.7 (model card; generation_config.json sets none), other values neutral",
       "test_set": "public test set only", "scenarios": 42, "reps": 3, "runs_per_setup": 144,
       "tool_path": "probe chose native (" + open(f"{R}/adapter.txt").read().split("\n")[1] + "); 0 native calls in DEV pilot 1 -> template-documented reader (pre-registered rule step 2); amendments 1-3",
       "fanar": fanar, "headline_setup": "tool, thinking off", "common_setup": common,
       "post_hoc_observations": {"half_hour_wnus": obs,
            "half_hour_reference_tool_setup": "Qwen3 8B 0/35 whole-hour, Jais 3 7B 0/33 (qt-02 session rows)",
            "note": "not pre-registered; counted from raw runs after reading failures"},
       "laptop_floor": "not measured; a 27B model does not fit 8 GB",
       "results_commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}
json.dump(res, open("findings/qt03-fanar-2-27b/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for a, d in fanar.items():
    print(a, {k: d[k] for k in ("success_pct", "ci95_pct", "pass3_pct", "emergencies_in_time", "complaint_medical_handed_over", "wait_median_s", "wait_p90_s", "loop_runs", "silent_turns", "runs_with_english_only_reply", "runs_with_malformed_tag_in_reply", "steps_with_reasoning", "steps", "used_find_date_runs")})
print("common:", [(r["model"], r["success_pct"], r["emergencies_in_time"]) for r in common])
print("obs:", obs)
