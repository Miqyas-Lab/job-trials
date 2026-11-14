#!/bin/bash
# miqyas · bf-01 — adapter back-fill (trials/bf-01-adapter-backfill.yaml).
# Both tool paths (own format + prompted-JSON adapter) for Jais 3 3.7B, Jais 3 7B, Qwen3 8B and Fanar 2 27B, tool setup.
# Pod: RTX 4090, PyTorch template, CONTAINER/VOLUME DISK >= 150 GB (Fanar bf16 conversion). Run every step DETACHED:
#   setsid nohup bash scripts/run_bf01.sh setup       > bf01_setup.log  2>&1 < /dev/null &   (~15 min)
#   setsid nohup bash scripts/run_bf01.sh pilot       > bf01_pilot.log  2>&1 < /dev/null &   (~15 min)  -> share PILOT CHECK lines
#   setsid nohup bash scripts/run_bf01.sh test        > bf01_test.log   2>&1 < /dev/null &   (~3 h)
#   setsid nohup bash scripts/run_bf01.sh fanar-setup > bf01_fsetup.log 2>&1 < /dev/null &   (~45 min: build + 54 GB + convert)
#   setsid nohup bash scripts/run_bf01.sh fanar-pilot > bf01_fpilot.log 2>&1 < /dev/null &   (~15 min)  -> share PILOT CHECK line
#   setsid nohup bash scripts/run_bf01.sh fanar-test  > bf01_ftest.log  2>&1 < /dev/null &   (~2-3 h)
#   bash scripts/run_bf01.sh pack
# Watch progress:  tail -3 bf01_test.log   or   wc -l results/bf01/*/runs.jsonl   (144 lines = one path done)
set -u
cd "$(dirname "$0")/.."
exec 9> /tmp/run_bf01.lock
if ! flock -n 9; then echo "Another run_bf01.sh is already running — not starting a second one."; exit 1; fi
OUT="results/bf01"
CTX=32768
NPRED=8192
LL_A="$HOME/llama.cpp-7df8b87"     # Jais, Qwen (qt-02 build)
LL_F="$HOME/llama.cpp-9c9074e"     # Fanar (qt-03 build)
FREPO="QCRI/Fanar-2-27B-Instruct"
FREV="074005040e9c3511b1c43b4298bef09908285534"
FGGUF="models/gpu/Fanar-2-27B-Instruct-Q4_K_M.gguf"
FSHA="582453644729b1e1d69cdbc7b37722a06f6ed87b09b135c23468df0591520c00"
FTPL="results/qt03/chat_template_llamacpp.jinja"
# key  gguf  native-mode  effort  sampling-flag
SMALL=(
  "qwen3-8b    Qwen3-8B-Q4_K_M.gguf     chat  off  "
  "jais3-3.7b  Jais-3-3.7B-Q4_K_M.gguf  jais  low  --sampling jais"
  "jais3-7b    Jais-3-7B-Q4_K_M.gguf    jais  low  --sampling jais"
)

build () {   # $1 dir  $2 commit  $3 targets
  [ -x "$1/build/bin/llama-server" ] && return 0
  echo "== building llama.cpp $2 with CUDA (about 10 minutes) =="
  pip install -q -U cmake huggingface_hub
  command -v git >/dev/null || (apt-get update -q && apt-get install -y -q git)
  [ -d "$1" ] || git clone https://github.com/ggml-org/llama.cpp "$1"
  (cd "$1" && git checkout -q "$2" && cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CUDA_ARCHITECTURES=native && cmake --build build -j 16 --target $3) || exit 1
}

start_server () {   # $1 llama dir  $2 gguf  $3 extra args
  pkill -f llama-server; sleep 2
  "$1/build/bin/llama-server" -m "$2" --jinja $3 -ngl 99 -c $CTX -np 1 --port 8080 > /tmp/server_bf01.log 2>&1 9>&- &
  for i in $(seq 1 240); do curl -s localhost:8080/health | grep -q '"ok"' && return 0; sleep 2; done
  echo "server did not start — last log lines:"; tail -20 /tmp/server_bf01.log; return 1
}

pilot_check () {   # $1 runs.jsonl  — the limits in the pre-registration
  python3 - "$1" <<'PY'
import json, sys
R = [json.loads(l) for l in open(sys.argv[1])]
st = [s for r in R if 'steps' in r for s in r['steps']]
bad = sum(1 for s in st if s.get('parsed') is False)
reason = sum(1 for s in st if (s.get('reasoning') or '').strip())
err = sum('error' in r for r in R); ctx = sum(r.get('flags', {}).get('context', False) for r in R)
p0 = (R[0]['steps'][0].get('prompt_n') or 0) + (R[0]['steps'][0].get('cached_n') or 0) if R and R[0].get('steps') else 0
ok = err == 0 and ctx == 0 and st and bad / len(st) <= 0.10 and p0 >= 1000
print(f"PILOT CHECK {sys.argv[1].split('/')[-2]}: runs {len(R)} · errors {err} · context overflows {ctx} · steps {len(st)} · "
      f"not parsed {bad} ({100*bad/max(len(st),1):.0f}%) · steps with reasoning {reason} · first prompt tokens {p0} · {'OK' if ok else 'STOP'}")
PY
}

run_path () {   # $1 label  $2 mode  $3 effort  $4 split  $5 reps  $6 safety  $7 sampling-flag...
  local label=$1 mode=$2 eff=$3 split=$4 reps=$5 safety=$6; shift 6
  python3 scripts/run_v2.py --label "$label" --mode "$mode" "$@" --split "$split" --arms tool --efforts "$eff" \
      --reps "$reps" --safety-reps "$safety" --n-predict $NPRED --out-root "$OUT" || return 1
  python3 scripts/score_v2.py "$OUT/$label" | tee "$OUT/$label/scorecard.txt"
}

case "${1:-}" in
setup)
  build "$LL_A" 7df8b87 llama-server
  command -v hf >/dev/null || pip install -q -U huggingface_hub
  mkdir -p models/gpu "$OUT"; df -h . | tail -1
  for row in "Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf" "IFM/Jais-3-3.7B-GGUF Jais-3-3.7B-Q4_K_M.gguf" "IFM/Jais-3-7B-GGUF Jais-3-7B-Q4_K_M.gguf"; do
    set -- $row
    [ -f "models/gpu/$2" ] || hf download "$1" "$2" --local-dir models/gpu >/dev/null || { echo "DOWNLOAD FAILED: $1/$2"; exit 1; }
  done
  (cd models/gpu && grep -E "Qwen3-8B|Jais-3-3.7B|Jais-3-7B" ../../results/frontdesk_v2/models_sha256.txt | sha256sum -c -) \
    || { echo "STOP: GGUF files differ from the registered ones"; exit 1; }
  { echo "llama.cpp (Jais, Qwen) $(cd "$LL_A" && git rev-parse --short HEAD)"; echo "repo commit $(git rev-parse --short HEAD)";
    (cd models/gpu && sha256sum Qwen3-8B-Q4_K_M.gguf Jais-3-3.7B-Q4_K_M.gguf Jais-3-7B-Q4_K_M.gguf); } > "$OUT/model_provenance.txt"
  cat "$OUT/model_provenance.txt"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | tee "$OUT/gpu.txt"
  grep -q "def prompted_kwargs" scripts/run_v2.py || { echo "STOP: runner without the bf-01 adapter switch"; exit 1; }
  python3 scripts/test_v2.py || exit 1
  echo "SETUP OK — next: setsid nohup bash scripts/run_bf01.sh pilot > bf01_pilot.log 2>&1 < /dev/null &"
  ;;
pilot)
  for row in "${SMALL[@]}"; do
    read -r key gguf mode eff samp <<< "$row"
    start_server "$LL_A" "models/gpu/$gguf" "" || exit 1
    run_path "pilot-$key-prompted" prompted "$eff" dev 1 0 $samp > /dev/null
    pilot_check "$OUT/pilot-$key-prompted/runs.jsonl"
  done
  pkill -f llama-server
  echo "PILOT DONE — share the three PILOT CHECK lines before running 'test'."
  ;;
test)
  for row in "${SMALL[@]}"; do
    read -r key gguf mode eff samp <<< "$row"
    pilot_check "$OUT/pilot-$key-prompted/runs.jsonl" | grep -q " OK$" || { echo "STOP: $key pilot not OK — amendment first"; exit 1; }
    start_server "$LL_A" "models/gpu/$gguf" "" || exit 1
    run_path "$key-native" "$mode" "$eff" test 3 2 $samp || exit 1
    run_path "$key-prompted" prompted "$eff" test 3 2 $samp || exit 1
  done
  pkill -f llama-server
  echo "TEST DONE — next: setsid nohup bash scripts/run_bf01.sh fanar-setup > bf01_fsetup.log 2>&1 < /dev/null &"
  ;;
fanar-setup)
  [ -d "$LL_F" ] || git clone https://github.com/ggml-org/llama.cpp "$LL_F"
  build "$LL_F" 9c9074e "llama-server llama-quantize"
  df -h . | tail -1
  if [ ! -f "$FGGUF" ]; then
    pip install -q -r "$LL_F/requirements/requirements-convert_hf_to_gguf.txt" || pip install -q gguf sentencepiece safetensors transformers
    hf download "$FREPO" --revision "$FREV" --local-dir models/hf/fanar-2-27b || { echo "DOWNLOAD FAILED: $FREPO@$FREV"; exit 1; }
    python3 "$LL_F/convert_hf_to_gguf.py" models/hf/fanar-2-27b --outtype bf16 --outfile models/gpu/fanar-2-27b-bf16.gguf || exit 1
    "$LL_F/build/bin/llama-quantize" models/gpu/fanar-2-27b-bf16.gguf "$FGGUF" Q4_K_M || exit 1
    rm -f models/gpu/fanar-2-27b-bf16.gguf   # free ~54 GB
  fi
  echo "$FSHA  $FGGUF" | sha256sum -c - || { echo "STOP: the converted GGUF differs from qt-03"; exit 1; }
  python3 scripts/fix_raw_template.py models/hf/fanar-2-27b/chat_template.jinja /tmp/bf01_fanar_tpl.jinja || exit 1
  cmp -s /tmp/bf01_fanar_tpl.jinja "$FTPL" || { echo "STOP: converted template differs from qt-03"; exit 1; }
  { echo "llama.cpp (Fanar) $(cd "$LL_F" && git rev-parse --short HEAD)"; sha256sum "$FGGUF"; } >> "$OUT/model_provenance.txt"
  tail -2 "$OUT/model_provenance.txt"
  echo "FANAR SETUP OK — next: setsid nohup bash scripts/run_bf01.sh fanar-pilot > bf01_fpilot.log 2>&1 < /dev/null &"
  ;;
fanar-pilot)
  start_server "$LL_F" "$FGGUF" "--chat-template-file $FTPL" || exit 1
  run_path pilot-fanar-2-27b-prompted prompted off dev 1 0 --sampling fanar-2 > /dev/null
  pilot_check "$OUT/pilot-fanar-2-27b-prompted/runs.jsonl"
  pkill -f llama-server
  echo "PILOT DONE — share the PILOT CHECK line before running 'fanar-test'."
  ;;
fanar-test)
  pilot_check "$OUT/pilot-fanar-2-27b-prompted/runs.jsonl" | grep -q " OK$" || { echo "STOP: Fanar pilot not OK — amendment first"; exit 1; }
  start_server "$LL_F" "$FGGUF" "--chat-template-file $FTPL" || exit 1
  run_path fanar-2-27b-native template off test 3 2 --sampling fanar-2 || exit 1
  run_path fanar-2-27b-prompted prompted off test 3 2 --sampling fanar-2 || exit 1
  pkill -f llama-server; echo "FANAR TEST DONE — next: bash scripts/run_bf01.sh pack"
  ;;
pack)
  tar czf bf01_results.tar.gz "$OUT" && ls -la bf01_results.tar.gz
  echo "Download bf01_results.tar.gz from JupyterLab (right-click > Download), then STOP the pod."
  ;;
*) echo "usage: bash scripts/run_bf01.sh {setup|pilot|test|fanar-setup|fanar-pilot|fanar-test|pack}"; exit 2 ;;
esac
