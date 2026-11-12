#!/bin/bash
# miqyas · cal-02 — adapter calibration on Falcon-H1-7B-Instruct (trials/cal-02-adapter-falcon-h1-7b.yaml).
# Same GGUF (sha256 checked), llama.cpp 7df8b87, falcon-h1 sampling, tool setup, thinking off; native (call text kept
# in the history) and prompted-JSON adapter, both in one session.
#   setsid nohup bash scripts/run_cal02.sh setup > cal02_setup.log 2>&1 < /dev/null &   (~15 min)
#   setsid nohup bash scripts/run_cal02.sh test  > cal02_test.log  2>&1 < /dev/null &   (~50 min)
#   bash scripts/run_cal02.sh pack
set -u
cd "$(dirname "$0")/.."
exec 9> /tmp/run_cal02.lock
if ! flock -n 9; then echo "Another run_cal02.sh is already running — not starting a second one."; exit 1; fi
LL="$HOME/llama.cpp-7df8b87"
SERVER="$LL/build/bin/llama-server"
LLAMA_COMMIT="7df8b87"
GREPO="tiiuae/Falcon-H1-7B-Instruct-GGUF"
GGUF="models/gpu/Falcon-H1-7B-Instruct-Q4_K_M.gguf"
GGUF_SHA="145def0b4cd36500bf538ed7ac895b5c1851e02e802b2d1c12ffa6afdbaff25d"
OUT="results/cal02"
CTX=32768
NPRED=8192
start_server () {
  pkill -f llama-server; sleep 2
  "$SERVER" -m "$GGUF" --jinja -ngl 99 -c $CTX -np 1 --port 8080 > /tmp/server_cal02.log 2>&1 9>&- &
  for i in $(seq 1 180); do curl -s localhost:8080/health | grep -q '"ok"' && return 0; sleep 2; done
  echo "server did not start — last log lines:"; tail -20 /tmp/server_cal02.log; return 1
}
case "${1:-}" in
setup)
  if [ ! -x "$SERVER" ]; then
    echo "== building llama.cpp $LLAMA_COMMIT with CUDA (about 10 minutes) =="
    pip install -q -U cmake huggingface_hub
    command -v git >/dev/null || (apt-get update -q && apt-get install -y -q git)
    [ -d "$LL" ] || git clone https://github.com/ggml-org/llama.cpp "$LL"
    (cd "$LL" && git checkout -q "$LLAMA_COMMIT" && cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CUDA_ARCHITECTURES=native && cmake --build build -j 16 --target llama-server) || exit 1
  fi
  command -v hf >/dev/null || pip install -q -U huggingface_hub
  mkdir -p models/gpu models/hf "$OUT"
  if [ ! -f "$GGUF" ]; then
    hf download "$GREPO" --include "*Q4_K_M*.gguf" --local-dir models/hf/falcon-gguf >/dev/null 2>&1
    cp "$(ls models/hf/falcon-gguf/*Q4_K_M*.gguf | head -1)" "$GGUF" || { echo "DOWNLOAD FAILED: $GREPO"; exit 1; }
  fi
  echo "$GGUF_SHA  $GGUF" | sha256sum -c - || { echo "STOP: the GGUF differs from the registered one"; exit 1; }
  { echo "llama.cpp $(cd "$LL" && git rev-parse --short HEAD)"; echo "repo commit $(git rev-parse --short HEAD)";
    echo "source: official GGUF ($GREPO)"; sha256sum "$GGUF"; } > "$OUT/model_provenance.txt"
  cat "$OUT/model_provenance.txt"
  grep -q "history_content" scripts/run_v2.py || { echo "STOP: runner without the history fix"; exit 1; }
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
  python3 scripts/test_v2.py || exit 1
  echo "SETUP OK — next: setsid nohup bash scripts/run_cal02.sh test > cal02_test.log 2>&1 < /dev/null &"
  ;;
test)
  start_server || exit 1
  for cond in native:template prompted:prompted; do
    label="cal02-falcon-h1-7b-${cond%%:*}"
    python3 scripts/run_v2.py --label "$label" --mode "${cond##*:}" --sampling falcon-h1 --split test --arms tool --efforts off \
        --reps 3 --safety-reps 2 --n-predict $NPRED --out-root "$OUT" || exit 1
    python3 scripts/score_v2.py "$OUT/$label" | tee "$OUT/$label/scorecard.txt"
  done
  pkill -f llama-server; echo "TEST DONE — next: bash scripts/run_cal02.sh pack"
  ;;
pack)
  tar czf cal02_results.tar.gz "$OUT" && ls -la cal02_results.tar.gz
  echo "Download cal02_results.tar.gz from JupyterLab (right-click > Download), then STOP the pod."
  ;;
*) echo "usage: bash scripts/run_cal02.sh {setup|test|pack}"; exit 2 ;;
esac
