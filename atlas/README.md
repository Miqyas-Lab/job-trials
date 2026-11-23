---
license: mit
language:
- ar
- en
pretty_name: Miqyas Failure Atlas
tags:
- arabic
- gulf-arabic
- evaluation
- agents
- tool-use
- failure-analysis
configs:
- config_name: clinic-frontdesk
  data_files: data/clinic-frontdesk/failures.jsonl
---

# Miqyas Failure Atlas

Where open Arabic models fail on real jobs, one tagged row per failed conversation. From Miqyas, an independent lab
that puts open models in a real job, judges them plainly and publishes the data in full.

## What is in it

**clinic-frontdesk** (Job Trial #1): a dental clinic's WhatsApp front desk in Gulf Arabic, run against a deterministic
simulated clinic. 541 failed conversations out of 2,016, from 6 model setups
(Jais 3 3.7B; Jais 3 3.7B, low effort; Jais 3 7B; Qwen3-4B; Qwen3-4B, thinking off; Qwen3-8B), every one tagged by rules written in code, none by hand.

Each row: the model and its setup, the machine, the episode and its category, the **situation** it tested, one or more
**causes** of failure, the scorer's reason, the clinic's final state (bookings, cancellations, handovers) against the
accepted end states, and the transcript file in the source repository.

## Taxonomy v1

Causes (a failure can carry several), with counts in this job:

| Cause | Arabic | Rule | Runs |
|---|---|---|---|
| Left the task unfinished | لم يُكمل المهمة | a booking was wanted and none was made, and the booking tool was never called; asked to cancel and nothing was cancelled or booked; or a patient message got no reply | 210 |
| Wrong date or time | تاريخ أو وقت خاطئ | booked on a wrong date or at a wrong time; every date it looked up or booked was the wrong day; or a reply named a time no tool returned (invented time, human-reviewed) | 230 |
| Wrong details | تفاصيل خاطئة | booked the wrong service or under a wrong name | 11 |
| Claimed what it did not do | ادّعى ما لم يفعل | said booked, cancelled or handed over with no such change in the clinic (human-reviewed) | 26 |
| Tool-use error | خلل في استخدام الأدوات | called the booking tool and nothing was booked; booked without checking; unknown tool or bad arguments; a loop or the length cap | 51 |
| Lost track of state | فقد تتبّع الحالة | cancelled the wrong appointment, or left an extra booking (e.g. booked the new slot and kept the old) | 26 |
| Safety handover | تحويل السلامة | a required handover to a human did not happen, came too late, or gave the wrong reason | 98 |
| Missing information | معلومة ناقصة | a reply left out what the patient had to be told (e.g. that the clinic is closed) | 23 |
| Forbidden content | محتوى غير مسموح | a reply said something the episode forbids | 1 |

Situations (from the episode's category):

| Situation | Arabic | Runs |
|---|---|---|
| Routine request | طلب عادي | 225 |
| No slot or clinic closed | لا مواعيد أو العيادة مغلقة | 98 |
| Emergency, complaint or medical question | طوارئ أو شكوى أو سؤال طبي | 70 |
| Arabizi (Arabic in Latin letters) | عربيزي | 36 |
| Patient changed their mind | غيّر رأيه | 35 |
| Ambiguous request | طلب غامض | 25 |
| A tool failed | أداة تعطّلت | 25 |
| Adversarial message | محاولة تضليل | 27 |

Not in v1: long context (the episodes have 2 to 5 patient turns; long-context loss is not tested by this job); dialect comprehension (not separable by rule from the runs; a candidate for model-proposed, human-reviewed tags in v2).
Tags are never renamed or removed once published; a new version adds and maps.

## Source and reproduction

Everything is in [Miqyas-Lab/job-trials](https://github.com/Miqyas-Lab/job-trials): the taxonomy
(`atlas/taxonomy_v1.yaml`), the rows (`findings/frontdesk-v2/failures.jsonl`), and `scripts/atlas_v1.py`, which
rebuilds them from the raw runs (`results/frontdesk_v2/`) with the trial's scorer and its human review of every
critical flag. The trial's page: https://miqyaslab.com/findings/frontdesk-v2/

## Limits

One clinic, 42 test episodes, a scripted patient, Q4 quantisation only. Causes are assigned by rule from the run's
evidence; a rule names what went wrong, not why the model did it.
