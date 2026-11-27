#!/usr/bin/env python3
"""The site frame (site revamp, 26 Nov 2026): writes the new pages and puts the shared header and footer on every
other page.

    python3 scripts/build_site_pages.py           writes the pages
    python3 scripts/build_site_pages.py --check   fails if any page differs from what this script writes

New pages: / (home), /التجارب/ (trials), /الاستقلالية/ (independence and funding), /تواصل/ (contact).
Older pages keep their content; the header goes right after <body> and the footer right before </body>, between
<!-- mq:header --> / <!-- mq:footer --> markers, so a second run changes nothing. Redirect pages are left alone.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMAIL = "hello@miqyaslab.com"
GITHUB = "https://github.com/Miqyas-Lab/job-trials"
HF = "https://huggingface.co/Miqyas-Lab"
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'none'")

HEADER = f"""<!-- mq:header -->
<link rel="stylesheet" href="/assets/site.css">
<header class="mq-header">
  <div class="mq-bar">
    <nav class="mq-nav" aria-label="الأقسام">
      <button type="button" class="mq-menu-btn" aria-label="القائمة" aria-expanded="false"><img src="/assets/brand/miqyas-favicon.svg" alt=""></button>
      <div class="mq-menu">
        <a href="/التجارب/">التجارب</a>
        <a href="/المنهجية/">المنهجية</a>
        <a href="/الاستقلالية/">الاستقلالية</a>
        <a href="/المعجم/">المعجم</a>
        <a href="/الأداة/">أداة الرموز</a>
        <a href="/تواصل/">تواصل معنا</a>
      </div>
    </nav>
    <div class="mq-brand">
      <a href="/" aria-label="مقياس: الصفحة الرئيسية"><img src="/assets/brand/miqyas-lockup-on-light.svg" alt="مقياس · Miqyas"></a>
      <span class="mq-sep"></span>
      <a class="mq-ext" href="{GITHUB}">GitHub</a>
      <a class="mq-ext" href="{HF}">Hugging Face</a>
    </div>
  </div>
</header>
<!-- /mq:header -->"""

FOOTER = f"""<!-- mq:footer -->
<footer class="mq-footer">
  <div class="mq-bar">
    <span class="mq-n">miqyaslab.com</span>
    <span><a href="{GITHUB}">GitHub</a><a href="{HF}">Hugging Face</a><a href="https://x.com/miqyaslab">X @miqyaslab</a></span>
  </div>
</footer>
<script src="/assets/site.js" defer></script>
<!-- /mq:footer -->"""


def page(title: str, description: str, path: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://miqyaslab.com{path}">
<link rel="canonical" href="https://miqyaslab.com{path}">
<link rel="icon" href="/assets/brand/miqyas-favicon.svg" type="image/svg+xml">
</head>
<body class="mq-page">
{HEADER}
{body}
{FOOTER}
</body>
</html>
"""


HOME = """<main>
  <section class="mq-wrap" style="padding-top:72px;padding-bottom:56px;display:flex;flex-wrap:wrap;gap:48px;align-items:flex-end">
    <div style="flex:7 1 520px;min-width:0">
      <h1 class="mq-h1" style="font-size:56px;line-height:1.25">مختبر مستقل للذكاء الاصطناعي</h1>
      <div class="mq-rule" style="margin:24px 0"></div>
      <p style="margin:0 0 16px;font-size:26px;font-weight:600;line-height:1.45;max-width:660px">ذكاء اصطناعي محلي، يُعتمد بالدليل.</p>
      <p style="margin:0;font-size:19px;line-height:1.6;max-width:600px">نختبر أي نموذج مفتوح الأوزان، عربيًا كان أو عالميًا، في عمل حقيقي بالعربية، ثم نساعد المؤسسات والأفراد على فهمه وتشغيله على أجهزتهم.</p>
      <div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:32px">
        <a class="mq-btn" href="/تواصل/">تواصل معنا</a>
        <a class="mq-btn-line" href="/التجارب/">كل التجارب</a>
      </div>
    </div>
    <div class="mq-column" aria-hidden="true"><div class="mq-scale">
      <div class="mq-tick" style="top:10%"></div><div class="mq-tick mq-minor" style="top:27%"></div><div class="mq-tick" style="top:44%"></div>
      <div class="mq-tick mq-minor" style="top:61%"></div><div class="mq-tick" style="top:78%"></div><div class="mq-dot"></div>
    </div></div>
  </section>
  <section class="mq-band" aria-label="مستكشف النتائج"><div class="mq-wrap" style="padding-top:48px;padding-bottom:48px">
    <div id="mq-explorer"></div>
  </div></section>
  <section class="mq-wrap" style="padding-top:64px;padding-bottom:56px">
    <div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:8px">
      <h2 class="mq-h2" style="font-size:32px;margin:0">التجارب</h2>
      <p style="margin:0;font-size:14px;color:#6E7178">كل تجربة: بروتوكول مسجّل في git قبل التشغيل، ومحادثات خام منشورة.</p>
    </div>
    <div id="mq-trials"></div>
  </section>
  <section class="mq-band"><div class="mq-wrap" style="padding-top:56px;padding-bottom:56px">
    <h2 class="mq-h2" style="font-size:32px;margin-bottom:24px">كيف نختبر</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:32px">
      <div style="border-top:3px solid #1F4E8C;padding-top:16px"><h3 style="margin:0 0 8px;font-size:20px">نسجّل قبل أن نشغّل</h3><p style="margin:0;font-size:16px;line-height:1.6;color:#3A3F47">البروتوكول والحالات وطريقة الحساب في git قبل أي تشغيل، وكل تعديل مؤرخ.</p></div>
      <div style="border-top:3px solid #1F4E8C;padding-top:16px"><h3 style="margin:0 0 8px;font-size:20px">ننشر كل محادثة</h3><p style="margin:0;font-size:16px;line-height:1.6;color:#3A3F47">المخرجات الخام كاملة، وما لم نقسه نكتب أنه لم يُقس.</p></div>
      <div style="border-top:3px solid #1F4E8C;padding-top:16px"><h3 style="margin:0 0 8px;font-size:20px">قواعد واحدة للجميع</h3><p style="margin:0;font-size:16px;line-height:1.6;color:#3A3F47">لا نقبل مالًا من مختبر نختبر نماذجه، ونفصح عن أي دعم آخر ومصدره. <a href="/الاستقلالية/" style="color:#1F4E8C">الاستقلالية</a></p></div>
    </div>
  </div></section>
</main>"""

TRIALS = """<main>
  <div class="mq-wrap" style="padding-top:40px;padding-bottom:32px">
    <h1 class="mq-h1">التجارب</h1>
    <div class="mq-rule"></div>
    <p class="mq-lead" style="font-size:18px">كل تجربة نشرناها، الأحدث أولًا. لكل تجربة بروتوكول مسجّل في git قبل التشغيل، ومحادثات خام منشورة كاملة. تجارب العمل تصدر حكمًا لكل نموذج ومهمة وجهاز؛ التجارب السريعة أرقام فقط.</p>
  </div>
  <section class="mq-band"><div class="mq-wrap" style="padding-top:32px;padding-bottom:56px"><div id="mq-trials"></div></div></section>
</main>"""


def card(title, text):
    return (f'<div class="mq-card" style="padding:24px"><h3>{title}</h3>'
            f'<p style="margin:10px 0 0;font-size:16px;line-height:1.75;color:#3A3F47">{text}</p></div>')


INDEPENDENCE = f"""<main>
  <div class="mq-wrap" style="padding-top:40px;padding-bottom:40px">
    <h1 class="mq-h1">الاستقلالية والتمويل</h1>
    <div class="mq-rule"></div>
    <p class="mq-lead">مقياس مختبر مستقل. القواعد أدناه تنطبق على كل مختبر وكل نموذج، ولا يغيّرها أي داعم.</p>
  </div>
  <section class="mq-band"><div class="mq-wrap mq-grid" style="padding-top:48px;padding-bottom:48px">
    {card("استقلال مالي عن المختبرات", "لا نقبل أي مال نقدي من مختبر تُختبر نماذجه هنا، ولا أي دعم مشروط باختبار نموذج أو الترويج له.")}
    {card("كل دعم معلن", 'قد نقبل رصيدًا سحابيًا أو عتادًا أو خدمات من أي جهة. كل دعم قيمته <span class="mq-n">50</span> دولارًا أو أكثر يُعلن هنا وفي صفحة كل تجربة يمسّها، باسم الجهة ونوع الدعم.')}
    {card("القواعد نفسها للجميع", "لا يرى أي مختبر النتائج قبل غيره. إن أُعطي مختبر مهلة للرد قبل النشر، تُعطى كل المختبرات المهلة نفسها. لا أحد يدفع ليظهر في أي مقارنة.")}
  </div></section>
  <section style="max-width:820px;margin:0 auto;padding:56px 24px 64px">
    <h2 class="mq-h2">ما لا يستطيع الداعم فعله</h2>
    <p style="margin:0 0 18px;font-size:17px;line-height:1.8">لا يحق لأي داعم اختيار النتائج، أو منع نشر نتيجة سلبية، أو شراء ترتيب في أي مقارنة. البروتوكول يُسجَّل في git قبل التشغيل، والمخرجات الخام تُنشر كاملة، فالدعم لا يغيّر ما يُقاس ولا كيف يُقاس.</p>
    <h2 class="mq-h2" style="margin-top:40px">العمل الاستشاري</h2>
    <p style="margin:0 0 18px;font-size:17px;line-height:1.8">قد نقدّم أعمالًا استشارية مدفوعة في نشر النماذج العربية. هذه الأعمال منفصلة عن المقارنات العامة المنشورة هنا، ولا تُستخدم بياناتها فيها. أي تجربة عامة تتناول نموذجًا لعميل استشاري تُعلن ذلك في مقدمتها.</p>
    <h2 class="mq-h2" style="margin-top:40px">الدعم المتلقّى</h2>
    <div style="border:1px solid #D8D5CE;border-radius:12px;overflow:hidden">
      <div style="display:grid;grid-template-columns:120px minmax(0,1fr);gap:16px;padding:14px 18px;background:#F4F6FA;font-size:14px;color:#3A3F47"><span>السنة</span><span>الجهة ونوع الدعم</span></div>
      <div style="display:grid;grid-template-columns:120px minmax(0,1fr);gap:16px;padding:16px 18px;border-top:1px solid #D8D5CE;font-size:16px"><span class="mq-n" style="text-align:right">2026</span><span>RunPod: رصيد سحابي ترويجي بقيمة <span class="mq-n">5</span> دولارات، غير مرتبط بأي نموذج أو تجربة.</span></div>
    </div>
    <p style="margin:16px 0 0;font-size:14px;line-height:1.7;color:#6E7178">كل تعديل على هذه الصفحة مؤرخ ومحفوظ في <a href="{GITHUB}/commits/main/%D8%A7%D9%84%D8%A7%D8%B3%D8%AA%D9%82%D9%84%D8%A7%D9%84%D9%8A%D8%A9" style="color:#1F4E8C">سجل git العام</a>.</p>
  </section>
</main>"""


def route(title, text, btn, href):
    return (f'<div class="mq-card" style="padding:24px;display:flex;flex-direction:column"><h3>{title}</h3>'
            f'<p style="margin:10px 0 20px;font-size:16px;line-height:1.75;color:#3A3F47;flex:1">{text}</p>'
            f'<a class="mq-btn" style="align-self:flex-start" href="{href}">{btn}</a></div>')


CONTACT = f"""<main>
  <div class="mq-wrap" style="padding-top:40px;padding-bottom:40px">
    <h1 class="mq-h1">تواصل معنا</h1>
    <div class="mq-rule"></div>
    <p class="mq-lead">اختر ما يناسب طلبك. نرد على كل رسالة، ولا نشارك عنوانك مع أي جهة.</p>
  </div>
  <section class="mq-band"><div class="mq-wrap mq-grid" style="padding-top:48px;padding-bottom:64px">
    {route("مؤسسة تريد تشغيل ذكاء اصطناعي محلي", "عيادة أو بنك أو جهة حكومية. نساعد في اختيار النموذج المناسب لعملك، وتشغيله على أجهزتك، وتدريب فريقك عليه.", "راسلنا", f"mailto:{EMAIL}?subject=%D9%85%D8%B3%D8%A7%D8%B9%D8%AF%D8%A9%20%D9%81%D9%8A%20%D8%AA%D8%B4%D8%BA%D9%8A%D9%84%20%D9%86%D9%85%D9%88%D8%B0%D8%AC%20%D9%85%D8%AD%D9%84%D9%8A")}
    {route("مختبر أو مطوّر يريد اختبار نموذج", "اطلب اختبار نموذجك علنًا على GitHub. نختبر بالقواعد نفسها لكل النماذج، ولا نقبل مالًا من مختبر نختبر نماذجه.", "اطلب اختبارًا", f"{GITHUB}/issues/new?title=Model%20test%20request%3A%20")}
    {route("صحافة وباحثون", "للأسئلة عن تجاربنا وبياناتنا، أو لطلب تعليق على نتيجة منشورة.", "راسلنا", f"mailto:{EMAIL}")}
  </div></section>
  <section class="mq-wrap" style="padding-top:32px;padding-bottom:56px">
    <p style="margin:0;font-size:15px;color:#6E7178">البريد المباشر: <a href="mailto:{EMAIL}" class="mq-n" style="color:#1F4E8C">{EMAIL}</a></p>
  </section>
</main>"""

NEW = {
    "index.html": ("مقياس · Miqyas Lab", "مختبر مستقل للذكاء الاصطناعي: نختبر النماذج مفتوحة الأوزان في عمل حقيقي بالعربية، وننشر كل محادثة.", "/", HOME),
    "التجارب/index.html": ("مقياس · التجارب", "كل تجارب مقياس المنشورة، مع أرقامها ومحادثاتها الخام.", "/التجارب/", TRIALS),
    "الاستقلالية/index.html": ("مقياس · الاستقلالية والتمويل", "قواعد مقياس في التمويل والاستقلالية، والدعم المتلقّى.", "/الاستقلالية/", INDEPENDENCE),
    "تواصل/index.html": ("مقياس · تواصل معنا", "تواصل مع مقياس: تشغيل ذكاء اصطناعي محلي، أو طلب اختبار نموذج، أو أسئلة صحفية وبحثية.", "/تواصل/", CONTACT),
}
FRAMED = ["المعيار/index.html", "المعيار/مساهمون/index.html", "المنهجية/index.html", "المعجم/index.html", "الأداة/index.html",
          "الحاسبة/index.html"]


def framed(text: str) -> str:
    text = re.sub(r"\n?<!-- mq:header -->.*?<!-- /mq:header -->", "", text, flags=re.S)
    text = re.sub(r"\n?<!-- mq:footer -->.*?<!-- /mq:footer -->", "", text, flags=re.S)
    text = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + HEADER, text, count=1)
    i = text.rfind("</body>")
    return text[:i] + FOOTER + "\n" + text[i:]


def targets() -> dict[Path, str]:
    out = {ROOT / f: page(*v) for f, v in NEW.items()}
    for f in FRAMED + sorted(str(p.relative_to(ROOT)) for p in (ROOT / "findings").glob("*/index.html")):
        p = ROOT / f
        out[p] = framed(p.read_text(encoding="utf-8"))
    return out


def main(argv) -> int:
    bad = []
    for p, text in targets().items():
        if "--check" in argv:
            if not p.is_file() or p.read_text(encoding="utf-8") != text:
                bad.append(str(p.relative_to(ROOT)))
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
    if "--check" in argv:
        print("pages up to date" if not bad else "not up to date: " + ", ".join(bad))
        return 1 if bad else 0
    print(f"wrote {len(NEW)} new pages and framed the others")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
