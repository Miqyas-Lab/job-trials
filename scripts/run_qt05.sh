#!/bin/bash
# miqyas · qt-05 — Inkling 2 Mini, clinic front desk, Quick Trial (trials/qt-05-inkling-2-mini-clinic.yaml).
# The publisher does not claim Arabic support for this model; we tested it because we promised to, as a dated exception
# to our inclusion rule (see inclusion_exception in the trial file).
# Pod: RTX 4090, PyTorch template, CONTAINER/VOLUME DISK >= 60 GB. Run every step DETACHED:
#   setsid nohup bash scripts/run_qt05.sh setup  > qt05_setup.log 2>&1 < /dev/null &   (~20 min: build + ~18 GB + checks)
#        -> share the SETUP lines (llama.cpp commit, GGUF file and sha256, n_ctx_train, params, TEMPLATE CHECK)
#   setsid nohup bash scripts/run_qt05.sh pilot  > qt05_pilot.log 2>&1 < /dev/null &   (~20 min) -> share the 4 PILOT CHECK lines
#   setsid nohup bash scripts/run_qt05.sh test   > qt05_test.log  2>&1 < /dev/null &   (4 parts of 144 runs)
#   bash scripts/run_qt05.sh pack
# Watch progress:  tail -3 qt05_test.log   or   wc -l results/qt05/*/runs.jsonl   (144 lines = one part done)
# Is it alive?  ps aux | grep -c "[r]un_v2.py"   (1 = running, 0 = stopped: a log line that never changes is not proof)
# Each part starts a fresh server with the prompt cache in normal memory off (--cache-ram 0); finished parts are
# skipped when a step is run again; qt05_results.tar.gz is rewritten after every finished part, so download it now
# and then: a lost pod costs at most the part in progress.
set -u
cd "$(dirname "$0")/.."
exec 9> /tmp/run_qt05.lock
if ! flock -n 9; then echo "Another run_qt05.sh is already running — not starting a second one."; exit 1; fi
OUT="results/qt05"
CTX=32768
NPRED=8192
LL="$HOME/llama.cpp-qt05"
LL_COMMIT="${LL_COMMIT:-master}"   # setup records the exact commit; the trial file registers it by amendment before the pilot
MREPO="thinkingmachines/Inkling-2-Mini"
MREV="7a67ae2314b44ef05c87fd1d4d311c58aaeb18f6"
GREPO="ggml-org/Inkling-2-Mini-GGUF"
EFF="none"                         # the lowest reasoning effort the template offers (effort_map: none 0.0)
SAMP="--sampling inkling-2-mini"   # temperature 1.0 (generation_config.json), other samplers neutral
# label  mode  arm
PARTS=(
  "tool-native    chat      tool"
  "tool-adapter   prompted  tool"
  "table-native   chat      table"
  "base-native    chat      base"
)

gguf () { ls models/gpu/qt05/*.gguf 2>/dev/null | grep -v -i mmproj | head -1; }

build () {
  [ -x "$LL/build/bin/llama-server" ] && return 0
  echo "== building llama.cpp $LL_COMMIT with CUDA (about 10 minutes) =="
  pip install -q -U cmake huggingface_hub jinja2
  command -v git >/dev/null || (apt-get update -q && apt-get install -y -q git)
  [ -d "$LL" ] || git clone https://github.com/ggml-org/llama.cpp "$LL"
  (cd "$LL" && git fetch -q origin && git checkout -q "$LL_COMMIT" && cmake -B build -DGGML_CUDA=ON -DLLAMA_CURL=OFF \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES=native -DLLAMA_USE_PREBUILT_UI=OFF \
    && cmake --build build -j 16 --target llama-server) || exit 1
}

start_server () {
  pkill -f llama-server; sleep 2
  "$LL/build/bin/llama-server" -m "$(gguf)" --jinja -ngl 99 -c $CTX -np 1 --cache-ram 0 --port 8080 > /tmp/server_qt05.log 2>&1 9>&- &
  for i in $(seq 1 240); do curl -s localhost:8080/health | grep -q '"ok"' && return 0; sleep 2; done
  echo "server did not start — last log lines:"; tail -30 /tmp/server_qt05.log; return 1
}

template_check () {   # pilot check (1) and the first half of (2): llama.cpp's render against the reference render
  python3 - "$OUT/chat_template.jinja" <<'PY'
import json, sys, urllib.request
from jinja2 import nodes
from jinja2.ext import Extension
from jinja2.sandbox import ImmutableSandboxedEnvironment

class Generation(Extension):          # transformers' {% generation %}: renders its body unchanged
    tags = {"generation"}
    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(("name:endgeneration",), drop_needle=True)
        return nodes.CallBlock(self.call_method("_r", []), [], [], body).set_lineno(lineno)
    def _r(self, caller):
        return caller()

def raise_exception(m):
    raise ValueError(m)

tools = [{"type": "function", "function": {"name": "find_date", "description": "Find a date",
          "parameters": {"type": "object", "properties": {"day": {"type": "string"}}, "required": ["day"]}}}]
def conv(args_as_string):
    a = {"day": "السبت"}
    return [{"role": "system", "content": "أنت موظف استقبال في عيادة."},
            {"role": "user", "content": "أبي موعد يوم السبت"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "c1", "type": "function", "function": {
                "name": "find_date", "arguments": json.dumps(a, ensure_ascii=False) if args_as_string else a}}]},
            {"role": "tool", "tool_call_id": "c1", "content": "2026-11-28"},
            {"role": "assistant", "content": "موعدك يوم السبت 28 نوفمبر."},
            {"role": "user", "content": "شكرًا"}]

env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True, extensions=[Generation, "jinja2.ext.loopcontrols"])
env.filters["tojson"] = lambda x, ensure_ascii=False, indent=None, separators=None, sort_keys=False: json.dumps(
    x, ensure_ascii=ensure_ascii, indent=indent, separators=separators, sort_keys=sort_keys)
env.globals.update(raise_exception=raise_exception)
ref = env.from_string(open(sys.argv[1], encoding="utf-8").read()).render(
    messages=conv(False), tools=tools, add_generation_prompt=True, reasoning_effort="none", bos_token="", eos_token="")
# llama.cpp gets the OpenAI form (arguments as a JSON string), as run_v2.py sends it
body = {"messages": conv(True), "tools": tools, "add_generation_prompt": True, "chat_template_kwargs": {"reasoning_effort": "none"}}
req = urllib.request.Request("http://localhost:8080/apply-template", json.dumps(body).encode(), {"Content-Type": "application/json"})
try:
    got = json.load(urllib.request.urlopen(req, timeout=60))["prompt"]
except Exception as e:
    print(f"TEMPLATE CHECK: llama.cpp could not render (arguments sent as a JSON string): {e} · STOP"); sys.exit(1)
if got == ref:
    print(f"TEMPLATE CHECK: llama.cpp render = reference render ({len(ref)} chars), generation block and arguments as an object OK · OK")
else:
    i = next((k for k in range(min(len(got), len(ref))) if got[k] != ref[k]), min(len(got), len(ref)))
    print(f"TEMPLATE CHECK: renders differ at char {i}: llama.cpp {got[max(0,i-60):i+80]!r} | reference {ref[max(0,i-60):i+80]!r} · STOP")
    sys.exit(1)
print("effort line: " + next((l for l in ref.split("<|end_message|>") if "Thinking effort level" in l), "(none)"))
PY
}

pilot_check () {   # $1 runs.jsonl — the limits in the pre-registration
  python3 - "$1" <<'PY'
import json, sys
R = [json.loads(l) for l in open(sys.argv[1])]
st = [s for r in R if 'steps' in r for s in r['steps']]
bad = sum(1 for s in st if s.get('parsed') is False)
reason = sum(1 for s in st if (s.get('reasoning') or '').strip())
calls = sum(len(s.get('calls') or []) for s in st)
after_call = sum(1 for s in st if (s.get('step') or 0) > 0)    # a request whose history holds an earlier tool call
err = sum('error' in r for r in R); ctx = sum(r.get('flags', {}).get('context', False) for r in R)
p0 = (R[0]['steps'][0].get('prompt_n') or 0) + (R[0]['steps'][0].get('cached_n') or 0) if R and R[0].get('steps') else 0
ok = err == 0 and ctx == 0 and st and bad / len(st) <= 0.10 and p0 >= 1000
print(f"PILOT CHECK {sys.argv[1].split('/')[-2]}: runs {len(R)} · errors {err} · context overflows {ctx} · steps {len(st)} · "
      f"not parsed {bad} ({100*bad/max(len(st),1):.0f}%) · tool calls {calls} · requests after a call {after_call} · "
      f"steps with reasoning {reason} · first prompt tokens {p0} · {'OK' if ok else 'STOP'}")
PY
}

save () { tar czf qt05_results.tar.gz.tmp "$OUT" && mv qt05_results.tar.gz.tmp qt05_results.tar.gz && echo "saved: qt05_results.tar.gz"; }

run_part () {   # $1 label  $2 mode  $3 arm  $4 split  $5 reps  $6 safety
  python3 scripts/run_v2.py --label "$1" --mode "$2" $SAMP --split "$4" --arms "$3" --efforts $EFF \
      --reps "$5" --safety-reps "$6" --n-predict $NPRED --out-root "$OUT" || return 1
  python3 scripts/score_v2.py "$OUT/$1" | tee "$OUT/$1/scorecard.txt"
}

case "${1:-}" in
setup)
  build
  command -v hf >/dev/null || pip install -q -U huggingface_hub
  mkdir -p models/gpu/qt05 "$OUT"; df -h . | tail -1
  [ -n "$(gguf)" ] || hf download "$GREPO" --include "*IQ4_NL*.gguf" --local-dir models/gpu/qt05 >/dev/null \
    || { echo "DOWNLOAD FAILED: $GREPO IQ4_NL"; exit 1; }
  [ -n "$(gguf)" ] || { echo "STOP: no IQ4_NL GGUF in $GREPO"; exit 1; }
  hf download "$MREPO" chat_template.jinja LICENSE --revision "$MREV" --local-dir "$OUT/ref" >/dev/null \
    || { echo "DOWNLOAD FAILED: $MREPO@$MREV chat_template.jinja"; exit 1; }
  cp "$OUT/ref/chat_template.jinja" "$OUT/chat_template.jinja"
  GREV=$(python3 -c "from huggingface_hub import HfApi; print(HfApi().model_info('$GREPO').sha)")
  { echo "llama.cpp $(cd "$LL" && git rev-parse HEAD)"; echo "repo commit $(git rev-parse --short HEAD)";
    echo "gguf repo $GREPO@$GREV"; echo "model repo $MREPO@$MREV";
    (cd models/gpu/qt05 && sha256sum "$(basename "$(gguf)")"); } > "$OUT/model_provenance.txt"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | tee "$OUT/gpu.txt"
  start_server || { echo "STOP: the server does not load the model (inkling2_loop support in this llama.cpp?)"; exit 1; }
  grep -E "general.architecture|n_ctx_train|model params|model size|general.base_model|general.source" /tmp/server_qt05.log \
    | sed 's/^[^:]*: *//' | sort -u | tee "$OUT/gguf_metadata.txt"
  nvidia-smi --query-gpu=memory.used --format=csv,noheader | sed 's/^/GPU memory with the model loaded: /' | tee -a "$OUT/gguf_metadata.txt"
  template_check | tee "$OUT/template_check.txt"
  grep -q " OK$" "$OUT/template_check.txt" || { pkill -f llama-server; echo "STOP: template check not OK — amendment first"; exit 1; }
  pkill -f llama-server
  python3 scripts/test_v2.py || exit 1
  cat "$OUT/model_provenance.txt"
  echo "SETUP OK — share these lines (they go into the trial file by amendment), then:"
  echo "  setsid nohup bash scripts/run_qt05.sh pilot > qt05_pilot.log 2>&1 < /dev/null &"
  ;;
pilot)
  grep -q " OK$" "$OUT/template_check.txt" 2>/dev/null || { echo "STOP: run setup first"; exit 1; }
  for row in "${PARTS[@]}"; do
    read -r label mode arm <<< "$row"
    start_server || exit 1
    run_part "pilot-$label" "$mode" "$arm" dev 1 0 > /dev/null
    pilot_check "$OUT/pilot-$label/runs.jsonl"
  done
  pkill -f llama-server
  echo "PILOT DONE — share the four PILOT CHECK lines before running 'test'."
  ;;
test)
  for row in "${PARTS[@]}"; do
    read -r label mode arm <<< "$row"
    pilot_check "$OUT/pilot-$label/runs.jsonl" | grep -q " OK$" || { echo "STOP: $label pilot not OK — amendment first"; exit 1; }
  done
  for row in "${PARTS[@]}"; do
    read -r label mode arm <<< "$row"
    [ -f "$OUT/$label/scorecard.txt" ] && { echo "skip $label (done)"; continue; }
    rm -rf "$OUT/$label"
    start_server || exit 1
    run_part "$label" "$mode" "$arm" test 3 2 || exit 1
    save
  done
  pkill -f llama-server
  echo "TEST DONE — next: bash scripts/run_qt05.sh pack"
  ;;
pack)
  save && ls -la qt05_results.tar.gz
  echo "Download qt05_results.tar.gz from JupyterLab (right-click > Download), then STOP the pod."
  ;;
*) echo "usage: bash scripts/run_qt05.sh {setup|pilot|test|pack}"; exit 2 ;;
esac
