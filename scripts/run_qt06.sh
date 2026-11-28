#!/bin/bash
# miqyas · qt-06 — the exam01 re-test at higher precision, Quick Trial (promised in the exam01 thread).
# The original: prompts/p1.txt, qwen3:8b through Ollama 0.32.14 with thinking off, 4-bit default, one sample on the
# Mac mini M4, 20 Aug 2026 (results/raw/m4_q_p1_qwen3_8b_nothink_20260820_022041.txt, request from quality.sh).
# Here: the same request on the same Ollama version at three precisions — qwen3:8b (4-bit, the control on this card),
# qwen3:8b-q8_0, qwen3:8b-fp16 — 20 samples each, sample 1 at the original seed 42.
# Pod: RTX 4090, any CUDA template, CONTAINER/VOLUME DISK >= 50 GB. Run every step DETACHED:
#   setsid nohup bash scripts/run_qt06.sh setup > qt06_setup.log 2>&1 < /dev/null &   (~25 min: Ollama + ~30 GB pulls)
#        -> share the SETUP lines (Ollama version, GPU, one ID line per model)
#   setsid nohup bash scripts/run_qt06.sh pilot > qt06_pilot.log 2>&1 < /dev/null &   (~2 min) -> share the 3 PILOT lines
#   setsid nohup bash scripts/run_qt06.sh test  > qt06_test.log  2>&1 < /dev/null &   (~10 min, 60 samples)
#   bash scripts/run_qt06.sh pack
# Watch progress:  ls results/qt06/*/ | grep -c json   (60 = done)
# Is it alive?  ps aux | grep -c "[r]un_qt06.sh"   (1 or more = running)
# A sample already on disk is never run again, so any step can be re-run after a lost connection; qt06_results.tar.gz
# is rewritten after each level.
set -u
cd "$(dirname "$0")/.."
exec 9> /tmp/run_qt06.lock
if ! flock -n 9; then echo "Another run_qt06.sh is already running — not starting a second one."; exit 1; fi
OUT="results/qt06"
OLLAMA_VERSION="0.32.14"
URL="${OLLAMA_URL:-http://localhost:11434}"
LEVELS=("q4:qwen3:8b" "q8_0:qwen3:8b-q8_0" "fp16:qwen3:8b-fp16")   # label:tag
SEEDS=(42 $(seq 1 19))
mkdir -p "$OUT"

serve () {
  curl -s "$URL/api/version" >/dev/null && return 0
  OLLAMA_HOST=127.0.0.1:11434 nohup ollama serve > /tmp/ollama_qt06.log 2>&1 9>&- &
  for i in $(seq 1 60); do curl -s "$URL/api/version" >/dev/null && return 0; sleep 2; done
  echo "ollama did not start — last log lines:"; tail -20 /tmp/ollama_qt06.log; return 1
}

one () {   # one sample, written exactly as quality.sh wrote the original: a header line, then Ollama's JSON
  local label=$1 tag=$2 seed=$3 f="$OUT/$1/s$3.json"
  [ -s "$f" ] && return 0
  mkdir -p "$OUT/$label"
  python3 - "$tag" "$seed" > /tmp/qt06_body.json <<'PY' || return 1
import json, sys
p = open("prompts/p1.txt", encoding="utf-8").read().replace("\n", "")   # quality.sh: tr -d '\n'
print(json.dumps({"model": sys.argv[1], "prompt": p, "stream": False,
                  "options": {"num_predict": 500, "temperature": 0.7, "seed": int(sys.argv[2])}, "think": False},
                 ensure_ascii=False))
PY
  local r; r=$(curl -s --max-time 600 "$URL/api/generate" -d @/tmp/qt06_body.json) || return 1
  echo "$r" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('done') and 'response' in d" 2>/dev/null \
    || { echo "sample $label s$seed failed: ${r:0:300}"; return 1; }
  { echo "=== p1 | $tag think:false seed:$seed | $(date -u +%Y%m%dT%H%M%SZ) ==="; echo "$r"; } > "$f.tmp" && mv "$f.tmp" "$f"
}

pack () { tar czf qt06_results.tar.gz "$OUT" && echo "PACKED qt06_results.tar.gz ($(ls "$OUT"/*/*.json 2>/dev/null | wc -l) samples)"; }

case "${1:-}" in
  setup)
    if ! ollama --version 2>/dev/null | grep -q "$OLLAMA_VERSION"; then
      command -v zstd >/dev/null || (apt-get update -q && apt-get install -y -q zstd curl)
      curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION="$OLLAMA_VERSION" sh || exit 1
    fi
    serve || exit 1
    for lv in "${LEVELS[@]}"; do ollama pull "${lv#*:}" || exit 1; done
    {
      echo "SETUP ollama $(curl -s "$URL/api/version")"
      echo "SETUP gpu $(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo none)"
      for lv in "${LEVELS[@]}"; do ollama list | awk -v t="${lv#*:}" '$1==t {print "SETUP model", $1, $2, $3 $4}'; done
    } | tee "$OUT/setup.txt"
    ;;
  pilot)
    serve || exit 1
    for lv in "${LEVELS[@]}"; do
      one "${lv%%:*}" "${lv#*:}" 42 || exit 1
      python3 - "$OUT/${lv%%:*}/s42.json" <<'PY'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read().split("\n", 1)[1])
print("PILOT", d["model"], "eval_count", d["eval_count"], "done_reason", d["done_reason"],
      "|", d["response"].replace("\n", " ")[:120])
PY
    done
    ;;
  test)
    serve || exit 1
    for lv in "${LEVELS[@]}"; do
      for s in "${SEEDS[@]}"; do one "${lv%%:*}" "${lv#*:}" "$s" || exit 1; done
      echo "LEVEL ${lv%%:*} done: $(ls "$OUT/${lv%%:*}"/*.json | wc -l) samples"; pack
    done
    ;;
  pack) pack ;;
  *) echo "usage: bash scripts/run_qt06.sh setup|pilot|test|pack"; exit 2 ;;
esac
