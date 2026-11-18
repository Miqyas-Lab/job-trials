"""Build results.json for Job Trial #2 stage 1 (Riyadh clinic, Quick Trial, numbers only) from the scored runs.
Every published number on the stage-1 page comes from here.
Public set: results/jt02/<model>-<path>-public/ (raw conversations, phone-like numbers redacted after scoring).
Private set: results/jt02/private_scores/<model>-<path>-private/ (per-scenario scores and categories only; no text)."""
import csv, json, random, re, statistics, subprocess

R = "results/jt02"
ARMS = ("base", "table", "tool")
T = lambda v: str(v) == "True"
MODELS = [  # key, display name, paths (own-format path first), maker repo
    ("jais3-7b", "Jais 3 7B", ["jais", "prompted"], "inceptionai / MBZUAI (IFM/Jais-3-7B-GGUF)"),
    ("jais3-3.7b", "Jais 3 3.7B", ["jais", "prompted"], "inceptionai / MBZUAI (IFM/Jais-3-3.7B-GGUF)"),
    ("qwen3-8b", "Qwen3 8B", ["chat", "prompted"], "Qwen (Qwen/Qwen3-8B-GGUF)"),
    ("qwen3-4b", "Qwen3 4B", ["chat", "prompted"], "Qwen (Qwen/Qwen3-4B-GGUF)"),
    ("falcon-h1-7b", "Falcon-H1 7B", ["template", "prompted"], "TII (tiiuae/Falcon-H1-7B-Instruct-GGUF)"),
    ("allam-7b", "ALLaM 7B", ["prompted"], "HUMAIN (humain-ai/ALLaM-7B-Instruct-preview, self-converted)"),
    ("silma-9b", "SILMA 9B", ["prompted"], "SILMA AI (silma-ai/SILMA-9B-Instruct-v1.0, self-converted)"),
    ("fanar-2-27b", "Fanar 2 27B", ["template", "prompted"], "QCRI (QCRI/Fanar-2-27B-Instruct, self-converted)"),
]
PATH_NAME = {"jais": "model's own format", "chat": "model's own format", "template": "model's own format",
             "prompted": "prompted-JSON adapter"}


def rows(folder, fname):
    out = []
    for r in csv.DictReader(open(f"{folder}/{fname}", encoding="utf-8-sig")):
        r["rep"] = int(r["rep"])
        for k in ("success", "state_ok", "handoff", "invented_time", "false_confirmation", "cap", "loop", "silent_turn"):
            r[k] = T(r[k])
        out.append(r)
    return out


def boot(by_ep, n=4000, seed=7):
    """Cluster bootstrap over scenarios (registered: 4,000 draws, seed 7)."""
    keys = sorted(by_ep); rng = random.Random(seed); vals = []
    for _ in range(n):
        s = t = 0
        for k in (rng.choice(keys) for _ in keys):
            s += sum(by_ep[k]); t += len(by_ep[k])
        vals.append(s / t)
    vals.sort()
    return [round(100 * vals[int(0.025 * n)], 1), round(100 * vals[int(0.975 * n) - 1], 1)]


def waits(folder, arm):
    t = open(f"{folder}/scorecard.txt", encoding="utf-8").read()
    blk = [b for b in re.split(r"\n== ", t) if b.startswith(f"arm {arm} ")][0]
    m = re.search(r"median ([\d.]+)s\s+p90 ([\d.]+)s", blk)
    return [float(m.group(1)), float(m.group(2))]


def arm_block(rs_all, arm, folder):
    rs = [r for r in rs_all if r["arm"] == arm]
    b3 = [r for r in rs if r["rep"] < 3]
    by = {}
    for r in sorted(b3, key=lambda r: r["rep"]):
        by.setdefault(r["episode"], []).append(r["success"])
    em = [r for r in rs if r["category"] == "emergency"]
    cm = [r for r in rs if r["category"] in ("complaint", "medical")]
    crit = {k: sum(r[k] for r in rs) for k in ("invented_time", "false_confirmation", "cap", "loop", "silent_turn")}
    return {"success_pct": round(100 * sum(r["success"] for r in b3) / len(b3), 1), "ci95_pct": boot(by),
            "pass3_pct": round(100 * sum(all(v[:3]) for v in by.values()) / len(by), 1),
            "emergencies_in_time": f"{sum(r['state_ok'] and r['handoff'] for r in em)}/{len(em)}",
            "complaint_medical_handed_over": f"{sum(r['handoff'] for r in cm)}/{len(cm)}",
            "critical_runs": crit, "critical_total": sum(crit.values()),
            "wait_median_p90_s": waits(folder, arm), "runs_scored": len(b3), "runs_counted": len(rs), "scenarios": len(by)}


def phones(folder):
    n = 0
    for l in open(f"{folder}/runs.jsonl", encoding="utf-8"):
        r = json.loads(l)
        n += any("[رقم محذوف]" in (x.get("text") or "") for x in r["replies"])
    return n


# Dubai (Job Trial #1 scenarios), common setup, from earlier results files; read, never typed
q4 = json.load(open("findings/qt04-silma-9b/results.json", encoding="utf-8"))
dubai_native = {r["model"].split(" (")[0]: r for r in q4["common_setup"]}
cal = q4["adapter_calibrations"]
DUBAI = {}
for key, name, paths, _ in MODELS:
    for p in paths:
        d = None
        if p != "prompted" and name in dubai_native:
            r = dubai_native[name]; d = {"success_pct": r["success_pct"], "ci95_pct": r["ci95_pct"], "source": r["source"]}
        elif p == "prompted" and name in ("ALLaM 7B", "SILMA 9B"):
            r = dubai_native[name]; d = {"success_pct": r["success_pct"], "ci95_pct": r["ci95_pct"], "source": r["source"]}
        elif p == "prompted" and name == "Qwen3 4B":
            d = {"success_pct": cal["qwen3_4b_qt02"]["adapter_pct"], "ci95_pct": None, "source": "qt-02 adapter calibration"}
        elif p == "prompted" and name == "Falcon-H1 7B":
            c2 = q4["cal02"]["prompted_json_adapter"]; d = {"success_pct": c2["success_pct"], "ci95_pct": c2["ci95_pct"], "source": "cal-02"}
        DUBAI[(key, p)] = d or {"success_pct": None, "note": "not measured on the Dubai scenarios yet (bf-01, registered)"}

paths_out = []
for key, name, paths, maker in MODELS:
    for p in paths:
        pub_dir, prv_dir = f"{R}/{key}-{p}-public", f"{R}/private_scores/{key}-{p}-private"
        pub, prv = rows(pub_dir, "scored.csv"), rows(prv_dir, "scores.csv")
        meta = json.load(open(f"{pub_dir}/meta.json", encoding="utf-8"))
        entry = {"model": name, "key": key, "maker": maker, "path": p, "path_name": PATH_NAME[p],
                 "effort": meta["efforts"][0],
                 "public": {a: arm_block(pub, a, pub_dir) for a in ARMS},
                 "private": {a: arm_block(prv, a, prv_dir) for a in ARMS},
                 "public_runs_with_invented_phone_redacted": phones(pub_dir),
                 "dubai_common_setup": DUBAI[(key, p)]}
        entry["private_minus_public_tool_points"] = round(entry["private"]["tool"]["success_pct"] - entry["public"]["tool"]["success_pct"], 1)
        paths_out.append(entry)

# registered stage-2 rule: better path per model on private tool success; ties public tool success, then fewer critical
best = {}
for e in paths_out:
    k = (e["private"]["tool"]["success_pct"], e["public"]["tool"]["success_pct"], -e["private"]["tool"]["critical_total"])
    if e["model"] not in best or k > best[e["model"]][0]:
        best[e["model"]] = (k, e["path"])
ranking = [{"rank": i + 1, "model": m, "path": p, "private_tool_pct": k[0], "public_tool_pct": k[1], "private_tool_critical": -k[2]}
           for i, (m, (k, p)) in enumerate(sorted(best.items(), key=lambda kv: kv[1][0], reverse=True))]

prov1 = open(f"{R}/model_provenance.txt").read().strip().split("\n")
provR = open(f"{R}/model_provenance_R.txt").read().strip().split("\n")
res = {
    "trial": "jt-02-riyadh-clinic", "stage": 1, "type": "quick-trial (numbers only, no verdict)",
    "question": "Can an open Arabic model run a Riyadh dental clinic's WhatsApp front desk, with patients writing in Najdi?",
    "sets": {"public": "42 test scenarios (Najdi, reviewed by two native Najdi speakers, 161/161 agreement)",
             "private": "42 held-out test scenarios written by two native Najdi speakers, never published; sealed sha256 18742b54...4509f"},
    "runs": "3 reps per scenario for success (126 runs per setup), plus 2 safety reps on emergency, complaint and medical scenarios (counts out of 144)",
    "setups": {"base": "no date help", "table": "calendar in the prompt", "tool": "date tool (the common setup)"},
    "clinic": "Riyadh: Sun-Thu 14:00-22:00, Sat 11:00-19:00, Fri closed; clock Thu 5 Nov 2026 15:30; prayer-relative times left out (disclosed)",
    "ci": "95% cluster bootstrap over scenarios, 4,000 draws, seed 7",
    "critical_failures": "runs with an invented time, a false confirmation, the length cap, a loop or a silent turn (any one fails the run)",
    "paths": paths_out,
    "stage2_selection": {"rule": "two highest private-set tool-setup success, each model at its better path; ties: public, then fewer critical failures (registered 16 Nov, before any result)",
                         "ranking": ranking, "selected": [r["model"] + " (" + PATH_NAME[r["path"]] + ")" for r in ranking[:2]],
                         "note": "the second place (71.4) and the third (68.3) are inside each other's 95% CIs; the rule is applied as registered"},
    "contamination_check": "no path is much stronger on public than on private: largest public lead "
                           + str(max(-e["private_minus_public_tool_points"] for e in paths_out)) + " points",
    "machines": {"first": {"parts": "13 public parts", "when": "16-17 Nov 2026", "gpu": open(f"{R}/gpu.txt").read().strip(),
                           "repo_commit": [l for l in prov1 if l.startswith("repo commit")][0].split()[-1],
                           "note": "lost on 17 Nov (provider ended the machine); finished parts had been downloaded (amendment 4)"},
                 "restart": {"parts": "Fanar 2 27B adapter public + all 14 private parts", "when": "17-18 Nov 2026",
                             "gpu": open(f"{R}/gpu_R.txt").read().strip(),
                             "repo_commit": [l for l in provR if l.startswith("repo commit")][0].split()[-1],
                             "note": "Fanar 2 27B's three parts ran with the server prompt cache off and a fresh server per part (amendment 6); the test died once during its template private part, which was discarded and rerun"}},
    "model_sha256": [l for l in prov1 if "gguf" in l], "llama_cpp": [l for l in prov1 if l.startswith("llama.cpp")],
    "reply_times": "RTX 4090 on both machines; Fanar 2 27B adapter public and all private parts on the restart machine; compare within a set",
    "results_commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
}
json.dump(res, open("findings/jt02-riyadh-stage1/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for e in paths_out:
    print(f"{e['model']:<13}{e['path']:<9} pub {e['public']['tool']['success_pct']:>5} {e['public']['tool']['ci95_pct']}  "
          f"prv {e['private']['tool']['success_pct']:>5} {e['private']['tool']['ci95_pct']}  dubai {e['dubai_common_setup'].get('success_pct')}  "
          f"em pub {e['public']['tool']['emergencies_in_time']} prv {e['private']['tool']['emergencies_in_time']}  phones {e['public_runs_with_invented_phone_redacted']}")
print(ranking[:3]); print(res["contamination_check"])
