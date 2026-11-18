"""Build index.html and scorecard_x_source.html for Job Trial #2 stage 1 from results.json.
Numbers in tables and prose come from results.json; the Arabic prose is written here and reviewed by the founder."""
import json

D = json.load(open("findings/jt02-riyadh-stage1/results.json", encoding="utf-8"))
P = D["paths"]
by = {(e["key"], e["path"]): e for e in P}
PATH_AR = {"jais": "صيغته", "chat": "صيغته", "template": "صيغته", "prompted": "محوّل JSON"}
SUB = {"jais3-7b": "أقل جهد", "jais3-3.7b": "أقل جهد", "qwen3-8b": "بلا تفكير", "qwen3-4b": "بلا تفكير",
       "fanar-2-27b": "بلا تفكير", "falcon-h1-7b": "", "allam-7b": "", "silma-9b": ""}


def n(x):
    return f'<span class="num">{x}</span>'


def pct(x, d=1):
    return "—" if x is None else (f"{x:.{d}f}%" if d else f"{round(x)}%")


def ci(c):
    return "" if not c else f' <span class="ci">[{c[0]}–{c[1]}]</span>'


rank = D["stage2_selection"]["ranking"]
best = [by[(next(e["key"] for e in P if e["model"] == r["model"]), r["path"])] for r in rank]
first, second, third = best[0], best[1], best[2]
pub_lead = max(-e["private_minus_public_tool_points"] for e in P)
lead_e = max(P, key=lambda e: -e["private_minus_public_tool_points"])
table_wins = [e for e in P if e["private"]["table"]["success_pct"] > e["private"]["tool"]["success_pct"]]
allam = by[("allam-7b", "prompted")]
T = lambda e, s="private", a="tool", k="success_pct": e[s][a][k]

# ---------- main table: every path, common setup ----------
rows = []
for e in sorted(P, key=lambda e: -T(e)):
    dub = e["dubai_common_setup"]
    rows.append(
        f'<tr{" class=\"this\"" if e in best[:2] else ""}><td dir="ltr">{e["model"]}</td><td>{PATH_AR[e["path"]]}</td>'
        f'<td class="num">{pct(T(e))}{ci(e["private"]["tool"]["ci95_pct"])}</td>'
        f'<td class="num">{pct(T(e, "public"))}{ci(e["public"]["tool"]["ci95_pct"])}</td>'
        f'<td class="num">{e["private"]["tool"]["emergencies_in_time"]} · {e["public"]["tool"]["emergencies_in_time"]}</td>'
        f'<td class="num">{e["private"]["tool"]["complaint_medical_handed_over"]} · {e["public"]["tool"]["complaint_medical_handed_over"]}</td>'
        f'<td class="num">{e["private"]["tool"]["critical_total"]} · {e["public"]["tool"]["critical_total"]}</td>'
        f'<td class="num">{pct(dub.get("success_pct"))}</td></tr>')
MAIN = "\n    ".join(rows)

# ---------- three setups ----------
rows3 = []
for e in sorted(P, key=lambda e: -T(e)):
    c = lambda s, a: f'<td class="num">{pct(T(e, s, a))}</td>'
    rows3.append(f'<tr><td dir="ltr">{e["model"]}</td><td>{PATH_AR[e["path"]]}</td>' + c("private", "base") + c("private", "table")
                 + c("private", "tool") + c("public", "base") + c("public", "table") + c("public", "tool") + "</tr>")
SETUPS = "\n    ".join(rows3)

# ---------- ranking ----------
rk = []
for r in rank:
    rk.append(f'<tr{" class=\"this\"" if r["rank"] <= 2 else ""}><td class="num">{r["rank"]}</td><td dir="ltr">{r["model"]}</td>'
              f'<td>{PATH_AR[r["path"]]}</td><td class="num">{pct(r["private_tool_pct"])}</td><td class="num">{pct(r["public_tool_pct"])}</td>'
              f'<td class="num">{r["private_tool_critical"]}</td></tr>')
RANK = "\n    ".join(rk)

# ---------- reply times (tool setup, median / p90) ----------
rt = []
for e in sorted(P, key=lambda e: e["public"]["tool"]["wait_median_p90_s"][0]):
    w1, w2 = e["public"]["tool"]["wait_median_p90_s"], e["private"]["tool"]["wait_median_p90_s"]
    rt.append(f'<tr><td dir="ltr">{e["model"]}</td><td>{PATH_AR[e["path"]]}</td><td class="num">{w1[0]} s / {w1[1]} s</td>'
              f'<td class="num">{w2[0]} s / {w2[1]} s</td></tr>')
TIMES = "\n    ".join(rt)

page = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>مقياس — تجربة العمل #2، المرحلة الأولى: استقبال عيادة في الرياض</title>
<meta name="description" content="تجربة سريعة استكشافية: ثمانية نماذج مفتوحة في استقبال عيادة أسنان في الرياض، مع مرضى يكتبون بالنجدي. 42 حالة عامة و42 حالة خاصة لم تُنشر، × 3 محاولات. أرقام فقط، بلا حكم.">
<meta property="og:title" content="هل يقدر نموذج عربي مفتوح يدير استقبال عيادة في الرياض؟ · مقياس">
<meta property="og:image" content="https://miqyaslab.com/findings/jt02-riyadh-stage1/scorecard_x.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="../../assets/brand/miqyas-favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../../assets/base.css">
<style>
  :root{{color-scheme:light}}
  @media (prefers-color-scheme:dark){{:root{{--ink:#12161C;--paper:#FAF9F6;--rule:#D8D5CE;--dim:#6E7178;--soft:#EFEDE7;--surface:#fff;--signal:#C42B1F;--verify:#1B5E4A}}}}
  .num{{font-family:var(--mono);font-variant-numeric:tabular-nums;direction:ltr;unicode-bidi:isolate}}
  .data-table td.num{{text-align:end;white-space:nowrap}}
  .data-table td{{white-space:nowrap}}
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
  .en p{{font-family:var(--ar)}}
  .en{{direction:ltr;text-align:left;unicode-bidi:isolate;font-size:.9375rem;border-block-start:1px solid var(--rule);padding-block-start:1rem}}
  ul.tight li{{margin-block:.35rem}}
  a{{color:var(--ink);text-underline-offset:3px}}
  .scroll{{overflow-x:auto}}
  .brandfoot{{display:flex;justify-content:space-between;align-items:center;border-block-start:1px solid var(--rule);padding-block-start:.75rem;margin-block:2rem;font-size:.8125rem}}
  .brandfoot .b{{display:inline-flex;align-items:center;gap:.5rem}}
  .brandfoot img{{width:24px;height:22px}}
  .brandfoot .site{{font-family:var(--mono);color:var(--dim);direction:ltr}}
  img.card{{width:100%;height:auto;border:1px solid var(--rule);margin-block:1rem}}
</style>
</head>
<body>

<div class="strip"><div class="wrap">
  <span><b>تجربة سريعة · استكشافية</b></span>
  <span><b class="num">8</b> نماذج · <b class="num">14</b> طريقة</span>
  <span><b class="num">42</b> حالة عامة و<b class="num">42</b> خاصة</span>
  <span>مسجّلة مسبقًا</span>
</div></div>

<div class="wrap">
<div class="brandbar"><a href="../../" aria-label="مقياس: الصفحة الرئيسية"><img src="../../assets/brand/miqyas-lockup-on-light.svg" alt="مقياس · Miqyas"></a></div>

<header>
  <h1 class="q">هل يقدر نموذج عربي مفتوح يدير استقبال عيادة أسنان في الرياض؟</h1>
  <p class="q-en">Job Trial #2 · stage 1 · Quick Trial · exploratory · numbers only, no verdict</p>
  <p>نقلنا وظيفة <a href="../frontdesk-v2/">تجربة العمل #1</a> من دبي إلى الرياض: موظف استقبال على واتساب لعيادة أسنان، بالأدوات والقواعد وطريقة التقييم نفسها، لكن المرضى يكتبون هذه المرة باللهجة النجدية، ومواعيد العيادة مواعيد الرياض. اختبرنا ثمانية نماذج مفتوحة، كلًا منها بطريقتي استدعاء الأدوات حين تتوفر له الطريقتان، وعلى الإعدادات الثلاثة، بثلاث محاولات لكل حالة.</p>
  <p>وأضفنا لأول مرة مجموعة حالات خاصة: {n(42)} حالة كتبها متحدثان أصليان باللهجة النجدية ولم تُنشر، فلا يمكن أن يكون أي نموذج قد رآها. ننشر نتائجها درجاتٍ وفئاتٍ فقط، وتبقى رسائلها خاصة كي تبقى المجموعة صالحة للاختبار.</p>
  <p class="note">هذه المرحلة الأولى، وهي تجربة سريعة: ننشر الأرقام فقط ولا نصدر حكمًا. المرحلة الثانية تجربة عمل كاملة بأحكام لنموذجين، تختارهما قاعدة سجّلناها قبل أي نتيجة.</p>
</header>

<img class="card" src="scorecard_x.png" alt="بطاقة نتائج المرحلة الأولى من تجربة العمل #2">

<h2>الأرقام على الإعداد المشترك</h2>
<p>الإعداد المشترك: أداة التاريخ، ومن غير تفكير قبل الرد أو بأقل جهد. في كل خلية الرقم على الحالات الخاصة أولًا ثم على العامة.</p>
<div class="scroll">
<table class="data-table">
  <thead><tr><th>النموذج</th><th>الأدوات</th><th>صحيحة كاملة · خاصة</th><th>صحيحة كاملة · عامة</th><th>طوارئ وصلت لموظف</th><th>شكاوى وأسئلة طبية وصلت لموظف</th><th>محادثات فيها خطأ حرج</th><th>دبي، الطريقة نفسها</th></tr></thead>
  <tbody>
    {MAIN}
  </tbody>
</table>
</div>
<p class="note">فترات الثقة {n("95%")} بين قوسين، مجمّعة حسب الحالة ({n("4,000")} سحبة). نسب النجاح من {n(126)} محادثة لكل مجموعة ({n(42)} حالة × {n(3)})، وبقية العدّ من {n(144)} محادثة تشمل محاولتين إضافيتين لكل حالة أمان. الخطأ الحرج: موعد مخترع، أو تأكيد حجز لم يتم، أو رد بلغ حد الطول، أو حلقة، أو رسالة بلا رد؛ أي واحد منها يُفشل المحادثة. «محوّل JSON»: طريقة كتبناها لعرض الأدوات على أي نموذج؛ «صيغته»: طريقة النموذج الخاصة. عمود دبي من تجارب سابقة على حالات تجربة العمل #1، أي جلسات مختلفة؛ و«—» حيث لم نقس تلك الطريقة على حالات دبي بعد (التجربة bf-01 مسجّلة).</p>

<div class="obs">
  <h2>من ينتقل إلى المرحلة الثانية</h2>
  <p>القاعدة المسجّلة في {n("16")} نوفمبر، قبل أي نتيجة: النموذجان الأعلى نجاحًا على الحالات الخاصة في الإعداد المشترك، كلٌّ بطريقته الأفضل؛ وعند التعادل نحتكم إلى الحالات العامة، ثم إلى الأقل أخطاءً حرجة.</p>
  <div class="scroll">
  <table class="data-table">
    <thead><tr><th></th><th>النموذج</th><th>طريقته الأفضل</th><th>خاصة</th><th>عامة</th><th>أخطاء حرجة (خاصة)</th></tr></thead>
    <tbody>
    {RANK}
    </tbody>
  </table>
  </div>
  <p>ينتقل <span dir="ltr">{first["model"]}</span> و<span dir="ltr">{second["model"]}</span>، كلاهما عبر محوّل JSON. الفرق بين الثاني ({n(pct(T(second)))}) والثالث <span dir="ltr">{third["model"]}</span> ({n(pct(T(third)))}) يقع داخل فترتي الثقة، فهو ليس فرقًا واضحًا بينهما؛ طبّقنا القاعدة كما سُجّلت.</p>
</div>

<h2>الإعدادات الثلاثة</h2>
<div class="scroll">
<table class="data-table">
  <thead><tr><th>النموذج</th><th>الأدوات</th><th>خاصة: بلا مساعدة</th><th>خاصة: التقويم في التعليمات</th><th>خاصة: أداة التاريخ</th><th>عامة: بلا مساعدة</th><th>عامة: التقويم في التعليمات</th><th>عامة: أداة التاريخ</th></tr></thead>
  <tbody>
    {SETUPS}
  </tbody>
</table>
</div>
<p>على الحالات الخاصة، كان وضع التقويم داخل التعليمات أفضل من أداة التاريخ في {n(len(table_wins))} من {n(len(P))} طريقة. الإعداد المشترك يبقى أداة التاريخ لأنه المسجّل مسبقًا والمستخدم في كل تجاربنا.</p>

<div class="obs">
  <h2>الحالات العامة والخاصة</h2>
  <p>لم تتفوق أي طريقة على الحالات العامة تفوقًا كبيرًا: أكبر تقدم للعامة على الخاصة {n(pub_lead)} نقطة (<span dir="ltr">{lead_e["model"]}</span>، {PATH_AR[lead_e["path"]]}). لو كان نموذج قد رأى الحالات العامة أثناء تدريبه، لتوقعنا أن يتفوق عليها بوضوح. وجاءت الحالات الخاصة في المتوسط أسهل قليلًا من العامة. هذا لا يثبت أن أي نموذج لم يرَ الحالات العامة، لكنه لا يُظهر علامة على ذلك.</p>
</div>

<h2>ما لاحظناه في الأرقام</h2>
<ul class="tight">
  <li>محوّل JSON رفع أغلب النماذج التي لها صيغة خاصة على الحالات الخاصة: <span dir="ltr">Jais 3 7B</span> من {n(pct(T(by[("jais3-7b","jais")])))} إلى {n(pct(T(by[("jais3-7b","prompted")])))}، و<span dir="ltr">Falcon-H1 7B</span> من {n(pct(T(by[("falcon-h1-7b","template")])))} إلى {n(pct(T(by[("falcon-h1-7b","prompted")])))}، و<span dir="ltr">Fanar 2 27B</span> من {n(pct(T(by[("fanar-2-27b","template")])))} إلى {n(pct(T(by[("fanar-2-27b","prompted")])))}. الاستثناء <span dir="ltr">Qwen3 8B</span>: صيغته {n(pct(T(by[("qwen3-8b","chat")])))} والمحوّل {n(pct(T(by[("qwen3-8b","prompted")])))}.</li>
  <li><span dir="ltr">Jais 3 3.7B</span> عبر المحوّل حوّل الطوارئ إلى موظف في {n(by[("jais3-3.7b","prompted")]["private"]["tool"]["emergencies_in_time"])} فقط على الحالات الخاصة، مقابل {n(by[("jais3-3.7b","jais")]["private"]["tool"]["emergencies_in_time"])} بصيغته.</li>
  <li><span dir="ltr">ALLaM 7B</span> و<span dir="ltr">SILMA 9B</span> لم يحوّلا أي حالة طوارئ إلى موظف على الحالات الخاصة. وفي {n(allam["public_runs_with_invented_phone_redacted"])} محادثة عامة من {n(432)} كتب <span dir="ltr">ALLaM 7B</span> رقم هاتف مخترعًا؛ حذفنا كل الأرقام المخترعة من البيانات المنشورة.</li>
  <li>أرقام كل نموذج في الرياض قريبة من أرقامه في دبي على الطريقة نفسها، والفروق داخل فترات الثقة في الأغلب. الحالات والجلسات مختلفة، فهذه مقارنة تقريبية.</li>
</ul>

<h2>زمن الرد على RTX 4090 (أداة التاريخ، الوسيط / أبطأ 10%)</h2>
<div class="scroll">
<table class="data-table">
  <thead><tr><th>النموذج</th><th>الأدوات</th><th>عامة</th><th>خاصة</th></tr></thead>
  <tbody>
    {TIMES}
  </tbody>
</table>
</div>
<p class="note">جرت الحالات العامة على جهاز والخاصة على جهاز آخر من النوع نفسه (انظر <a href="#run">كيف جرى التشغيل</a>)، فالمقارنة الأدق داخل العمود الواحد.</p>

<div class="obs" id="run">
  <h2>كيف جرى التشغيل</h2>
  <p>بدأ الاختبار على جهاز RTX 4090 مستأجر في {n("16")} نوفمبر. في {n("17")} نوفمبر أنهى المزوّد الجهاز وحذف قرصه أثناء التشغيل. كانت {n(13)} طريقة على الحالات العامة قد انتهت ونُزّلت، فأبقيناها. وأعدنا من البداية ما لم يكتمل: طريقة المحوّل لـ <span dir="ltr">Fanar 2 27B</span> على العامة (لم تُحسب نتيجتها الجزئية)، والطرق الأربع عشرة كلها على الخاصة (لم يُنظر في أي شيء منها). سجّلنا ذلك تعديلًا في ملف التجربة قبل إعادة التشغيل.</p>
  <p>جرت الأجزاء المتبقية على جهاز RTX 4090 آخر، بملفات النماذج نفسها (تحققنا من بصماتها) والإعدادات نفسها. وأثناء طريقة <span dir="ltr">Fanar 2 27B</span> بصيغته على الخاصة توقف الاختبار دون رسالة خطأ؛ فأوقفنا ذاكرة الخادم المؤقتة للمحادثات السابقة وأعدنا تشغيل الخادم لكل جزء في أجزاء Fanar الثلاثة المتبقية، وأعدنا ذلك الجزء من البداية. هذه الذاكرة توفّر الوقت فقط ولا تغيّر ما يكتبه النموذج. كل ذلك في تعديلات ملف التجربة (من {n(4)} إلى {n(6)}).</p>
</div>

<h2>حدود هذه التجربة</h2>
<ul class="tight">
  <li>المرحلة الأولى أرقام فقط. المراجعة اليدوية للأخطاء الحرجة، والتدقيق الأعمى لـ {n(30)} محادثة على الأقل لكل نموذج بيد المتحدثَين النجديين، وإعادة التشغيل، وسلّم الأجهزة، كلها في المرحلة الثانية.</li>
  <li>تركنا خارج التجربة مواعيد الصلاة وما يُحسب بالنسبة لها، وهي جزء من عمل عيادة حقيقية في الرياض.</li>
  <li>كتب الحالات وراجعها متحدثان أصليان باللهجة النجدية؛ كاتب التجربة ليس متحدثًا بها. اتفق المراجعان على {n("161")} رسالة من {n("161")} في الحالات العامة.</li>
  <li>نتائج الحالات الخاصة درجات وفئات فقط؛ رسائلها ومحادثاتها الخام لا تُنشر.</li>
  <li>أربع طرق لم نقسها بعد على حالات دبي: محوّل JSON لـ <span dir="ltr">Jais 3 7B</span> و<span dir="ltr">Jais 3 3.7B</span> و<span dir="ltr">Qwen3 8B</span> و<span dir="ltr">Fanar 2 27B</span>. قياسها موضوع التجربة bf-01 المسجّلة.</li>
  <li>نماذج ALLaM وSILMA وFanar لا يوجد لها ملف GGUF رسمي، فحوّلناها بأنفسنا من أوزان مثبتة، وسجّلنا بصمة كل ملف.</li>
</ul>

<h2>الملفات</h2>
<ul class="tight">
  <li><a href="https://github.com/Miqyas-Lab/job-trials/blob/main/trials/jt-02-riyadh-clinic.yaml">ملف التسجيل المسبق وتعديلاته الستة ↗</a></li>
  <li><a href="https://github.com/Miqyas-Lab/job-trials/tree/main/results/jt02">المحادثات الخام للحالات العامة والدرجات ↗</a></li>
  <li><a href="https://github.com/Miqyas-Lab/job-trials/tree/main/results/jt02/private_scores">درجات الحالات الخاصة لكل حالة (بلا نصوص) ↗</a></li>
  <li><a href="https://github.com/Miqyas-Lab/job-trials/blob/main/findings/jt02-riyadh-stage1/results.json">results.json ↗</a></li>
</ul>

<section class="en" id="en">
  <h2>English</h2>
  <p>Job Trial #2, stage 1 (Quick Trial, exploratory, numbers only): the Job Trial #1 dental-clinic WhatsApp front desk moved to Riyadh, with patients writing in Najdi. Eight open models, both tool paths where both exist (14 paths), three setups, 3 runs per scenario, on 42 public scenarios and, for the first time, 42 private held-out scenarios written by two native Najdi speakers and never published (private results are released as per-scenario scores only). Common setup (date tool), private / public: {first["model"]} (prompted-JSON adapter) {pct(T(first))} / {pct(T(first,"public"))}; {second["model"]} (adapter) {pct(T(second))} / {pct(T(second,"public"))}; {third["model"]} (own format) {pct(T(third))} / {pct(T(third,"public"))}; ALLaM 7B {pct(T(allam))}; SILMA 9B {pct(T(by[("silma-9b","prompted")]))}. By the rule registered before any result, {first["model"]} and {second["model"]} go to stage 2 (a full Job Trial with verdicts); the second and third places are inside each other's 95% CIs. No path is much stronger on public than private (largest public lead {pub_lead} points). The calendar-in-prompt setup beat the date tool on {len(table_wins)} of {len(P)} paths on the private set. The first rented machine was ended by the provider mid-run; 13 finished public parts were kept and the rest re-run from the start on a second RTX 4090 (amendments 4-6). Prayer-relative times were left out. Full details in the <a href="https://github.com/Miqyas-Lab/job-trials/tree/main/findings/jt02-riyadh-stage1">trial folder</a>.</p>
</section>

<div class="brandfoot"><span class="b"><img src="../../assets/brand/miqyas-favicon.svg" alt="">مقياس</span><span class="site">miqyaslab.com</span></div>
</div>
</body>
</html>
"""
open("findings/jt02-riyadh-stage1/index.html", "w", encoding="utf-8").write(page)

# ---------- scorecard 1200x675: each model at its better path (private), rows by private success ----------
cr = []
for e in best:
    dub = e["dubai_common_setup"].get("success_pct")
    cls = ' class="main"' if e in best[:2] else ""
    sub = f' <span class="sub">{SUB[e["key"]]}</span>' if SUB[e["key"]] else ""
    nm = e["model"].replace(" ", " · ", 1) if e["model"].count(" ") >= 1 else e["model"]
    nm = {"Jais 3 7B": "Jais 3 · 7B", "Jais 3 3.7B": "Jais 3 · 3.7B", "Qwen3 8B": "Qwen3 · 8B", "Qwen3 4B": "Qwen3 · 4B",
          "Falcon-H1 7B": "Falcon-H1 · 7B", "ALLaM 7B": "ALLaM · 7B", "SILMA 9B": "SILMA · 9B", "Fanar 2 27B": "Fanar 2 · 27B"}[e["model"]]
    cr.append(f'<tr{cls}><td class="name">{nm}{sub}</td><td class="path">{PATH_AR[e["path"]].replace(" JSON","")}</td>'
              f'<td class="num"><span class="n">{pct(T(e))}</span></td><td class="num"><span class="n">{pct(T(e, "public"))}</span></td>'
              f'<td class="num"><span class="n">{e["private"]["tool"]["emergencies_in_time"]}</span></td>'
              f'<td class="num"><span class="n">{e["private"]["tool"]["complaint_medical_handed_over"]}</span></td>'
              f'<td class="num"><span class="n">{pct(dub)}</span></td></tr>')
CARD = "\n    ".join(cr)
card = open("findings/qt04-silma-9b/scorecard_x_source.html", encoding="utf-8").read()
head = card.split("<body>")[0].replace("qt-04 scorecard · every number from findings/qt04-silma-9b/results.json (greedy re-run headline; common_setup) · option A: common-setup table, rows chosen by setup, never by lab (standard v1.2)",
                                        "jt-02 stage 1 scorecard · generated by make_page.py from results.json · each model at its better path on the private set (the registered selection measure)")
body = f"""<body>
  <div class="head">
    <div class="strip"><b>تجربة سريعة · استكشافية</b> · تجربة العمل الثانية، المرحلة الأولى · <span class="n">42</span> حالة خاصة و<span class="n">42</span> عامة × <span class="n">3</span> · مسجّلة مسبقًا · <span class="n">llama.cpp Q4 · RTX 4090</span> · <span class="n">Nov 2026</span></div>
    <img src="../../assets/brand/miqyas-lockup-on-light.svg" alt="مقياس">
  </div>

  <h1>هل يقدر نموذج عربي مفتوح يدير استقبال عيادة <span class="model">في الرياض</span>؟</h1>
  <p class="en">Quick Trial · exploratory · numbers only, no verdict · patients write in Najdi · same setup for every model</p>

  <table style="margin-top:14px">
    <tr>
      <th>النموذج · أداة التاريخ · طريقته الأفضل</th>
      <th>الأدوات</th>
      <th class="num">صحيحة كاملة<br>حالات خاصة</th>
      <th class="num">صحيحة كاملة<br>حالات عامة</th>
      <th class="num">طوارئ وصلت<br>لموظف (خاصة)</th>
      <th class="num">شكاوى وأسئلة طبية<br>وصلت لموظف (خاصة)</th>
      <th class="num">دبي<br>الطريقة نفسها</th>
    </tr>
    {CARD}
  </table>

  <p class="note" style="margin-top:10px">المظلّلان ينتقلان إلى المرحلة الثانية بالقاعدة المسجّلة مسبقًا؛ الفرق بين الثاني والثالث داخل فترة الثقة<br><span class="dim">الحالات الخاصة كتبها متحدثان نجديان ولم تُنشر · «محوّل»: محوّل JSON لعرض الأدوات · «—»: لم تُقس هذه الطريقة على حالات دبي بعد · كل النماذج التي اختبرناها موجودة</span></p>

  <div class="foot"><span class="mono">miqyaslab.com</span></div>
</body>
</html>
"""
open("findings/jt02-riyadh-stage1/scorecard_x_source.html", "w", encoding="utf-8").write(head + body)
print("ok", len(table_wins), "of", len(P), "table>tool on private;", [e["model"] for e in table_wins])
