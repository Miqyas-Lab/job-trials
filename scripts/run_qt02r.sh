#!/bin/bash
# miqyas · qt-02r — re-run of the Falcon-H1-7B-Instruct Quick Trial after the harness fault (qt-02 amendment of
# 2026-11-12). Same official GGUF (sha256 checked against results/qt02/model_provenance.txt), same llama.cpp build
# 7df8b87, same sampling, window and generation cap, all three setups. The only change is the history: the runner
# keeps the call text in the assistant message as the model wrote it (scripts/run_v2.py, qt-03 amendment 2).
#
# On a RunPod pod (RTX 4090, PyTorch template), from the repo root. Run every step DETACHED:
#   setsid nohup bash scripts/run_qt02r.sh setup > qt02r_setup.log 2>&1 < /dev/null &   (~15 min)
#   setsid nohup bash scripts/run_qt02r.sh test  > qt02r_test.log  2>&1 < /dev/null &   (~45-75 min)
#   bash scripts/run_qt02r.sh pack
# Check progress with: tail -5 qt02r_<step>.log   (closing the terminal does not stop the run)
set -u
cd "$(dirname "$0")/.."
exec 9> /tmp/run_qt02r.lock
if ! flock -n 9; then echo "Another run_qt02r.sh is already running — not starting a second one."; exit 1; fi
LL="$HOME/llama.cpp-7df8b87"
SERVER="$LL/build/bin/llama-server"
LLAMA_COMMIT="7df8b87"
GREPO="tiiuae/Falcon-H1-7B-Instruct-GGUF"
GGUF="models/gpu/Falcon-H1-7B-Instruct-Q4_K_M.gguf"
GGUF_SHA="145def0b4cd36500bf538ed7ac895b5c1851e02e802b2d1c12ffa6afdbaff25d"   # results/qt02/model_provenance.txt
OUT="results/qt02r"
LABEL="falcon-h1-7b-q4-qt02r"
CTX=32768
NPRED=8192
start_server () {
  pkill -f llama-server; sleep 2
  "$SERVER" -m "$GGUF" --jinja -ngl 99 -c $CTX -np 1 --port 8080 > /tmp/server_qt02r.log 2>&1 9>&- &
  for i in $(seq 1 180); do curl -s localhost:8080/health | grep -q '"ok"' && return 0; sleep 2; done
  echo "server did not start — last log lines:"; tail -20 /tmp/server_qt02r.log; return 1
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
  echo "$GGUF_SHA  $GGUF" | sha256sum -c - || { echo "STOP: the GGUF differs from the one qt-02 used"; exit 1; }
  { echo "llama.cpp $(cd "$LL" && git rev-parse --short HEAD)"; echo "repo commit $(git rev-parse --short HEAD)";
    echo "source: official GGUF ($GREPO), same file as qt-02"; sha256sum "$GGUF"; } > "$OUT/model_provenance.txt"
  cat "$OUT/model_provenance.txt"
  grep -q "history_content" scripts/run_v2.py || { echo "STOP: runner without the history fix"; exit 1; }
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
  python3 scripts/test_v2.py || exit 1
  echo "SETUP OK — next: setsid nohup bash scripts/run_qt02r.sh test > qt02r_test.log 2>&1 < /dev/null &"
  ;;
test)
  start_server || exit 1
  python3 scripts/run_v2.py --label "$LABEL" --mode template --sampling falcon-h1 --split test --arms base table tool --efforts off \
      --reps 3 --safety-reps 2 --n-predict $NPRED --out-root "$OUT"
  python3 scripts/score_v2.py "$OUT/$LABEL" | tee "$OUT/$LABEL/scorecard.txt"
  pkill -f llama-server; echo "TEST DONE — next: bash scripts/run_qt02r.sh pack"
  ;;
pack)
  tar czf qt02r_results.tar.gz "$OUT" && ls -la qt02r_results.tar.gz
  echo "Download qt02r_results.tar.gz from JupyterLab (right-click > Download), then STOP the pod."
  ;;
*) echo "usage: bash scripts/run_qt02r.sh {setup|test|pack}"; exit 2 ;;
esac
