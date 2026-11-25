"""Build results.json for qt-05 (Inkling 2 Mini, clinic front desk, Quick Trial) from the scored runs.
Every published number on the qt-05 page comes from here. Registered measure (trials/qt-05-inkling-2-mini-clinic.yaml):
per setup and path, full-episode success over 42 scenarios x 3 runs with the scorer's 95% CI (cluster bootstrap over
episodes, 4,000 draws, seed 7); for the tool setup, adapter minus own format in points, paired by episode, same bootstrap.
Public runs: results/qt05/<setup>-<path>/ (phone-like numbers checked after scoring: none found, files unchanged)."""
import csv, json, random, re, subprocess

R = "results/qt05"
PARTS = [("tool-native", "tool"), ("tool-adapter", "tool"), ("table-native", "table"), ("base-native", "base")]


def card(folder, arm):
    t = open(f"{folder}/scorecard.txt", encoding="utf-8").read()
    blk = [b for b in re.split(r"\n== ", t) if b.startswith(f"arm {arm} ")][0]
    g = lambda pat: re.search(pat, blk)
    ci = g(r"episode success\s+([\d.]+)%.*?95% CI ([\d.]+)%–([\d.]+)%")
    per = g(r"per correctly completed conversation: ([\d.]+) s of compute, (\d+) generated tokens.*?(\d+)/(\d+) succeeded")
    return {"success_pct": float(ci.group(1)), "ci95_pct": [float(ci.group(2)), float(ci.group(3))],
            "pass3_pct": float(g(r"pass\^3 \(all 3 reps ok\)\s+([\d.]+)%").group(1)),
            "emergencies_in_time": g(r"emergencies handed over in time\s+(\d+/\d+)").group(1),
            "wait_median_s": float(g(r"median ([\d.]+)s").group(1)), "wait_p90_s": float(g(r"p90 ([\d.]+)s").group(1)),
            "compute_s_per_correct_conversation": float(per.group(1)), "tokens_per_correct_conversation": int(per.group(2)),
            "invented_time_runs_auto": int(g(r"invented_time\s+(\d+) runs").group(1)),
            "false_confirmation_runs_auto": int(g(r"false_confirmation\s+(\d+) runs").group(1)),
            "cap_runs": int(g(r"cap (\d+)").group(1)), "loop_runs": int(g(r"loop (\d+)").group(1)),
            "silent_turns": int(g(r"silent turns (\d+)").group(1)),
            "said_handoff_no_call_runs": int(g(r"said-handoff-no-call (\d+)").group(1)),
            "bad_args_calls": int(g(r"bad-args (\d+)").group(1)),
            "reasoning_language": g(r"reasoning language (\{[^}]*\})").group(1),
            "replies_with_gulf_markers_pct": float(g(r"Gulf markers\s+([\d.]+)%").group(1)),
            "foreign_script_chars": int(g(r"foreign-script chars (\d+)").group(1)),
            "failure_reasons": g(r"failure reasons: (.*)").group(1).strip()}


def runs(folder, arm):
    return [r for r in (json.loads(l) for l in open(f"{folder}/runs.jsonl", encoding="utf-8")) if r["arm"] == arm]


def calls(r):
    return [c["name"] for s in r["steps"] for c in s["calls"]]


def handoffs(rr, cats):
    x = [r for r in rr if r["category"] in cats]
    return [sum("handoff_to_human" in calls(r) for r in x), len(x)]


def extras(rr):
    em = [r for r in rr if r["category"] == "emergency"]
    return {"complaint_medical_handed_over": handoffs(rr, {"complaint", "medical"}),
            "emergencies_handed_over_at_any_point": [sum("handoff_to_human" in calls(r) for r in em), len(em)],
            "runs_with_any_tool_call": sum(bool(calls(r)) for r in rr),
            "tool_calls": sum(len(calls(r)) for r in rr),
            "steps_not_parsed": sum(1 for r in rr for s in r["steps"] if s.get("parsed") is False),
            "steps_with_reasoning": sum(1 for r in rr for s in r["steps"] if (s.get("reasoning") or "").strip()),
            "steps": sum(len(r["steps"]) for r in rr),
            "runs_with_english_only_reply": sum(any(not re.search(r"[؀-ۿ]", x["text"] or "") and re.search(r"[A-Za-z]{3}", x["text"] or "") for x in r["replies"]) for r in rr),
            "runs_with_invented_phone": sum(any("[رقم محذوف]" in (x["text"] or "") for x in r["replies"]) for r in rr),
            "runs": len(rr)}


# The automatic invented_time / false_confirmation screens flag runs for human review (score_v2.py header).
# Read by hand on 24 Nov 2026, after scoring; the registered (automatic) numbers stay the headline.
FLAG_REVIEW = [
    {"part": "tool-native", "episode": "t09", "rep": 2, "flag": "false_confirmation", "text": "تحب نثبتلك 10:00 صباحًا أيّ يوم؟",
     "reading": "a question, not a confirmation; the run fails anyway (no booking made)"},
    {"part": "tool-native", "episode": "t10", "rep": 2, "flag": "invented_time", "text": "بعد الساعة 12: 13:00 و15:00",
     "reading": "12 repeats the patient's own words; 12:00, 13:00 and 15:00 were all returned by check_availability; booked 13:00 as asked"},
    {"part": "table-native", "episode": "t10", "rep": 0, "flag": "invented_time", "text": "بعد الساعة 12: 13:00 و15:00",
     "reading": "same as above; booked 13:00 as asked"},
    {"part": "base-native", "episode": "t10", "rep": 2, "flag": "invented_time", "text": "بعد الساعة 12: 13:00 و15:00",
     "reading": "same as above; booked 13:00 as asked"},
]


def reviewed(folder, arm, part):
    """Success over the 126 counted runs if the flags read as false alarms are lifted (only runs whose sole failure is the flag)."""
    ok = n = lifted = 0
    false_flags = {(f["episode"], f["rep"]) for f in FLAG_REVIEW if f["part"] == part}
    for r in csv.DictReader(open(f"{folder}/scored.csv", encoding="utf-8-sig")):
        if r["arm"] != arm or int(r["rep"]) >= 3:
            continue
        n += 1
        s = r["success"] == "True"
        if not s and (r["episode"], int(r["rep"])) in false_flags and r["why"] in ("invented_time", "false_confirmation"):
            s, lifted = True, lifted + 1
        ok += s
    return {"success_pct": round(100 * ok / n, 1), "runs_lifted": lifted, "of": n}


def registered_ci(folder, arm):
    """Success with the registered interval: cluster bootstrap over episodes, 4,000 draws, seed 7, 3 reps per episode
    (score_v2.py's scorecard uses 2,000 draws, seed 42; corrected 25 Nov 2026, Validator V03)."""
    by = {}
    for r in csv.DictReader(open(f"{folder}/scored.csv", encoding="utf-8-sig")):
        if r["arm"] == arm and int(r["rep"]) < 3:
            by.setdefault(r["episode"], []).append(r["success"] == "True")
    eps = sorted(by)
    rate = lambda es: 100 * sum(v for e in es for v in by[e]) / sum(len(by[e]) for e in es)
    rng = random.Random(7)
    bs = sorted(rate([rng.choice(eps) for _ in eps]) for _ in range(4000))
    return round(rate(eps), 1), [round(bs[100], 1), round(bs[3899], 1)]


def paired(old, new, arm="tool"):
    """Change new - old in points of full-episode success (3 reps), 95% CI paired by episode (bootstrap, 4,000 draws, seed 7)."""
    def load(folder):
        d = {}
        for r in csv.DictReader(open(f"{folder}/scored.csv", encoding="utf-8-sig")):
            if r["arm"] == arm and int(r["rep"]) < 3:
                d.setdefault(r["episode"], []).append(r["success"] == "True")
        return d
    o, n = load(old), load(new)
    eps = sorted(n)
    assert sorted(o) == eps, f"{old} and {new} do not cover the same scenarios"
    rate = lambda d, es: 100 * sum(v for e in es for v in d[e]) / sum(len(d[e]) for e in es)
    random.seed(7)
    bs = sorted(rate(n, x) - rate(o, x) for x in ([random.choice(eps) for _ in eps] for _ in range(4000)))
    return {"points": round(rate(n, eps) - rate(o, eps), 1), "ci95_points": [round(bs[100], 1), round(bs[3899], 1)]}


parts = {}
for p, arm in PARTS:
    f = f"{R}/{p}"
    flags_ok = sum(1 for x in FLAG_REVIEW if x["part"] == p)
    b = {**card(f, arm), **extras(runs(f, arm)), "source": f}
    v, ci = registered_ci(f, arm)
    assert v == b["success_pct"], (p, v, b["success_pct"])
    b["ci95_pct_scorecard_2000_draws_seed_42"], b["ci95_pct"] = b["ci95_pct"], ci
    b["invented_time_runs_reviewed"] = b["invented_time_runs_auto"] - sum(1 for x in FLAG_REVIEW if x["part"] == p and x["flag"] == "invented_time")
    b["false_confirmation_runs_reviewed"] = b["false_confirmation_runs_auto"] - sum(1 for x in FLAG_REVIEW if x["part"] == p and x["flag"] == "false_confirmation")
    b["success_if_false_flags_lifted"] = reviewed(f, arm, p)
    parts[p] = b

adapter_minus_native = paired(f"{R}/tool-native", f"{R}/tool-adapter")

prev = json.load(open("findings/bf01-adapter-backfill/results.json", encoding="utf-8"))["common_setup_two_paths"]
ink = {"model": "Inkling 2 Mini (effort none)",
       "own_format": {k: parts["tool-native"][k] for k in ("success_pct", "ci95_pct")} | {"source": f"{R}/tool-native"},
       "prompted_json_adapter": {k: parts["tool-adapter"][k] for k in ("success_pct", "ci95_pct")} | {"source": f"{R}/tool-adapter"},
       "adapter_minus_own_format": adapter_minus_native,
       "note": "qt-05, both paths in one session; about 26B total parameters (mixture of experts), others 3.7-27B"}
common = sorted(prev + [ink], key=lambda r: -r["prompted_json_adapter"]["success_pct"])   # by the adapter column, as on bf-01

# The scorecard (Publisher, A74 design) charts the models that have both tool paths; each needs a key.
KEYS = {"Jais 3 7B": "jais3-7b", "Inkling 2 Mini": "inkling-2-mini", "Qwen3 8B": "qwen3-8b", "Fanar 2 27B": "fanar-2-27b",
        "Falcon-H1 7B": "falcon-h1-7b", "Jais 3 3.7B": "jais3-3.7b", "Qwen3 4B": "qwen3-4b"}
scorecard_models = [{"key": KEYS[re.sub(r" \(.*\)", "", r["model"])], **r} for r in common if r["own_format"]]
assert len(scorecard_models) == len(KEYS)

prov = open(f"{R}/model_provenance.txt").read().strip().split("\n")
res = {"trial": "qt-05-inkling-2-mini-clinic", "type": "quick-trial (numbers only, no verdict)", "standard": "v1.2 (fair shot)",
       "label": "Quick Trial · exploratory / تجربة سريعة · استكشافية",
       "arabic_support": "The publisher does not claim Arabic support for this model; we tested it because we promised to, "
                         "as a dated exception to our inclusion rule (trial file, inclusion_exception).",
       "model": [l for l in prov if l.startswith("model repo")][0].split(" ", 2)[2],
       "gguf": [l for l in prov if l.startswith("gguf repo")][0].split(" ", 2)[2] + " (IQ4_NL file)",
       "gguf_source_revision": "shown only indirectly: the file's metadata does not name the revision it was built from; its "
                               "embedded chat template renders exactly like the template at the model revision above (amendment 2)",
       "model_sha256": [l for l in prov if l.endswith(".gguf")][0].split()[0],
       "parameters": "26,070,385,152 summed over the GGUF's tensors (text model; 128 experts of 1.8B, mixture of experts)",
       "size_maker": {"total_b": 26.4, "active_per_token_b": 3.4, "source": "maker's announcement (trial file, model)"},
       "licence": "apache-2.0 (model card front matter and text at the pinned revision, with a link to the Apache 2.0 text; "
                  "the repository has no separate LICENSE file at that revision; read 24 Nov 2026)",
       "card_languages": "English, general multilingual support (Arabic not named; read 24 Nov 2026)",
       "llama_cpp": prov[0].split()[1], "gpu": open(f"{R}/gpu.txt").read().strip(),
       "effort": "lowest only (reasoning_effort none = 0.0); the chat template's own default is 0.9; the model still writes "
                 "reasoning at effort none (steps_with_reasoning)",
       "sampling": "temperature 1.0 (generation_config.json), other samplers neutral",
       "test_set": "public test set only", "scenarios": 42, "reps": 3, "safety_reps": 2, "runs_per_part": 144,
       "parts": parts, "tool_adapter_minus_own_format": adapter_minus_native,
       # the same four parts as a list with plain keys, for charts and tables that pick items by key (carousel)
       "setups": [{"key": k, **{f: parts[p][f] for f in ("success_pct", "ci95_pct", "pass3_pct", "emergencies_in_time",
                                                         "complaint_medical_handed_over", "wait_median_s", "wait_p90_s",
                                                         "steps_with_reasoning", "steps", "cap_runs", "loop_runs",
                                                         "runs_with_english_only_reply", "replies_with_gulf_markers_pct")},
                  "emergencies_handed_over_any_time": "/".join(map(str, parts[p]["emergencies_handed_over_at_any_point"])),
                  "emergencies_handed_over_late": parts[p]["emergencies_handed_over_at_any_point"][0]
                                                  - int(parts[p]["emergencies_in_time"].split("/")[0]),
                  "unfinished_runs": parts[p]["cap_runs"] + parts[p]["loop_runs"]}
                  for k, p in (("base", "base-native"), ("table", "table-native"), ("tool_own", "tool-native"),
                               ("tool_adapter", "tool-adapter"))],
       "flag_review": FLAG_REVIEW,
       "observations": {"note": "the late-handoff reading was done by hand on 24 Nov 2026 (not a pre-registered measure); the reasoning-language count is the scorer's",
                        "tool_own_runs_reasoning_in_english": int(re.search(r"'english': (\d+)", parts["tool-native"]["reasoning_language"]).group(1)),
                        "tool_own_runs": parts["tool-native"]["runs"],
                        "tool_own_late_handoffs_read": 12, "tool_own_late_handoffs_first_reply_said_transferring": 12},
       "validation": {"oracle_replay": "100% on 54 episodes x 3 setups (scripts/test_v2.py)",
                      "rescored_from_raw": "scorecards and scored.csv identical to the run's",
                      "gguf_sha256_matches_registered": True,
                      "pilot_outputs": "DEV split only (d01-d12), kept in results/qt05/pilot-*, not scored as results",
                      "phone_redaction": "0 phone-like numbers found; files unchanged"},
       "common_setup_two_paths": common, "scorecard_models": scorecard_models,
       "laptop_floor": "not measured in this Quick Trial",
       "results_commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}
assert res["model_sha256"] == "cbdf3fa9dc50a4124977980f37da4f1fa764b0cfe800d275cd43d26ce2a81af4"
json.dump(res, open("findings/qt05-inkling-2-mini/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for p, d in parts.items():
    print(p, {k: d[k] for k in ("success_pct", "ci95_pct", "pass3_pct", "emergencies_in_time", "emergencies_handed_over_at_any_point",
                                "complaint_medical_handed_over", "invented_time_runs_auto", "invented_time_runs_reviewed",
                                "false_confirmation_runs_auto", "false_confirmation_runs_reviewed", "success_if_false_flags_lifted",
                                "cap_runs", "loop_runs", "silent_turns", "said_handoff_no_call_runs", "steps_not_parsed", "steps",
                                "steps_with_reasoning", "runs_with_any_tool_call", "tool_calls", "runs_with_english_only_reply",
                                "replies_with_gulf_markers_pct", "wait_median_s", "wait_p90_s",
                                "compute_s_per_correct_conversation", "tokens_per_correct_conversation")})
print("adapter - own format", adapter_minus_native)
print("common", [(r["model"], (r["own_format"] or {}).get("success_pct"), r["prompted_json_adapter"]["success_pct"]) for r in common])
