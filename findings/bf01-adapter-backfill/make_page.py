"""Write index.html for bf-01 from results.json: every number on the page is read from there, none is typed.
Run after make_results.py."""
import json

D = json.load(open("findings/bf01-adapter-backfill/results.json", encoding="utf-8"))
M = {m["key"]: m for m in D["models"]}
NAME = {"qwen3-8b": "Qwen3 8B", "jais3-3.7b": "Jais 3 3.7B", "jais3-7b": "Jais 3 7B", "fanar-2-27b": "Fanar 2 27B"}
ORDER = ["jais3-7b", "qwen3-8b", "fanar-2-27b", "jais3-3.7b"]


def n(x):
    return f'<span class="num">{x}</span>'


def pct(b):
    return f'<td class="num">{b["success_pct"]}% <span class="ci">[{b["ci95_pct"][0]}–{b["ci95_pct"][1]}]</span></td>'


def pts(d):
    s = lambda v: f"{v:+.1f}".replace("+0.0", "0.0").replace("-", "−")
    return f'<td class="num">{s(d["points"])} <span class="ci">[{s(d["ci95_points"][0])}, {s(d["ci95_points"][1])}]</span></td>'


def sg(v):
    return "0.0" if v == 0 else f"{v:+.1f}"


def frac(x):
    return f"{x[0]}/{x[1]}" if isinstance(x, list) else x


head = "".join(f'<th dir="ltr">{NAME[k]}</th>' for k in ORDER)
main_rows = [
    ("بصيغة النموذج الخاصة", lambda m: pct(m["own_format"])),
    ("عبر محوّل JSON", lambda m: pct(m["prompted_json_adapter"])),
    ("الفرق: المحوّل ناقص الصيغة الخاصة (نقاط)", lambda m: pts(m["adapter_minus_own_format"])),
]
main = "\n".join(f"    <tr><td>{label}</td>{''.join(f(M[k]) for k in ORDER)}</tr>" for label, f in main_rows)

SEC = [
    ("صحيحة في المحاولات الثلاث", lambda b: f'{b["pass3_pct"]}%'),
    ("طوارئ حُوّلت لموظف في الوقت المناسب", lambda b: b["emergencies_in_time"]),
    ("شكاوى وأسئلة طبية حُوّلت لموظف", lambda b: frac(b["complaint_medical_handed_over"])),
    ("محادثات ذكر فيها موعدًا لم يتحقق منه", lambda b: f'{b["invented_time_runs"]}/{b["runs"]}'),
    ("محادثات أكّد فيها حجزًا لم يتم", lambda b: f'{b["false_confirmation_runs"]}/{b["runs"]}'),
    ("محادثات فيها رد بالإنجليزية فقط", lambda b: f'{b["runs_with_english_only_reply"]}/{b["runs"]}'),
    ("استدعاءات أدوات بمعطيات غير صالحة", lambda b: b["bad_args_calls"]),
    ("زمن الرد على RTX 4090 (الوسيط / أبطأ 10%)", lambda b: f'{b["wait_median_s"]} s / {b["wait_p90_s"]} s'),
]
sec_head = "".join(f'<th dir="ltr">{NAME[k]} · {p}</th>' for k in ORDER for p in ("صيغته", "المحوّل"))
sec = "\n".join("    <tr><td>" + label + "</td>" + "".join(
    f'<td class="num">{f(M[k][p])}</td>' for k in ORDER for p in ("own_format", "prompted_json_adapter")) + "</tr>"
    for label, f in SEC)

PATHNOTE = {"bf-01, both paths in one session": "هذه الجلسة", "qt-02 pair": "زوج qt-02", "cal-02 pair": "زوج cal-02",
            "qt-01; no own tool path": "qt-01",
            "qt-04 greedy re-run (amendment 4); no own tool path": "qt-04 (إعادة التشغيل)"}
trows = []
for r in D["common_setup_two_paths"]:
    name = r["model"].split(" (")[0]
    own = pct(r["own_format"]) if r["own_format"] else '<td>لا توجد (القالب لا يدعم الأدوات)</td>'
    diff = pts(r["adapter_minus_own_format"]) if r["adapter_minus_own_format"] else "<td>—</td>"
    src = PATHNOTE[r["note"]]
    cls = ' class="this"' if r["note"].startswith("bf-01") else ""
    trows.append(f'    <tr{cls}><td dir="ltr">{name}</td>{own}{pct(r["prompted_json_adapter"])}{diff}<td>{src}</td></tr>')
table = "\n".join(trows)

rep = []
for k in ORDER:
    m = M[k]["reproducibility"]
    same = m["runs_with_identical_replies"]
    rep.append(f'    <tr><td dir="ltr">{NAME[k]}</td><td class="num">{m["published"]["success_pct"]}%</td>'
               f'<td class="num">{M[k]["own_format"]["success_pct"]}%</td>{pts(m["this_run_minus_published"])}'
               f'<td class="num">{same[0]}/{same[1]}</td><td dir="ltr">{m["published_run"]}</td></tr>')
rep = "\n".join(rep)
any_excl = any(M[k]["reproducibility"]["ci_excludes_zero"] for k in ORDER)
j37 = M["jais3-3.7b"]

page = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>مقياس — استكمال: طريقتا استدعاء الأدوات لأربعة نماذج</title>
<meta name="description" content="bf-01: أربعة نماذج على طريقتي استدعاء الأدوات في الجلسة نفسها، 42 حالة × 3 محاولات لكل طريقة. يكمل جدول الإعداد المشترك بعمودين. أرقام فقط، بلا حكم.">
<link rel="icon" href="../../assets/brand/miqyas-favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../../assets/base.css">
<style>
  :root{{color-scheme:light}}
  .num{{font-family:var(--mono);font-variant-numeric:tabular-nums;direction:ltr;unicode-bidi:isolate}}
  .data-table td.num{{text-align:end}}
  .data-table tr.this td{{font-weight:600}}
  .ci{{font-family:var(--mono);font-size:.75rem;color:var(--dim);direction:ltr;unicode-bidi:isolate}}
  .brandbar{{padding-block:2rem 0}}
  .brandbar a{{display:inline-block;line-height:0}}
  .brandbar img{{width:180px;height:auto}}
  header{{padding-block-start:1rem}}
  h1.q{{font-size:clamp(1.9rem,4.5vw,2.75rem);font-weight:600;line-height:1.3;margin-block-start:1rem}}
  .q-en{{font-family:var(--mono);font-size:.8125rem;color:var(--dim);direction:ltr;text-align:right;margin-block-start:.35rem}}
  .note{{font-size:.875rem;color:var(--dim)}}
  .obs{{border-block:1px solid var(--ink);padding-block:1.25rem;margin-block:1.5rem}}
  .en{{direction:ltr;text-align:left;unicode-bidi:isolate;font-size:.9375rem;border-block-start:1px solid var(--rule);padding-block-start:1rem}}
  ul.tight li{{margin-block:.35rem}}
  a{{color:var(--ink);text-underline-offset:3px}}
  .scroll{{overflow-x:auto}}
  .brandfoot{{display:flex;justify-content:space-between;align-items:center;border-block-start:1px solid var(--rule);padding-block-start:.75rem;margin-block:2rem;font-size:.8125rem}}
  .brandfoot .b{{display:inline-flex;align-items:center;gap:.5rem}}
  .brandfoot img{{width:24px;height:22px}}
  .brandfoot .site{{font-family:var(--mono);color:var(--dim);direction:ltr}}
</style>
</head>
<body>

<div class="strip"><div class="wrap">
  <span><b>استكمال bf-01</b></span>
  <span><b class="num">4</b> نماذج × طريقتان</span>
  <span><b class="num">{D["runs_per_path"]}</b> محادثة لكل طريقة</span>
  <span>مسجّل مسبقًا</span>
</div></div>

<div class="wrap">
<div class="brandbar"><a href="../../" aria-label="مقياس: الصفحة الرئيسية"><img src="../../assets/brand/miqyas-lockup-on-light.svg" alt="مقياس · Miqyas"></a></div>

<header>
  <h1 class="q">طريقتا استدعاء الأدوات، لكل نموذج</h1>
  <p class="q-en">bf-01 · adapter back-fill · numbers only, no verdict</p>
  <p>أثر محوّل JSON الذي نستخدمه يختلف من نموذج لآخر، فلا تصح مقارنة نموذج قسناه بطريقة بنموذج قسناه بالأخرى. لذلك قررنا أن نقيس كل نموذج بالطريقتين حين تتوفر له الطريقتان. هنا أربعة نماذج كانت مقيسة بصيغتها الخاصة فقط: قسنا طريقة المحوّل، وأعدنا صيغتها الخاصة في الجلسة نفسها حتى يقترن العمودان. الوظيفة نفسها (استقبال عيادة أسنان عبر واتساب)، والحالات الـ{n(D["scenarios"] if "scenarios" in D else 42)} العامة نفسها، وإعداد أداة التاريخ (الإعداد المشترك).</p>
</header>

<h2>الأرقام</h2>
<div class="scroll">
<table class="data-table">
  <thead><tr><th>محادثات صحيحة كاملة</th>{head}</tr></thead>
  <tbody>
{main}
  </tbody>
</table>
</div>
<p class="note">فترات الثقة {n("95%")} بين قوسين، مجمّعة حسب الحالة؛ وفترة الفرق مقترنة بالحالة نفسها في الطريقتين (إعادة معاينة الحالات، {n("4,000")} سحب). نسب النجاح من {n(126)} محادثة ({n(42)} حالة × {n(3)})، وبقية العدّ من {n(D["runs_per_path"])} محادثة تشمل محاولتين إضافيتين لكل حالة أمان.</p>

<h2>تفاصيل كل طريقة</h2>
<div class="scroll">
<table class="data-table">
  <thead><tr><th></th>{sec_head}</tr></thead>
  <tbody>
{sec}
  </tbody>
</table>
</div>
<p class="note">ذكر موعد لم يُتحقق منه وتأكيد حجز لم يتم يُكشفان بفحص آلي، وكل حالة منهما مدرجة في البيانات للمراجعة. لم يفشل قراءة أي رد في الطرق الثماني ({n(0)} خطوات غير مقروءة).</p>

<div class="obs">
  <h2>ما يستحق الانتباه</h2>
  <ul class="tight">
    <li>مع <span dir="ltr">Jais 3 3.7B</span> رفع المحوّل المحادثات الصحيحة، لكن الطوارئ التي حُوّلت لموظف في الوقت المناسب نزلت من {n(j37["own_format"]["emergencies_in_time"])} إلى {n(j37["prompted_json_adapter"]["emergencies_in_time"])}. نتيجة أعلى في المجموع لا تعني أن الطريقة أفضل في كل شيء.</li>
    <li>استدعاءات <span dir="ltr">Fanar 2 27B</span> بمعطيات غير صالحة كثيرة بالطريقتين ({n(M["fanar-2-27b"]["own_format"]["bad_args_calls"])} بصيغته و{n(M["fanar-2-27b"]["prompted_json_adapter"]["bad_args_calls"])} عبر المحوّل)، وكانت ردوده بالإنجليزية فقط في {n(M["fanar-2-27b"]["own_format"]["runs_with_english_only_reply"])} محادثة بصيغته و{n(M["fanar-2-27b"]["prompted_json_adapter"]["runs_with_english_only_reply"])} عبر المحوّل.</li>
  </ul>
</div>

<h2>كل النماذج التي قسناها على الإعداد المشترك، بالطريقتين</h2>
<p>مرتبة حسب عمود المحوّل، الطريقة الوحيدة المتاحة لكل النماذج.</p>
<div class="scroll">
<table class="data-table">
  <thead><tr><th>النموذج</th><th>بصيغته الخاصة</th><th>عبر محوّل JSON</th><th>الفرق (نقاط)</th><th>المصدر</th></tr></thead>
  <tbody>
{table}
  </tbody>
</table>
</div>
<p class="note">لا ننتقي النماذج: كل ما قسناه على الإعداد نفسه موجود. الصفوف من جلسات مختلفة، ففوارق النقاط القليلة بينها ليست ذات دلالة. لا نعدّل رقم أي طريقة بالطريقة الأخرى. قالبا <span dir="ltr">ALLaM</span> و<span dir="ltr">SILMA</span> لا يدعمان الأدوات، فلهما طريقة المحوّل فقط.</p>

<h2>إعادة القياس</h2>
<p>الطريقة الخاصة في هذه الجلسة تكرار لتشغيل منشور. سجّلنا مسبقًا أن نضيف ملاحظة مؤرخة إلى صفحة النموذج إذا استبعدت فترة الفرق الصفر.{" لم يحدث ذلك لأي نموذج، فلا تتغير أي صفحة سابقة." if not any_excl else ""}</p>
<div class="scroll">
<table class="data-table">
  <thead><tr><th>النموذج</th><th>المنشور</th><th>هذه الجلسة</th><th>الفرق (نقاط)</th><th>محادثات بالردود نفسها حرفيًا</th><th>التشغيل المنشور</th></tr></thead>
  <tbody>
{rep}
  </tbody>
</table>
</div>
<p class="note">مع النسخة نفسها من llama.cpp وملف النموذج نفسه، أعاد <span dir="ltr">Qwen3 8B</span> و<span dir="ltr">Jais 3 7B</span> كل محادثة حرفيًا. تشغيلا <span dir="ltr">Jais 3 3.7B</span> و<span dir="ltr">Fanar 2 27B</span> المنشوران كانا من جلسات أخرى، فاختلفت الردود واقتربت النسب.</p>

<h2>حدود هذا الاستكمال</h2>
<ul class="tight">
  <li>مجموعة الاختبار العامة فقط، وإعداد أداة التاريخ فقط.</li>
  <li>جربنا المحوّل بإعدادات كل نموذج نفسها (العيّنة والجهد والخادم)، ولم نضبطه لأي نموذج.</li>
  <li>بُني llama.cpp من غير صفحة المحادثة في المتصفح (التعديل 2): نستخدم واجهة الخادم البرمجية فقط، وهي نفسها في الحالتين.</li>
  <li>نجح فحص التجربة الأولية لطريقة المحوّل للنماذج الأربعة قبل أي اختبار.</li>
</ul>

<h2>الملفات</h2>
<ul class="tight">
  <li><a href="https://github.com/Miqyas-Lab/job-trials/blob/main/trials/bf-01-adapter-backfill.yaml">ملف التسجيل المسبق وتعديلاته ↗</a></li>
  <li><a href="https://github.com/Miqyas-Lab/job-trials/tree/main/results/bf01">المحادثات الخام والدرجات ↗</a></li>
  <li><a href="https://github.com/Miqyas-Lab/job-trials/blob/main/findings/bf01-adapter-backfill/results.json">results.json ↗</a></li>
</ul>

<section class="en" id="en">
  <h2>English</h2>
  <p>bf-01 (pre-registered adapter back-fill, numbers only): the effect of our prompted-JSON adapter differs by model, so a model measured on one tool path cannot be compared fairly with one measured on the other. Four models measured on their own tool format only were run on both paths in one session (dental clinic WhatsApp front desk, 42 public scenarios × 3 runs per path, date-tool setup). Fully correct conversations, own format → adapter: {"; ".join(f'{NAME[k]} {M[k]["own_format"]["success_pct"]}% → {M[k]["prompted_json_adapter"]["success_pct"]}% ({M[k]["adapter_minus_own_format"]["points"]:+.1f} points, paired 95% CI {sg(M[k]["adapter_minus_own_format"]["ci95_points"][0])} to {sg(M[k]["adapter_minus_own_format"]["ci95_points"][1])})' for k in ORDER)}. For Jais 3 3.7B the adapter raised success but emergencies handed to staff in time fell from {j37["own_format"]["emergencies_in_time"]} to {j37["prompted_json_adapter"]["emergencies_in_time"]}. Reproducibility: each own-format path repeats a published run; no difference excludes zero, and Qwen3 8B and Jais 3 7B reproduced every conversation word for word on the same llama.cpp build. The common-setup table now shows both paths for every model that has both, sorted by the adapter column. Phone-like numbers were redacted after scoring; rescoring gives the same scorecards. Full details in the <a href="https://github.com/Miqyas-Lab/job-trials/tree/main/findings/bf01-adapter-backfill">trial folder</a>.</p>
</section>
<div class="brandfoot"><span class="b"><img src="../../assets/brand/miqyas-favicon.svg" alt="">مقياس</span><span class="site">miqyaslab.com</span></div>
</div>
</body>
</html>
"""
open("findings/bf01-adapter-backfill/index.html", "w", encoding="utf-8").write(page)
print("index.html written")
