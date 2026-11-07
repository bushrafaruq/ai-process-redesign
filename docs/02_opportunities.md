# 2. AI and automation opportunities

Eight candidate opportunities came out of the pain points in [01_current_state.md](01_current_state.md).
Each is scored 1-5 on five criteria. For **risk**, 5 means *low* risk, so a higher score is always
better. Scores and weights live in `src/case_study/run.py`; the output is
`outputs/opportunity_scores.csv`.

| Criterion | Weight | What a 5 means |
|---|---|---|
| Value | 30% | Removes a major pain point or a large share of effort |
| Feasibility | 20% | Can be built and run with today's tools and skills |
| Data readiness | 15% | The data it needs exists and is usable now |
| Risk (5 = low) | 20% | Errors are cheap, visible and reversible; no safety or spend decisions without a person |
| Adoption | 15% | Fits how staff and residents already work |

## 2.1 Scores

| Opportunity | Value | Feas. | Data | Risk | Adopt. | **Score** | Decision |
|---|---|---|---|---|---|---|---|
| Instant acknowledgement with expected response time | 3 | 5 | 5 | 5 | 5 | **4.40** | Wave 1 |
| AI triage & routing with human approval | 5 | 4 | 4 | 4 | 4 | **4.30** | Wave 1 |
| Automated weekly KPI report | 3 | 5 | 4 | 5 | 4 | **4.10** | Wave 1 |
| Duplicate / same-issue detection | 3 | 3 | 3 | 4 | 4 | **3.35** | Wave 2 |
| Predictive maintenance from repeat faults | 4 | 2 | 1 | 4 | 3 | **3.00** | Wave 2 |
| Sentiment and complaint escalation | 2 | 4 | 3 | 3 | 3 | 2.90 | Not now |
| Resident self-service FAQ assistant | 3 | 3 | 2 | 3 | 3 | 2.85 | Not now |
| Fully autonomous resolution (AI books contractors) | 4 | 2 | 2 | 1 | 2 | 2.40 | Not now |

## 2.2 Reading the ranking

* **Wave 1 is one product, not three.** Triage creates the structured category, priority and owner
  for every request. The acknowledgement uses that to tell the resident who has it and when they will
  hear back; the KPI report is built from the same data. Triage has the highest value; the other two
  are cheap once it exists.
* **Predictive maintenance is valuable but not ready.** It needs reliable fault categories by asset
  and room, which do not exist until triage has run for a few months. Data readiness, not value, holds
  it back.
* **Autonomous resolution is deliberately parked.** It would commit spend and make safety calls with no
  person involved. The value is real, but the risk score of 1 rules it out until the triage agent has a
  measured track record.
* **The FAQ assistant** depends on a maintained knowledge base, and wrong answers go straight to
  residents. Revisit after Wave 1.

## 2.3 Sensitivity

If risk is ignored (weight 0, others rescaled), triage moves to first place (4.38), the same three
opportunities stay in Wave 1, and autonomous resolution is still joint last (2.75), because its
feasibility and data readiness are low as well. The Wave 1 decision does not depend on the exact
weights.
