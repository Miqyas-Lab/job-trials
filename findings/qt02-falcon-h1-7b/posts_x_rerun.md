# qt-02 · Falcon-H1 7B · correction thread (Miqyas X account), DRAFT for Mahmoud's review

Numbers from results.json (falcon_rerun, rerun_change_vs_first_run) and results/qt02r/.../scorecard.txt. Post after the
re-run page is live (PR #3 merged). Quote-post or reply to tweet 1/8 of the original qt-02 thread so readers of the old
numbers see it.

---
1/4
تصحيح · Falcon-H1 7B

وجدنا خللًا في أداة الاختبار لدينا: قالب Falcon-H1 لا يعرض استدعاءات الأدوات، وأداتنا كانت تحفظ استدعاءاته هناك فقط. فكان النموذج يرى أدوارًا فارغة منسوبة إليه.

أعدنا التشغيل بعد الإصلاح. الخطأ في أداتنا، لا في النموذج.

---
2/4
النتيجة على الإعداد المشترك (أداة التاريخ):
محادثات صحيحة كاملة: 25% بدل 14% (32 من 126)
طوارئ وصلت لموظف: 13 من 25 بدل 8

مع التقويم في التعليمات: 37% بدل 21%
بلا مساعدة في التاريخ: 18%، بلا تغيير

---
3/4
الملف والإعدادات نفسها، والتغيير الوحيد أن النموذج صار يرى استدعاءاته في سجل المحادثة. سجّلنا إعادة التشغيل في git قبل تشغيلها، وأبقينا أرقام التشغيل الأول على الصفحة بجانب الجديدة.

ما زال بعيدًا عن حد الوظيفة (90%).

---
4/4
كل النماذج على الإعداد نفسه الآن:
Jais 3 7B: 70% · Qwen3 8B: 68% · Fanar 2 27B: 55% · Qwen3 4B: 29% · Jais 3 3.7B: 29% · Falcon-H1 7B: 25% · ALLaM 7B: 9%

التفاصيل والبيانات الخام:
miqyaslab.com/findings/qt02-falcon-h1-7b/
