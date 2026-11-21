"""Build results.json for bf-01 (adapter back-fill) from the scored runs. Every published number on the bf-01 page
comes from here. Registered measure (trials/bf-01-adapter-backfill.yaml): per model, adapter minus own format in the
same session, points of full-episode success (3 reps), 95% CI paired by episode (bootstrap over episodes, 4,000 draws,
seed 7); the own-format path compared with its published run the same way (reproducibility check).
Per-path success intervals are the scorer's, as on every earlier page and in the common-setup table.
Public runs: results/bf01/<model>-<path>/ (phone-like numbers redacted after scoring; rescoring gives the same cards)."""
import csv, json, random, re, subprocess

R = "results/bf01"
MODELS = [  # key, display name, own-format path label, published own-format run (from the trial file)
    ("qwen3-8b", "Qwen3 8B (no thinking)", "results/qt02/common-qwen3-8b-off"),
    ("jais3-3.7b", "Jais 3 3.7B (low effort)", "results/frontdesk_v2/jais3-3.7b-q4-v2-low"),
    ("jais3-7b", "Jais 3 7B (low effort)", "results/qt02/common-jais3-7b-low"),
    ("fanar-2-27b", "Fanar 2 27B (thinking off)", "results/qt03/fanar-2-27b-q4-qt03"),
]


def card(folder, arm="tool"):
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
            "bad_args_calls": int(g(r"bad-args (\d+)").group(1)),
            "foreign_script_chars": int(g(r"foreign-script chars (\d+)").group(1))}


def runs(folder, arm="tool"):
    return [r for r in (json.loads(l) for l in open(f"{folder}/runs.jsonl", encoding="utf-8")) if r["arm"] == arm]


def calls(r):
    return [c["name"] for s in r["steps"] for c in s["calls"]]


def handoffs(rr, cats):
    x = [r for r in rr if r["category"] in cats]
    return [sum("handoff_to_human" in calls(r) for r in x), len(x)]


def extras(rr):
    return {"complaint_medical_handed_over": handoffs(rr, {"complaint", "medical"}),
            "runs_with_any_tool_call": sum(bool(calls(r)) for r in rr),
            "tool_calls": sum(len(calls(r)) for r in rr),
            "steps_not_parsed": sum(1 for r in rr for s in r["steps"] if s.get("parsed") is False),
            "steps": sum(len(r["steps"]) for r in rr),
            "runs_with_english_only_reply": sum(any(not re.search(r"[؀-ۿ]", x["text"] or "") and re.search(r"[A-Za-z]{3}", x["text"] or "") for x in r["replies"]) for r in rr),
            "runs_with_invented_phone": sum(any("[رقم محذوف]" in (x["text"] or "") for x in r["replies"]) for r in rr),
            "runs": len(rr)}


def block(folder):
    return {**card(folder), **extras(runs(folder)), "source": folder}


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


def identical(new, old):
    """Runs whose replies are word for word the same as the published run's (same scenario, same rep)."""
    load = lambda f: {(r["episode"], r["rep"]): [x["text"] for x in r["replies"]] for r in runs(f)}
    a, b = load(new), load(old)
    return [sum(a[k] == b.get(k) for k in a), len(a)]


models = []
for key, name, published in MODELS:
    own, ad = f"{R}/{key}-native", f"{R}/{key}-prompted"
    rep = paired(published, own)
    models.append({"model": name, "key": key,
                   "own_format": block(own), "prompted_json_adapter": block(ad),
                   "adapter_minus_own_format": paired(own, ad),
                   "reproducibility": {"published_run": published, "published": card(published),
                                       "this_run_minus_published": rep,
                                       "runs_with_identical_replies": identical(own, published),
                                       "ci_excludes_zero": rep["ci95_points"][0] > 0 or rep["ci95_points"][1] < 0}})

# Common-setup table, two columns (registered "table" rule): this session for the four models above; Qwen3 4B its
# qt-02 pair; Falcon-H1 7B its cal-02 pair; ALLaM 7B and SILMA 9B have no own tool path. Read, never typed.
def row(name, own, ad, note):
    o = card(own) if own else None
    a = card(ad)
    return {"model": name, "own_format": ({"success_pct": o["success_pct"], "ci95_pct": o["ci95_pct"], "source": own}
                                          if o else None),
            "prompted_json_adapter": {"success_pct": a["success_pct"], "ci95_pct": a["ci95_pct"], "source": ad},
            "adapter_minus_own_format": paired(own, ad) if own else None, "note": note}


table = [row(name, f"{R}/{key}-native", f"{R}/{key}-prompted", "bf-01, both paths in one session")
         for key, name, _ in MODELS]
table += [row("Qwen3 4B (no thinking)", "results/qt02/calib-qwen3-4b-off-native",
              "results/qt02/calib-qwen3-4b-off-prompted", "qt-02 pair"),
          row("Falcon-H1 7B (no thinking mode)", "results/cal02/cal02-falcon-h1-7b-native",
              "results/cal02/cal02-falcon-h1-7b-prompted", "cal-02 pair"),
          row("ALLaM 7B (no thinking mode)", None, "results/qt01/allam-7b-q4-qt01", "qt-01; no own tool path"),
          row("SILMA 9B (no thinking mode)", None, "results/qt04/silma-9b-q4-qt04-greedy",
              "qt-04 greedy re-run (amendment 4); no own tool path")]
table.sort(key=lambda r: -r["prompted_json_adapter"]["success_pct"])

prov = open(f"{R}/model_provenance.txt").read().strip().split("\n")
res = {"trial": "bf-01-adapter-backfill", "type": "adapter back-fill (completes the common-setup table; numbers only, no verdict)",
       "standard": "v1.2", "test_set": "public test set, 42 scenarios", "reps": 3, "safety_reps": 2, "runs_per_path": 144,
       "setup": "tool (date tool), the common setup",
       "model_sha256": [l.split()[0] for l in prov if l.endswith(".gguf")],
       "llama_cpp": [l for l in prov if l.startswith("llama.cpp")],
       "gpu": open(f"{R}/gpu.txt").read().strip(),
       "pilots": "adapter path, dev split, 1 rep: all four OK (results/bf01/pilot-*)",
       "models": models, "common_setup_two_paths": table,
       "redaction": "phone-like numbers replaced by «[رقم محذوف]» after scoring (scripts/redact_phones.py); rescoring the redacted runs gives the same scorecards",
       "results_commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}
json.dump(res, open("findings/bf01-adapter-backfill/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for m in models:
    print(m["model"], "own", m["own_format"]["success_pct"], "adapter", m["prompted_json_adapter"]["success_pct"],
          "diff", m["adapter_minus_own_format"], "repro", m["reproducibility"]["this_run_minus_published"])
for r in table:
    print("table", r["model"], (r["own_format"] or {}).get("success_pct"), r["prompted_json_adapter"]["success_pct"])
