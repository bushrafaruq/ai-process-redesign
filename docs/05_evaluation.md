# 5. Prototype evaluation

The prototype is evaluated on `data/test_set.csv`: 80 hand-labelled synthetic requests covering all
11 categories, with 13 urgent (P1) cases including fire, gas, an intruder, an injury and threats.
Run it with `python -m triage.evaluate` (baseline) or `python -m triage.evaluate --llm` (LLM).

## 5.1 Why these metrics

Accuracy alone hides the errors that matter. A routine request sent to the wrong team costs minutes;
an urgent one marked routine can cost far more. So the headline metrics are:

* **P1 recall:** share of truly urgent requests the agent marks urgent.
* **Safety escalation recall:** share of true safety requests that go straight to the duty manager.
* **Quick-approve precision:** how often the one-click suggestion is right. This decides whether
  coordinators trust the tool, which decides whether the business case is real.

## 5.2 Results: keyword baseline (`baseline-keywords-v1`)

| Metric | Result | Go-live gate |
|---|---|---|
| Category accuracy | 88.7% | |
| Category macro F1 | 0.885 | |
| Priority accuracy | 66.2% | |
| **P1 recall** | **69.2% (9 of 13)** | >= 95%: **fails** |
| **Safety escalation recall** | **72.7%** | >= 95%: **fails** |
| Over-escalated to P1 | 3 requests | |
| Quick-approve precision | 98.3% | >= 95%: passes |
| Review mode mix | 72.5% quick approve, 12.5% full review, 15% escalate now | |

Full error list: `outputs/eval_baseline_keywords_v1.md`. Confusion matrix:
`outputs/confusion_baseline_keywords_v1.png`.

## 5.3 What the errors show

* **Category is the easy part; urgency is the hard part.** Keywords find *what* the request is about
  but not *how bad* it is. "Toilet is overflowing onto the floor" was routed correctly but marked
  routine; "my ceiling light fell down, the wires are hanging out" the same.
* **The dangerous misses have no obvious keyword.** "A man I don't know followed me in through the main
  door" and "the guy next door is shouting and banging on the walls, I'm worried for her" describe
  safety risks in ordinary words. A keyword list will never be complete for these.
* **Quick approvals are reliable.** When the baseline is confident it is right 98% of the time, so the
  one-click path is safe for routine work.

**Conclusion.** The keyword baseline is good enough for routine routing but **does not pass the safety
gate and must not go live alone**. This is the case for an LLM classifier (which reads meaning, not
words) *with* the rule-based safety net and human review kept in place. The LLM result below decides
whether the pilot goes ahead.

## 5.4 Results: LLM classifier

Run `python -m triage.evaluate --llm` with `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` set. Results are
written to `outputs/eval_llm_*.md`; `python -m case_study.run` then uses them in the business case
automatically.

| Metric | Result | Go-live gate |
|---|---|---|
| Category accuracy | *to be filled from outputs/eval_llm_*.md* | |
| P1 recall | | >= 95% |
| Safety escalation recall | | >= 95% |
| Quick-approve precision | | >= 95% |

## 5.5 Limitations

* **Synthetic test set, written by the same person as the keyword rules.** The baseline result is
  therefore optimistic. A real pilot needs a test set sampled from real requests and labelled by two
  coordinators independently.
* **80 examples is small.** With 13 P1 cases, one miss moves P1 recall by about 8 points. The gate
  should be re-checked on a larger set before go-live.
* **Redaction is pattern-based.** It removes structured identifiers but not names in free text. A
  production system needs a named-entity step or a data processing agreement that covers names.
* **English only,** and no handling of images or attachments.
* **Confidence from the LLM is self-reported** and needs calibrating against real outcomes.
