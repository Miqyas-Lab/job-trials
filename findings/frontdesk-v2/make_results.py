"""Build results.json for Job Trial #1 (front-desk v2) from the raw runs; every published number comes from here.

Run from the repository root:  python3 findings/frontdesk-v2/make_results.py
Scores every run with scripts/score_v2.py, applies the recorded human review of every critical flag
(results/frontdesk_v2/flags_review_v2.py: a cleared flag is not a failure, a confirmed one is), and recomputes the
page's numbers: success per model and date setup (first 3 reps), 95% CI clustered by episode (2,000 draws, seed 42),
pass^3, emergencies, flags before and after review, the paired comparisons, and the two one-arm setups.
Added 2026-11-23, after publication: the page's numbers were the scorer's output with the review applied by hand.
This recipe reproduces all of them; the job declaration it was checked against reproduces 49 of 49 claims.
"""
import json
import os
import random
import subprocess
import sys

os.environ.setdefault("MIQYAS_CLINIC", "dubai")
sys.path.insert(0, "scripts")
import score_v2 as S  # noqa: E402

D = "results" + "/frontdesk_v2"      # for the review and hash files; the run folders are named in FOLDERS
CONFIGS = {  # run folder -> (model as the page names it, effort, arms, primary)
    "jais3-3.7b-q4-v2": ("Jais 3 3.7B", "high", ["base", "table", "tool"], True),
    "jais3-7b-q4-v2": ("Jais 3 7B", "high", ["base", "table", "tool"], True),
    "qwen3-8b-q4-v2": ("Qwen3-8B", "thinking on", ["base", "table", "tool"], True),
    "qwen3-4b-q4-v2": ("Qwen3-4B", "thinking on", ["base", "table", "tool"], True),
    "jais3-3.7b-q4-v2-low": ("Jais 3 3.7B", "low", ["tool"], False),
    "qwen3-4b-q4-v2-off": ("Qwen3-4B", "thinking off", ["tool"], False),
}
ARMS = {"base": "no date help", "table": "14-day calendar in the prompt", "tool": "find_date tool"}
CRITICAL = ("invented_time", "false_confirmation", "cap", "loop", "silent_turn")
REVIEWED = ("invented_time", "false_confirmation")
ns = {}
exec(open(f"{D}/flags_review_v2.py", encoding="utf-8").read(), ns)
REVIEW = ns["REVIEW"]


FOLDERS = {  # named in full, so a checker reads exactly these six setups (not the pilots, laptop or reproductions)
    "jais3-3.7b-q4-v2": "results/frontdesk_v2/jais3-3.7b-q4-v2",
    "jais3-7b-q4-v2": "results/frontdesk_v2/jais3-7b-q4-v2",
    "qwen3-8b-q4-v2": "results/frontdesk_v2/qwen3-8b-q4-v2",
    "qwen3-4b-q4-v2": "results/frontdesk_v2/qwen3-4b-q4-v2",
    "jais3-3.7b-q4-v2-low": "results/frontdesk_v2/jais3-3.7b-q4-v2-low",
    "qwen3-4b-q4-v2-off": "results/frontdesk_v2/qwen3-4b-q4-v2-off",
}


def rows_of(cfg):
    _, _, rows = S.load(FOLDERS[cfg])
    for r in rows:
        if "error" in r:
            continue
        r["auto"] = {f: bool(r[f]) for f in REVIEWED}
        for f in REVIEWED:
            d = REVIEW.get((cfg, r["episode"], r["arm"], r["rep"], f))
            if r[f] and d and d[0] == "cleared":
                r[f] = False
        r["success"] = r["state_ok"] and not any(r[c] for c in CRITICAL)
    return rows


def main_rows(rows, arm):
    return [r for r in rows if r.get("arm") == arm and "error" not in r and r["rep"] < 3]


def by_ep(rows):
    d = {}
    for r in sorted(rows, key=lambda r: r["rep"]):
        d.setdefault(r["episode"], []).append(r["success"])
    return d


def paired(a, b, n=2000, seed=42):
    A = {e: sum(v) / len(v) for e, v in by_ep(a).items()}
    B = {e: sum(v) / len(v) for e, v in by_ep(b).items()}
    diffs = [B[k] - A[k] for k in sorted(set(A) & set(B))]
    rng, vals = random.Random(seed), []
    for _ in range(n):
        s = [rng.choice(diffs) for _ in diffs]
        vals.append(sum(s) / len(s))
    vals.sort()
    return {"points": round(100 * sum(diffs) / len(diffs), 1) + 0.0,
            "ci95_points": [round(100 * vals[int(0.025 * n)], 1), round(100 * vals[int(0.975 * n) - 1], 1)]}


ROWS = {c: rows_of(c) for c in CONFIGS}
sha = dict(l.split()[::-1] for l in open(f"{D}/models_sha256.txt") if l.strip())
models = []
for cfg, (name, effort, arms, primary) in CONFIGS.items():
    rows = ROWS[cfg]
    out = {}
    for a in arms:
        m = main_rows(rows, a)
        every = [r for r in rows if r.get("arm") == a and "error" not in r]
        lo, hi = S.boot_ci(by_ep(m))
        em = [r for r in every if r["category"] == "emergency"]
        out[a] = {"success_pct": round(100 * sum(r["success"] for r in m) / len(m), 1),
                  "ci95_pct": [round(100 * lo, 1), round(100 * hi, 1)],
                  "pass3_pct": round(100 * S.pass_k(by_ep(m), 3), 1),
                  "successes_main": sum(r["success"] for r in m), "runs_main": len(m), "runs": len(every),
                  "emergencies_in_time": f"{sum(r['handoff'] for r in em)}/{len(em)}",
                  "emergencies_with_right_reason": f"{sum(r['handoff'] and r['state_ok'] for r in em)}/{len(em)}",
                  "flags_before_review": {f: sum(r["auto"][f] for r in every) for f in REVIEWED},
                  "flags_after_review": {f: sum(bool(r[f]) for r in every) for f in REVIEWED},
                  "reschedule": f"{sum(r['success'] for r in m if r['category'] == 'reschedule')}/"
                                f"{sum(1 for r in m if r['category'] == 'reschedule')}"}
    models.append({"key": cfg, "model": name, "effort": effort, "primary": primary, "arms": out,
                   "errors": sum("error" in r for r in rows), "source": FOLDERS[cfg]})

J37, J7, Q8 = ROWS["jais3-3.7b-q4-v2"], ROWS["jais3-7b-q4-v2"], ROWS["qwen3-8b-q4-v2"]
res = {
    "trial": "jt-01-frontdesk-v2", "type": "job trial (pre-registered; verdicts per model, sub-task and hardware)",
    "standard": "v1.2", "job": "clinic-frontdesk",
    "protocol": "docs/frontdesk_protocol_v2.md (9a83bfe, pre-registered 2026-10-21) and amendments 1-3",
    "test_set": "public test set, 42 scenarios", "reps": 3, "safety_reps": 2, "arms": ARMS,
    "conversations": sum(len(r) for r in ROWS.values()),
    "errors": sum("error" in x for r in ROWS.values() for x in r),
    "review": {"file": f"{D}/flags_review_v2.py", "decisions": len(REVIEW),
               "confirmed": sum(v[0] == "confirmed" for v in REVIEW.values()),
               "cleared": sum(v[0] == "cleared" for v in REVIEW.values())},
    "model_sha256": sha, "gpu": "NVIDIA GeForce RTX 4090", "models": models,
    "comparisons": {
        "h1_jais3_3.7b_tool_minus_base": paired(main_rows(J37, "base"), main_rows(J37, "tool")),
        "h1_jais3_7b_tool_minus_base": paired(main_rows(J7, "base"), main_rows(J7, "tool")),
        "jais3_7b_table_minus_base": paired(main_rows(J7, "base"), main_rows(J7, "table")),
        "jais3_3.7b_minus_qwen3_8b": {a: paired(main_rows(Q8, a), main_rows(J37, a)) for a in ARMS},
    },
    "known_gaps": [
        "The two one-setup runs (Jais 3 3.7B low effort, Qwen3-4B thinking off) were not in the flag review of "
        "2026-10-25, which covered the four main models: their 23 critical flags (20 and 3) have no human decision, so "
        "their success figures are the scorer's automatic numbers. A review can only clear flags, so they can only rise.",
        "The llama.cpp build was not recorded (the setup log says only version 0.7.0-dev, cloned 2026-10-24); the model "
        "files are pinned by sha256 in results/frontdesk_v2/models_sha256.txt.",
    ],
    "results_commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
}
json.dump(res, open("findings/frontdesk-v2/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{res['conversations']} conversations, {res['errors']} errors; results.json written")
