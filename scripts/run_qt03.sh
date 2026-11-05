#!/bin/bash
# miqyas · qt-03 — Fanar-2-27B-Instruct (QCRI) Quick Trial on the clinic front desk (trials/qt-03-fanar-2-27b-clinic.yaml).
# Same job, test set, window (32,768) and generation cap (8,192) as Job Trial #1. Standard v1.2 (fair shot):
# base/table/tool with thinking off (tool = common-setup headline) + tool with thinking on (the model's own best).
# Fanar thinks by default; the runner sends no_thinking + enable_thinking, and the pilot checks the switch works.
# Tool path (pre-registered): probe -> native (chat) if tools reach the prompt; if the DEV pilot then shows 0 native
# calls, re-run the pilot with 'template' (reads the template-documented format); else 'prompted' (JSON adapter).
#
# On a RunPod pod (RTX 4090, PyTorch template, CONTAINER/VOLUME DISK >= 150 GB), from the repo root. Run DETACHED:
#   setsid nohup bash scripts/run_qt03.sh setup > qt03_setup.log 2>&1 < /dev/null &   (~30-40 min: build + 54 GB download + convert)
#   setsid nohup bash scripts/run_qt03.sh pilot > qt03_pilot.log 2>&1 < /dev/null &   (~15 min)
#   setsid nohup bash scripts/run_qt03.sh test  > qt03_test.log  2>&1 < /dev/null &   (~2-3 h, thinking off, 3 setups)
#   setsid nohup bash scripts/run_qt03.sh think > qt03_think.log 2>&1 < /dev/null &   (~2-4 h, tool setup, thinking on)
#   bash scripts/run_qt03.sh pack
# Check progress with: tail -5 qt03_<step>.log   (closing the terminal does not stop the run)
set -u
cd "$(dirname "$0")/.."
exec 9> /tmp/run_qt03.lock
if ! flock -n 9; then echo "Another run_qt03.sh is already running — not starting a second one."; exit 1; fi
LL="$HOME/llama.cpp"
SERVER="$LL/build/bin/llama-server"
QUANT="$LL/build/bin/llama-quantize"
REPO="QCRI/Fanar-2-27B-Instruct"
REV="074005040e9c3511b1c43b4298bef09908285534"     # pinned in the pre-registration
GGUF="models/gpu/Fanar-2-27B-Instruct-Q4_K_M.gguf"
OUT="results/qt03"
LABEL="fanar-2-27b-q4-qt03"
CTX=32768
NPRED=8192

start_server () {
  pkill -f llama-server; sleep 2
  "$SERVER" -m "$GGUF" --jinja -ngl 99 -c $CTX -np 1 --port 8080 > /tmp/server_qt03.log 2>&1 9>&- &
  for i in $(seq 1 240); do curl -s localhost:8080/health | grep -q '"ok"' && return 0; sleep 2; done
  echo "server did not start — last log lines:"; tail -20 /tmp/server_qt03.log
  grep -qi "out of memory\|failed to allocate\|cudaMalloc" /tmp/server_qt03.log && \
    echo "FALLBACK RULE: does not fit 24 GB with a 32,768 window -> stop this pod, start a 48 GB card (RTX A6000 or L40S), rerun setup."
  return 1
}

probe_adapter () {   # prompt size with vs without tools, max_tokens 1: no model answer is read
  python3 - "$OUT/adapter.txt" <<'PY'
import json, sys, urllib.request
sys.path.insert(0, "scripts")
from clinic import system_prompt, tools_for
def n(tools):
    body = {"messages": [{"role": "system", "content": system_prompt("tool")}, {"role": "user", "content": "مرحبا"}],
            "max_tokens": 1, "temperature": 0, "cache_prompt": False, "chat_template_kwargs": {"no_thinking": True}}
    if tools: body["tools"] = tools_for("tool")
    r = json.load(urllib.request.urlopen(urllib.request.Request("http://localhost:8080/v1/chat/completions",
        json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=300))
    return r["timings"]["prompt_n"]
a, b = n(False), n(True)
mode = "chat" if b - a >= 200 else "prompted"
open(sys.argv[1], "w").write(f"{mode}\nprompt tokens without tools {a}, with tools {b}\n")
print(f"ADAPTER: {mode} (prompt tokens without tools {a}, with tools {b})")
PY
}

case "${1:-}" in
setup)
  if [ ! -x "$SERVER" ] || [ ! -x "$QUANT" ]; then
    echo "== building llama.cpp with CUDA (about 10 minutes) =="
    pip install -q -U cmake huggingface_hub
    command -v git >/dev/null || (apt-get update -q && apt-get install -y -q git)
    [ -d "$LL" ] || git clone --depth 1 https://github.com/ggml-org/llama.cpp "$LL"
    (cd "$LL" && cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES=native \
      && cmake --build build -j 16 --target llama-server llama-quantize) || exit 1
  fi
  command -v hf >/dev/null || pip install -q -U huggingface_hub
  (cd "$LL" && git rev-parse --short HEAD) > /tmp/llama_commit.txt
  mkdir -p models/gpu models/hf "$OUT"
  df -h . | tail -1
  if [ ! -f "$GGUF" ]; then
    pip install -q -r "$LL/requirements/requirements-convert_hf_to_gguf.txt" || pip install -q gguf sentencepiece safetensors transformers
    hf download "$REPO" --revision "$REV" --local-dir models/hf/fanar-2-27b || { echo "DOWNLOAD FAILED: $REPO@$REV"; exit 1; }
    python3 "$LL/convert_hf_to_gguf.py" models/hf/fanar-2-27b --outtype bf16 --outfile models/gpu/fanar-2-27b-bf16.gguf || exit 1
    "$QUANT" models/gpu/fanar-2-27b-bf16.gguf "$GGUF" Q4_K_M || exit 1
    mv models/gpu/fanar-2-27b-bf16.gguf /tmp/ 2>/dev/null; rm -f /tmp/fanar-2-27b-bf16.gguf   # free ~54 GB
  fi
  cp models/hf/fanar-2-27b/README.md "$OUT/model_card.md" 2>/dev/null
  cp models/hf/fanar-2-27b/LICENSE* "$OUT/LICENSE.txt" 2>/dev/null || echo "no LICENSE file in $REPO; card states Apache-2.0" > "$OUT/LICENSE.txt"
  echo "== generation_config.json (sampling check against the pre-registered temperature 0.7) =="
  cat models/hf/fanar-2-27b/generation_config.json 2>/dev/null || echo "(no generation_config.json)"
  grep -o 'no_thinking' models/hf/fanar-2-27b/chat_template.jinja 2>/dev/null | head -1 | sed 's/^/template switch found: /'
  { echo "llama.cpp $(cat /tmp/llama_commit.txt)"; echo "repo commit $(git rev-parse --short HEAD)"; echo "source: self-converted from $REPO@$REV (bf16 -> Q4_K_M)"; sha256sum "$GGUF"; } > "$OUT/model_provenance.txt"
  cat "$OUT/model_provenance.txt"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | tee "$OUT/gpu.txt"
  python3 scripts/test_v2.py || exit 1
  start_server || exit 1; pkill -f llama-server
  echo "SETUP OK (model loads with a 32,768 window) — send the generation_config lines to Claude, then:"
  echo "  setsid nohup bash scripts/run_qt03.sh pilot > qt03_pilot.log 2>&1 < /dev/null &"
  ;;
pilot)   # optional 2nd argument: template | prompted  (tool-path rule step 2/3, only after a pilot shows 0 native calls)
  start_server || exit 1
  [ -f "$OUT/adapter.txt" ] || probe_adapter || exit 1
  if [ -n "${2:-}" ]; then printf '%s\n' "$2" "$(tail -n +2 "$OUT/adapter.txt")" "path changed after pilot: $(head -1 "$OUT/adapter.txt") -> $2 (tool-path rule)" > "$OUT/adapter.txt"; fi
  MODE=$(head -1 "$OUT/adapter.txt")
  P="pilot-$MODE-$LABEL"
  python3 scripts/run_v2.py --label "$P" --mode "$MODE" --sampling fanar-2 --split dev --arms tool --efforts off on \
      --reps 1 --safety-reps 0 --n-predict $NPRED --out-root "$OUT"
  python3 scripts/score_v2.py "$OUT/$P" | tee "$OUT/$P/scorecard.txt"
  python3 - "$OUT/$P/runs.jsonl" "$MODE" <<'PY'
import json,sys
rows=[json.loads(l) for l in open(sys.argv[1])]
for eff in ("off","on"):
    R=[r for r in rows if r.get("effort")==eff]
    st=[s for r in R if 'steps' in r for s in r['steps']]
    calls=sum(len(s['calls']) for s in st)
    unparsed=sum(1 for s in st for c in s['calls'] if '_unparsed' in c.get('args',{}))
    withreason=sum(1 for s in st if (s.get('reasoning') or '').strip())
    leak=sum(1 for r in R for t in r.get('replies',[]) if '<think' in t.get('text','') or '</think' in t.get('text',''))
    ctx=sum(r.get('flags',{}).get('context',False) for r in R); err=sum('error' in r for r in R)
    p0=R[0]['steps'][0]['prompt_n'] if R and R[0].get('steps') else '-'
    print(f"PILOT CHECK [{eff}]: mode {sys.argv[2]} · runs {len(R)} · errors {err} · context overflows {ctx} · tool calls {calls} · unparsed {unparsed} · steps with reasoning {withreason}/{len(st)} · <think> in replies {leak} · first prompt tokens {p0}")
PY
  pkill -f llama-server
  echo "PILOT DONE — send both PILOT CHECK lines and the scorecard to Claude before running 'test'."
  echo "Expected: [off] reasoning 0 and <think> 0; [on] reasoning > 0 and <think> 0; tool calls > 0."
  ;;
test)
  [ -f "$OUT/adapter.txt" ] || { echo "run the pilot first (it fixes the tool path)"; exit 1; }
  MODE=$(head -1 "$OUT/adapter.txt")
  start_server || exit 1
  python3 scripts/run_v2.py --label "$LABEL" --mode "$MODE" --sampling fanar-2 --split test --arms base table tool --efforts off \
      --reps 3 --safety-reps 2 --n-predict $NPRED --out-root "$OUT"
  python3 scripts/score_v2.py "$OUT/$LABEL" | tee "$OUT/$LABEL/scorecard.txt"
  pkill -f llama-server; echo "TEST DONE — next: setsid nohup bash scripts/run_qt03.sh think > qt03_think.log 2>&1 < /dev/null &"
  ;;
think)
  MODE=$(head -1 "$OUT/adapter.txt")
  start_server || exit 1
  python3 scripts/run_v2.py --label "$LABEL-think" --mode "$MODE" --sampling fanar-2 --split test --arms tool --efforts on \
      --reps 3 --safety-reps 2 --n-predict $NPRED --out-root "$OUT"   # own label so meta.json of the thinking-off run is kept
  python3 scripts/score_v2.py "$OUT/$LABEL-think" | tee "$OUT/$LABEL-think/scorecard.txt"
  pkill -f llama-server; echo "THINK DONE — next: bash scripts/run_qt03.sh pack"
  ;;
pack)
  tar czf qt03_results.tar.gz "$OUT" && ls -la qt03_results.tar.gz
  echo "Download qt03_results.tar.gz from JupyterLab (right-click > Download), attach it to Claude, then STOP the pod."
  ;;
*)
  echo "usage: bash scripts/run_qt03.sh setup | pilot [template|prompted] | test | think | pack"; exit 1 ;;
esac
