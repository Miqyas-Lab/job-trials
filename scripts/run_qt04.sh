#!/bin/bash
# miqyas · qt-04 — Quick Trial: SILMA-9B-Instruct-v1.0 at the clinic front desk (trials/qt-04-silma-9b-clinic.yaml).
# Self-converted Q4_K_M from the pinned revision, llama.cpp 7df8b87, prompted-JSON adapter, window 8192, cap 4096.
# On a RunPod pod (RTX 4090, PyTorch template, 60 GB disk), from the repo root. Run every step DETACHED:
#   setsid nohup bash scripts/run_qt04.sh setup > qt04_setup.log 2>&1 < /dev/null &   (~25 min, incl. conversion)
#   setsid nohup bash scripts/run_qt04.sh pilot > qt04_pilot.log 2>&1 < /dev/null &   (~5 min, DEV only)
#   setsid nohup bash scripts/run_qt04.sh test  > qt04_test.log  2>&1 < /dev/null &   (~60-90 min)
#   bash scripts/run_qt04.sh pack
# Check progress with: tail -5 qt04_<step>.log   (closing the terminal does not stop the run)
set -u
cd "$(dirname "$0")/.."
exec 9> /tmp/run_qt04.lock
if ! flock -n 9; then echo "Another run_qt04.sh is already running — not starting a second one."; exit 1; fi
LL="$HOME/llama.cpp-7df8b87"
SERVER="$LL/build/bin/llama-server"
QUANT="$LL/build/bin/llama-quantize"
LLAMA_COMMIT="7df8b87"
REPO="silma-ai/SILMA-9B-Instruct-v1.0"
REV="d8f4d2b11a71e10f4231d38f0a343ee49715f392"     # pinned in the pre-registration
GGUF="models/gpu/SILMA-9B-Instruct-v1.0-Q4_K_M.gguf"
OUT="results/qt04"
LABEL="silma-9b-q4-qt04"
CTX=8192
NPRED=4096
start_server () {
  pkill -f llama-server; sleep 2
  TPL=""; [ -f "$OUT/chat_template_llamacpp.jinja" ] && TPL="--chat-template-file $OUT/chat_template_llamacpp.jinja"   # amendment 2
  "$SERVER" -m "$GGUF" --jinja $TPL -ngl 99 -c $CTX -np 1 --port 8080 > /tmp/server_qt04.log 2>&1 9>&- &
  for i in $(seq 1 180); do curl -s localhost:8080/health | grep -q '"ok"' && return 0; sleep 2; done
  echo "server did not start — last log lines:"; tail -20 /tmp/server_qt04.log; return 1
}
case "${1:-}" in
setup)
  if [ ! -x "$SERVER" ] || [ ! -x "$QUANT" ]; then
    echo "== building llama.cpp $LLAMA_COMMIT with CUDA (about 10 minutes) =="
    pip install -q -U cmake huggingface_hub
    command -v git >/dev/null || (apt-get update -q && apt-get install -y -q git)
    [ -d "$LL" ] || git clone https://github.com/ggml-org/llama.cpp "$LL"
    (cd "$LL" && git checkout -q "$LLAMA_COMMIT" && cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CUDA_ARCHITECTURES=native && cmake --build build -j 16 --target llama-server llama-quantize) || exit 1
  fi
  command -v hf >/dev/null || pip install -q -U huggingface_hub
  mkdir -p models/gpu models/hf "$OUT"
  df -h . | tail -1
  if [ ! -f "$GGUF" ]; then
    pip install -q -r "$LL/requirements/requirements-convert_hf_to_gguf.txt" || pip install -q gguf sentencepiece safetensors transformers
    hf download "$REPO" --revision "$REV" --local-dir models/hf/silma-9b || { echo "DOWNLOAD FAILED: $REPO@$REV"; exit 1; }
    python3 "$LL/convert_hf_to_gguf.py" models/hf/silma-9b --outtype bf16 --outfile models/gpu/silma-9b-bf16.gguf || exit 1
    "$QUANT" models/gpu/silma-9b-bf16.gguf "$GGUF" Q4_K_M || exit 1
    rm -f models/gpu/silma-9b-bf16.gguf   # free ~18 GB
  fi
  cp models/hf/silma-9b/README.md "$OUT/model_card.md" 2>/dev/null
  cp models/hf/silma-9b/LICENSE* "$OUT/LICENSE.txt" 2>/dev/null || echo "no LICENSE file in $REPO; card states Gemma terms" > "$OUT/LICENSE.txt"
  echo "== generation_config.json (the pre-registration says there is none) =="
  cat models/hf/silma-9b/generation_config.json 2>/dev/null || echo "(no generation_config.json)"
  { echo "llama.cpp $(cd "$LL" && git rev-parse --short HEAD)"; echo "repo commit $(git rev-parse --short HEAD)";
    echo "source: self-converted from $REPO@$REV (bf16 -> Q4_K_M)"; sha256sum "$GGUF"; } > "$OUT/model_provenance.txt"
  cat "$OUT/model_provenance.txt"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | tee "$OUT/gpu.txt"
  python3 scripts/test_v2.py || exit 1
  start_server || exit 1; pkill -f llama-server
  echo "SETUP OK (model loads with an 8,192 window) — next:"
  echo "  setsid nohup bash scripts/run_qt04.sh pilot > qt04_pilot.log 2>&1 < /dev/null &"
  ;;
fixtemplate)   # amendment 2: system prompt kept under llama.cpp; checked identical to the original with Jinja2
  python3 scripts/fix_silma_template.py models/hf/silma-9b/tokenizer_config.json "$OUT/chat_template_llamacpp.jinja" || exit 1
  echo "next: setsid nohup bash scripts/run_qt04.sh pilot > qt04_pilot2.log 2>&1 < /dev/null &"
  ;;
pilot)
  start_server || exit 1
  P="pilot-$LABEL"; [ -f "$OUT/chat_template_llamacpp.jinja" ] && P="pilot2-$LABEL"   # pilot 1 kept as evidence
  python3 scripts/run_v2.py --label "$P" --mode prompted --sampling silma --split dev --arms tool --efforts off \
      --reps 1 --safety-reps 0 --n-predict $NPRED --out-root "$OUT"
  python3 scripts/score_v2.py "$OUT/$P" | tee "$OUT/$P/scorecard.txt"
  python3 - "$OUT/$P/runs.jsonl" <<'PY'
import json,sys
rows=[json.loads(l) for l in open(sys.argv[1])]
err=sum('error' in r for r in rows); ctx=sum(r.get('flags',{}).get('context',False) for r in rows)
calls=sum(len(s['calls']) for r in rows if 'steps' in r for s in r['steps'])
bad=sum(1 for r in rows if 'steps' in r for s in r['steps'] if s.get('parsed') is False)
p0=[r['steps'][0]['prompt_n'] for r in rows if r.get('steps')]
print(f"PILOT CHECK: runs {len(rows)} · errors {err} · context overflows {ctx} · tool calls {calls} · non-JSON replies {bad} · first prompt tokens {min(p0) if p0 else '-'}")
PY
  pkill -f llama-server
  echo "PILOT DONE — share the PILOT CHECK line for review before running 'test'."
  ;;
test)
  [ -f "$OUT/chat_template_llamacpp.jinja" ] || { echo "STOP: run 'fixtemplate' and a second pilot first (amendment 2)"; exit 1; }
  start_server || exit 1
  python3 scripts/run_v2.py --label "$LABEL" --mode prompted --sampling silma --split test --arms base table tool --efforts off \
      --reps 3 --safety-reps 2 --n-predict $NPRED --out-root "$OUT"
  python3 scripts/score_v2.py "$OUT/$LABEL" | tee "$OUT/$LABEL/scorecard.txt"
  pkill -f llama-server; echo "TEST DONE — next: bash scripts/run_qt04.sh pack"
  ;;
pack)
  tar czf qt04_results.tar.gz "$OUT" && ls -la qt04_results.tar.gz
  echo "Download qt04_results.tar.gz from JupyterLab (right-click > Download), then STOP the pod."
  ;;
*) echo "usage: bash scripts/run_qt04.sh {setup|fixtemplate|pilot|test|pack}"; exit 2 ;;
esac
