#!/bin/bash
# miqyas · Job Trial #2 stage 1 — Riyadh clinic (trials/jt-02-riyadh-clinic.yaml).
# Eight models, both tool paths where both exist, three setups, public and private Riyadh sets.
# Pod: RTX 4090, PyTorch template, disk >= 150 GB (conversions run first, largest first; peak about 140 GB). Run every long step DETACHED:
#   setsid nohup bash scripts/run_jt02.sh setup  > jt02_setup.log 2>&1 < /dev/null &   (~1.5 h: 3 builds, downloads, 3 conversions)
#   (upload the private file, see 'private' below, then)  bash scripts/run_jt02.sh private
#   setsid nohup bash scripts/run_jt02.sh pilot  > jt02_pilot.log 2>&1 < /dev/null &   (~30 min)  -> share the PILOT CHECK lines
#   setsid nohup bash scripts/run_jt02.sh test   > jt02_test.log  2>&1 < /dev/null &   (~15 h; resumable: finished paths are skipped)
#   bash scripts/run_jt02.sh pack
# Watch progress:  tail -3 jt02_test.log   or   ls results/jt02/
set -u
cd "$(dirname "$0")/.."
exec 9> /tmp/run_jt02.lock
if ! flock -n 9; then echo "Another run_jt02.sh is already running — not starting a second one."; exit 1; fi
export MIQYAS_CLINIC=riyadh
OUT="results/jt02"; POUT="private/results"
PUB="corpus/frontdesk_riyadh.jsonl"
PRIV="private/riyadh_private_test.jsonl"
PRIV_SHA="18742b54a902e0f5f35e1954f41d804e419fad6974ad4a92fe8f0a0168d4509f"
LAB_AGE_KEY="age1r8nur5l2rr624ck8mu08e7qdndkwct8rj0z8ml8kcc083kq0rpaspjsc4q"
LL_A="$HOME/llama.cpp-7df8b87"; LL_F="$HOME/llama.cpp-9c9074e"; LL_L="$HOME/llama.cpp-8642541"
# key | gguf | build | own-format mode ("-" = none) | effort | sampling | window | cap | chat template file ("-" = model's own)
MODELS=(
  "jais3-7b|Jais-3-7B-Q4_K_M.gguf|A|jais|low|jais|32768|8192|-"
  "jais3-3.7b|Jais-3-3.7B-Q4_K_M.gguf|A|jais|low|jais|32768|8192|-"
  "qwen3-8b|Qwen3-8B-Q4_K_M.gguf|A|chat|off|qwen-nothink|32768|8192|-"
  "qwen3-4b|Qwen3-4B-Q4_K_M.gguf|A|chat|off|qwen-nothink|32768|8192|-"
  "falcon-h1-7b|Falcon-H1-7B-Instruct-Q4_K_M.gguf|A|template|off|falcon-h1|32768|8192|-"
  "allam-7b|ALLaM-7B-Instruct-preview-Q4_K_M.gguf|A|-|off|allam|4096|4096|-"
  "silma-9b|SILMA-9B-Instruct-v1.0-Q4_K_M.gguf|A|-|off|silma-greedy|8192|4096|results/qt04/chat_template_llamacpp.jinja"
  "fanar-2-27b|Fanar-2-27B-Instruct-Q4_K_M.gguf|F|template|off|fanar-2|32768|8192|results/qt03/chat_template_llamacpp.jinja"
)
SHAS="a8caa7fecf38d064f216f66d3d59641c1fbefdca9756af0703f4a872ab852eeb  models/gpu/Jais-3-7B-Q4_K_M.gguf
d2039e169049f0646f79bc27aec82ffc0842ff9af1bf75bfc16628929636e09a  models/gpu/Jais-3-3.7B-Q4_K_M.gguf
d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785  models/gpu/Qwen3-8B-Q4_K_M.gguf
7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5  models/gpu/Qwen3-4B-Q4_K_M.gguf
145def0b4cd36500bf538ed7ac895b5c1851e02e802b2d1c12ffa6afdbaff25d  models/gpu/Falcon-H1-7B-Instruct-Q4_K_M.gguf
858e7d3f8573548a79810d96f6164d48d2c6415d4822b5d9b39f5864a42a8544  models/gpu/ALLaM-7B-Instruct-preview-Q4_K_M.gguf
71bf624f9277bb7d7c2c69f1c26fc1ed50d6940d8c3de847c0219bbd67c08198  models/gpu/SILMA-9B-Instruct-v1.0-Q4_K_M.gguf
582453644729b1e1d69cdbc7b37722a06f6ed87b09b135c23468df0591520c00  models/gpu/Fanar-2-27B-Instruct-Q4_K_M.gguf"

build () {   # $1 dir  $2 commit  $3 targets
  [ -x "$1/build/bin/llama-quantize" ] && return 0
  echo "== building llama.cpp $2 =="
  [ -d "$1" ] || git clone -q https://github.com/ggml-org/llama.cpp "$1"
  (cd "$1" && git checkout -q "$2" && cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CUDA_ARCHITECTURES=native && cmake --build build -j 16 --target $3) || { echo "STOP: llama.cpp $2 did not build (see the lines above)"; exit 1; }
}

convert () {   # $1 llama dir  $2 repo  $3 revision ("" = latest)  $4 outtype  $5 gguf name
  [ -f "models/gpu/$5" ] && return 0
  local hf="models/hf/${5%.gguf}" rev=""
  [ -n "$3" ] && rev="--revision $3"
  pip install -q -r "$1/requirements/requirements-convert_hf_to_gguf.txt" 2>/dev/null || pip install -q gguf sentencepiece safetensors transformers
  hf download "$2" $rev --local-dir "$hf" >/dev/null || { echo "DOWNLOAD FAILED: $2"; exit 1; }
  python3 "$1/convert_hf_to_gguf.py" "$hf" --outtype "$4" --outfile "models/gpu/tmp-$4.gguf" || exit 1
  rm -rf "$hf"                                  # free the download before quantizing (disk: Fanar is 54 GB twice)
  "$1/build/bin/llama-quantize" "models/gpu/tmp-$4.gguf" "models/gpu/$5" Q4_K_M >/dev/null || exit 1
  rm -f "models/gpu/tmp-$4.gguf"
}

start_server () {   # $1 build A|F  $2 gguf  $3 window  $4 template file or -
  local ll="$LL_A" tpl=""; [ "$1" = F ] && ll="$LL_F"; [ "$4" != "-" ] && tpl="--chat-template-file $4"
  pkill -f llama-server; sleep 2
  "$ll/build/bin/llama-server" -m "models/gpu/$2" --jinja $tpl -ngl 99 -c "$3" -np 1 --port 8080 > /tmp/server_jt02.log 2>&1 9>&- &
  for i in $(seq 1 300); do curl -s localhost:8080/health | grep -q '"ok"' && return 0; sleep 2; done
  echo "server did not start — last log lines:"; tail -20 /tmp/server_jt02.log; return 1
}

selftest () {   # $1 name  $2 site  $3 episodes file ("" = Job Trial #1 corpus); prints one line, never a message
  local out; out=$(MIQYAS_CLINIC="$2" MIQYAS_EPISODES="$3" python3 scripts/test_v2.py 2>&1 | tail -1)
  case "$out" in "all self-tests passed"*) echo "self-test $1: passed";;
    *) echo "STOP: self-test $1 failed (scenario ids: $(MIQYAS_CLINIC="$2" MIQYAS_EPISODES="$3" python3 scripts/test_v2.py 2>&1 | grep -o 'failed [a-z0-9]*' | sort -u | tr '\n' ' '))"; return 1;; esac
}

paths_of () {   # $1 own-format mode -> the paths to run
  if [ "$1" = "-" ]; then echo "prompted"; else echo "$1 prompted"; fi
}

case "${1:-}" in
setup)
  pip install -q -U cmake huggingface_hub pyrage
  mkdir -p models/gpu "$OUT" private; df -h . | tail -1
  build "$LL_A" 7df8b87 "llama-server llama-quantize"
  build "$LL_F" 9c9074e "llama-server llama-quantize"
  build "$LL_L" 8642541 "llama-quantize"
  convert "$LL_F" QCRI/Fanar-2-27B-Instruct 074005040e9c3511b1c43b4298bef09908285534 bf16 Fanar-2-27B-Instruct-Q4_K_M.gguf
  convert "$LL_A" silma-ai/SILMA-9B-Instruct-v1.0 d8f4d2b11a71e10f4231d38f0a343ee49715f392 bf16 SILMA-9B-Instruct-v1.0-Q4_K_M.gguf
  convert "$LL_L" ALLaM-AI/ALLaM-7B-Instruct-preview 9c52c12c398b9184511520814d1a44c88f2cc5a9 f16 ALLaM-7B-Instruct-preview-Q4_K_M.gguf
  for row in "IFM/Jais-3-7B-GGUF Jais-3-7B-Q4_K_M.gguf" "IFM/Jais-3-3.7B-GGUF Jais-3-3.7B-Q4_K_M.gguf" \
             "Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf" "Qwen/Qwen3-4B-GGUF Qwen3-4B-Q4_K_M.gguf" \
             "tiiuae/Falcon-H1-7B-Instruct-GGUF Falcon-H1-7B-Instruct-Q4_K_M.gguf"; do
    set -- $row
    [ -f "models/gpu/$2" ] || hf download "$1" "$2" --local-dir models/gpu >/dev/null || { echo "DOWNLOAD FAILED: $1/$2"; exit 1; }
  done
  echo "$SHAS" | sha256sum -c - || { echo "STOP: a model file differs from the registered one (that model stops; amendment first)"; exit 1; }
  { for d in "$LL_A" "$LL_F" "$LL_L"; do echo "llama.cpp $(cd "$d" && git rev-parse --short HEAD)"; done
    echo "repo commit $(git rev-parse --short HEAD)"; echo "$SHAS"; } > "$OUT/model_provenance.txt"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | tee "$OUT/gpu.txt"
  selftest "Dubai (Job Trial #1)" dubai "" || exit 1
  selftest "Riyadh public and dev" riyadh "$PUB" || exit 1
  echo "SETUP OK — next: upload the private file to $PRIV (see 'private'), then: bash scripts/run_jt02.sh private"
  ;;
private)   # the founder uploads the decrypted private file to private/ (JupyterLab upload); this checks it
  [ -f "$PRIV" ] || { echo "Upload riyadh_private_test.jsonl into the folder 'private' first."; exit 1; }
  echo "$PRIV_SHA  $PRIV" | sha256sum -c - || { echo "STOP: the private file differs from the registered one"; exit 1; }
  selftest "Riyadh private" riyadh "$PRIV" || exit 1
  echo "PRIVATE OK — next: setsid nohup bash scripts/run_jt02.sh pilot > jt02_pilot.log 2>&1 < /dev/null &"
  ;;
pilot)
  for row in "${MODELS[@]}"; do
    IFS='|' read -r key gguf b mode eff samp win cap tpl <<< "$row"
    start_server "$b" "$gguf" "$win" "$tpl" || exit 1
    for p in $(paths_of "$mode"); do
      lab="pilot-$key-$p"
      python3 scripts/run_v2.py --label "$lab" --mode "$p" --sampling "$samp" --episodes "$PUB" --split dev --arms tool \
          --efforts "$eff" --reps 1 --safety-reps 0 --n-predict "$cap" --out-root "$OUT" > /dev/null || exit 1
      python3 - "$OUT/$lab/runs.jsonl" "$p" <<'PY'
import json, sys
R = [json.loads(l) for l in open(sys.argv[1])]
st = [s for r in R if 'steps' in r for s in r['steps']]
bad = sum(1 for s in st if s.get('parsed') is False)
err = sum('error' in r for r in R)
p0 = [(r['steps'][0].get('prompt_n') or 0) + (r['steps'][0].get('cached_n') or 0) for r in R if r.get('steps')]
ok = err == 0 and (sys.argv[2] != 'prompted' or bad <= 0.10 * max(len(st), 1)) and p0 and min(p0) >= 1000
print(f"PILOT CHECK {sys.argv[1].split('/')[-2]}: runs {len(R)} · errors {err} · unparsed {bad}/{len(st)} · "
      f"first prompt {min(p0) if p0 else '-'}-{max(p0) if p0 else '-'} tokens · {'OK' if ok else 'STOP'}")
PY
    done
  done
  grep -l '"clinic_site": "riyadh"' "$OUT"/pilot-*/meta.json | wc -l | xargs echo "pilot runs recorded as Riyadh:"
  pkill -f llama-server; echo "PILOT DONE — share the PILOT CHECK lines before running 'test'."
  ;;
test)
  echo "$PRIV_SHA  $PRIV" | sha256sum -c - >/dev/null || { echo "STOP: private file missing or changed"; exit 1; }
  for row in "${MODELS[@]}"; do
    IFS='|' read -r key gguf b mode eff samp win cap tpl <<< "$row"
    started=0
    for p in $(paths_of "$mode"); do
      for set in public private; do
        if [ "$set" = public ]; then root="$OUT"; eps="$PUB"; else root="$POUT"; eps="$PRIV"; fi
        lab="$key-$p-$set"
        [ -f "$root/$lab/scorecard.txt" ] && { echo "skip $lab (done)"; continue; }
        [ $started = 1 ] || { start_server "$b" "$gguf" "$win" "$tpl" || exit 1; started=1; }
        rm -rf "$root/$lab"
        python3 scripts/run_v2.py --label "$lab" --mode "$p" --sampling "$samp" --episodes "$eps" --split test \
            --arms base table tool --efforts "$eff" --reps 3 --safety-reps 2 --n-predict "$cap" --out-root "$root" || exit 1
        python3 scripts/score_v2.py "$root/$lab" > "$root/$lab/scorecard.txt" || exit 1
        echo "done $lab"
      done
    done
  done
  pkill -f llama-server; echo "TEST DONE — next: bash scripts/run_jt02.sh pack"
  ;;
pack)
  tar czf jt02_results.tar.gz "$OUT" && ls -la jt02_results.tar.gz
  python3 - "$POUT" "$LAB_AGE_KEY" <<'PY'
import io, os, sys, tarfile
from pyrage import encrypt, x25519
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as t:
    t.add(sys.argv[1], arcname="private_results")
open("jt02_private_results.tar.gz.age", "wb").write(encrypt(buf.getvalue(), [x25519.Recipient.from_str(sys.argv[2])]))
print("jt02_private_results.tar.gz.age written (private raw conversations, encrypted to the lab key)")
PY
  rm -rf private/
  echo "Download jt02_results.tar.gz and jt02_private_results.tar.gz.age, then STOP the pod (the private folder was deleted)."
  ;;
*) echo "usage: bash scripts/run_jt02.sh {setup|private|pilot|test|pack}"; exit 2 ;;
esac
