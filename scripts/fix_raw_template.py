"""qt-03 amendment 1: llama.cpp's Jinja engine has no {% raw %} statement. A raw block only prints its contents
literally, so each one is replaced by an equivalent string expression. The converted template is used only if it
renders byte-identical to the original (Python jinja2, HF settings) on test conversations: no tools / tools,
tool call + tool result, thinking on / off, with and without a generation prompt.
usage: python3 scripts/fix_raw_template.py <chat_template.jinja> <out.jinja>"""
import json, re, sys, datetime
sys.path.insert(0, "scripts")
from jinja2.sandbox import ImmutableSandboxedEnvironment
from jinja2.ext import loopcontrols

src = open(sys.argv[1], encoding="utf-8").read()
RAW = re.compile(r"\{%(-?)\s*raw\s*(-?)%\}(.*?)\{%(-?)\s*endraw\s*(-?)%\}", re.S)

def rep(m):
    lstrip_before, strip_start, body, strip_end, rstrip_after = m.groups()
    if strip_start: body = body.lstrip()
    if strip_end: body = body.rstrip()
    return ("{{-" if lstrip_before else "{{") + " " + json.dumps(body, ensure_ascii=False) + " " + ("-}}" if rstrip_after else "}}")

out, n = RAW.subn(rep, src)
print(f"raw blocks replaced: {n}")

def env():
    e = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True, extensions=[loopcontrols])
    e.filters["tojson"] = lambda x, indent=None, separators=None, sort_keys=False, ensure_ascii=False: json.dumps(
        x, indent=indent, separators=separators, sort_keys=sort_keys, ensure_ascii=ensure_ascii)
    def raise_exception(msg): raise ValueError(msg)
    e.globals.update(raise_exception=raise_exception, strftime_now=lambda f: datetime.datetime(2026, 11, 5).strftime(f))
    return e

from clinic import system_prompt, tools_for
tools = tools_for("tool")
call = {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "id": "c1",
        "function": {"name": tools[0]["function"]["name"], "arguments": {"date": "2026-11-10"}}}]}
convs = [
    [{"role": "system", "content": system_prompt("tool")}, {"role": "user", "content": "مرحبا، أبي موعد"}],
    [{"role": "system", "content": system_prompt("tool")}, {"role": "user", "content": "أبي تنظيف عقب باجر"}, call,
     {"role": "tool", "tool_call_id": "c1", "content": json.dumps({"ok": True}, ensure_ascii=False)},
     {"role": "assistant", "content": "تمام"}, {"role": "user", "content": "شكرا"}],
    [{"role": "user", "content": "ما هي عاصمة قطر؟"}],
]
a, b = env().from_string(src), env().from_string(out)
checked = 0
for msgs in convs:
    for tl in (None, tools):
        for nt in (True, False):
            for gp in (True, False):
                kw = dict(messages=msgs, add_generation_prompt=gp, no_thinking=nt, enable_thinking=not nt,
                          bos_token="<bos>", eos_token="<eos>")
                if tl: kw["tools"] = tl
                def r(t):
                    try: return t.render(**kw)
                    except Exception as ex: return f"EXC {type(ex).__name__}: {ex}"
                ra, rb = r(a), r(b)
                if ra != rb:
                    print("MISMATCH", {"tools": bool(tl), "no_thinking": nt, "gen_prompt": gp}); sys.exit(1)
                checked += 1
print(f"IDENTICAL on {checked}/{checked} renders")
if "raw" in re.findall(r"\{%-?\s*(\w+)", out): print("STOP: a raw statement is left"); sys.exit(1)
open(sys.argv[2], "w", encoding="utf-8").write(out)
print(f"wrote {sys.argv[2]}")
