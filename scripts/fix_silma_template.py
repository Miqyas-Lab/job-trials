"""qt-04 amendment 2: make SILMA's chat template keep the system prompt under llama.cpp's template engine.

SILMA's template stores the system prompt in a variable set inside an if block and prints it later
({% set system_message = ... %} ... {% if system_message is defined %}). llama.cpp's engine dropped it: the DEV pilot's
first prompt was 13 tokens, without the instructions or tools. This script writes a template that prints the system
prompt directly, and checks with the reference engine (Jinja2) that it renders exactly the same text as the original on
every test conversation, including the adapter's multi-turn shape. Usage:
    python3 scripts/fix_silma_template.py models/hf/silma-9b/tokenizer_config.json results/qt04/chat_template_llamacpp.jinja
"""
import json
import re
import sys

from jinja2.sandbox import ImmutableSandboxedEnvironment

ORIGINAL = (r"{% if messages[0]['role'] == 'system' %}{% set system_message = messages[0]['content'] %}{% endif %}"
            r"{% if system_message is defined %}{{ system_message }}{% endif %}")
FIXED = "{% if messages[0]['role'] == 'system' %}{{ messages[0]['content'] }}{% endif %}"

CONVERSATIONS = [
    [{"role": "system", "content": "تعليمات العيادة\nTOOLS: [...]"}, {"role": "user", "content": "مرحبا"}],
    [{"role": "system", "content": "S"}, {"role": "user", "content": "أبي موعد"},
     {"role": "assistant", "content": '{"tool_calls": [{"name": "find_slots", "arguments": {"day": "sat"}}]}'},
     {"role": "user", "content": "TOOL RESULT find_slots: [\"10:00\"]"},
     {"role": "assistant", "content": '{"response": "عندنا الساعة 10"}'}, {"role": "user", "content": "تمام"}],
    [{"role": "user", "content": "بدون تعليمات نظام"}],
]


def render(t, msgs, gen):
    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    env.globals["raise_exception"] = lambda m: (_ for _ in ()).throw(ValueError(m))
    return env.from_string(t).render(messages=msgs, add_generation_prompt=gen, bos_token="<bos>", eos_token="<eos>")


def main(src, dst):
    original = json.load(open(src, encoding="utf-8"))["chat_template"]
    if original.count(ORIGINAL) != 1:
        print("STOP: the template does not contain the expected system-prompt block; nothing written")
        return 1
    fixed = original.replace(ORIGINAL, FIXED)
    for msgs in CONVERSATIONS:
        for gen in (True, False):
            a, b = render(original, msgs, gen), render(fixed, msgs, gen)
            if a != b:
                print("STOP: the fixed template renders differently from the original; nothing written")
                return 1
    if "تعليمات العيادة" not in render(fixed, CONVERSATIONS[0], True):
        print("STOP: the system prompt is not in the rendered text")
        return 1
    open(dst, "w", encoding="utf-8").write(fixed)
    open(dst.replace("_llamacpp", "_original"), "w", encoding="utf-8").write(original)
    print(f"template fixed: identical to the original on {len(CONVERSATIONS) * 2} renders; written to {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
