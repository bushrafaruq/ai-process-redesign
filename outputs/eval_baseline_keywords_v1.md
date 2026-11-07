# Evaluation: `baseline-keywords-v1`

Test set: 80 hand-labelled synthetic requests. Confidence threshold: 0.6.

| Metric | Value |
|---|---|
| category_accuracy | 0.887 |
| category_macro_f1 | 0.885 |
| priority_accuracy | 0.662 |
| p1_recall | 0.692 |
| safety_escalation_recall | 0.727 |
| over_escalated_to_p1 | 3 |
| quick_approve_precision | 0.983 |
| llm_fallbacks | 0 |
| review_mode_share | {'ESCALATE_NOW': 0.15, 'FULL_REVIEW': 0.125, 'QUICK_APPROVE': 0.725} |

## Per category

| Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| maintenance_plumbing | 1.0 | 1.0 | 1.0 | 9 |
| maintenance_general | 0.8 | 1.0 | 0.889 | 12 |
| heating_hvac | 1.0 | 0.714 | 0.833 | 7 |
| access_keys | 1.0 | 0.75 | 0.857 | 8 |
| billing_payments | 1.0 | 1.0 | 1.0 | 8 |
| noise_conduct | 0.833 | 1.0 | 0.909 | 5 |
| cleaning_waste | 1.0 | 0.833 | 0.909 | 6 |
| internet_wifi | 1.0 | 1.0 | 1.0 | 6 |
| move_in_out | 1.0 | 1.0 | 1.0 | 5 |
| general_enquiry | 0.429 | 1.0 | 0.6 | 3 |
| safety_security | 0.875 | 0.636 | 0.737 | 11 |

## Errors (30)

| ID | True | Predicted | Conf | Mode | Text |
|---|---|---|---|---|---|
| T001 | maintenance_plumbing/P2 | maintenance_plumbing/P3 | 0.75 | QUICK_APPROVE | Hi, the toilet in my ensuite keeps running and won't stop filling. Room 214. |
| T012 | maintenance_general/P2 | maintenance_general/P3 | 0.75 | QUICK_APPROVE | Fridge in our flat is warm, all our food is going off. |
| T017 | heating_hvac/P3 | maintenance_general/P3 | 0.1 | FULL_REVIEW | There's black mould growing around my window, I think from condensation. |
| T019 | heating_hvac/P3 | general_enquiry/P3 | 0.0 | FULL_REVIEW | Extractor in the bathroom isn't pulling any air, mirror stays steamed for an hour |
| T021 | access_keys/P2 | access_keys/P3 | 0.75 | QUICK_APPROVE | Lost my key card on the bus, need a replacement please |
| T022 | access_keys/P2 | access_keys/P3 | 0.75 | QUICK_APPROVE | My fob stopped working on the main entrance but works on my bedroom door |
| T024 | access_keys/P2 | access_keys/P3 | 0.65 | QUICK_APPROVE | The bike shed lock is jammed, nobody can get their bikes out |
| T028 | billing_payments/P2 | billing_payments/P3 | 0.8 | QUICK_APPROVE | My direct debit failed because I changed banks, new IBAN IE29 AIBK 9311 5212 3456 78. How do I update it? |
| T030 | billing_payments/P2 | billing_payments/P3 | 0.75 | QUICK_APPROVE | When will I get my deposit back? I moved out 6 weeks ago. |
| T034 | noise_conduct/P2 | noise_conduct/P3 | 0.95 | QUICK_APPROVE | There is a party going on right now in the common room, it's 2am and very noisy |
| T035 | safety_security/P1 | noise_conduct/P3 | 0.7 | QUICK_APPROVE | The guy next door is shouting at his girlfriend and banging on the walls, I'm worried for her |
| T037 | cleaning_waste/P2 | maintenance_general/P3 | 0.15 | FULL_REVIEW | I saw a mouse in our kitchen last night, ran under the fridge |
| T041 | internet_wifi/P2 | internet_wifi/P3 | 0.85 | QUICK_APPROVE | Wifi keeps dropping every 10 minutes in my room, I can't do my online classes |
| T053 | safety_security/P1 | general_enquiry/P3 | 0.0 | FULL_REVIEW | A man I don't know followed me in through the main door and is wandering the corridors |
| T054 | safety_security/P2 | safety_security/P1 | 0.75 | ESCALATE_NOW | My bike was stolen from the shed even though it was locked |
| T056 | safety_security/P2 | safety_security/P1 | 0.75 | ESCALATE_NOW | Smoke alarm in my room beeps every minute, I think the battery is low |
| T060 | maintenance_general/P2 | maintenance_general/P3 | 0.75 | QUICK_APPROVE | The lift is stuck on the 4th floor and has been for an hour |
| T061 | access_keys/P2 | access_keys/P3 | 0.75 | QUICK_APPROVE | The study room door won't open with my card anymore |
| T064 | heating_hvac/P2 | heating_hvac/P3 | 0.85 | QUICK_APPROVE | My room is so cold I'm sleeping in a jacket, the heater does nothing |
| T066 | internet_wifi/P2 | internet_wifi/P3 | 0.8 | QUICK_APPROVE | Can't log in to the wifi portal, it says my account is expired |
| T067 | access_keys/P2 | safety_security/P1 | 0.2 | ESCALATE_NOW | My key broke in the lock and half of it is stuck inside |
| T068 | cleaning_waste/P2 | cleaning_waste/P3 | 0.75 | QUICK_APPROVE | Cockroaches in the shared bathroom on floor 1 |
| T069 | safety_security/P2 | general_enquiry/P3 | 0.0 | FULL_REVIEW | The front door to the building doesn't close fully, anyone could walk in |
| T070 | general_enquiry/P3 | general_enquiry/P2 | 0.8 | QUICK_APPROVE | Hey my friend is staying over tonight, do I need to register them? |
| T071 | maintenance_plumbing/P1 | maintenance_plumbing/P3 | 0.75 | QUICK_APPROVE | Toilet is overflowing onto the floor and won't stop |
| T075 | heating_hvac/P2 | heating_hvac/P3 | 0.75 | QUICK_APPROVE | Hot water runs out after 2 minutes in the morning |
| T076 | general_enquiry/P3 | general_enquiry/P2 | 0.7 | QUICK_APPROVE | I'd like to give feedback, the reception staff were really helpful today! |
| T077 | safety_security/P1 | maintenance_general/P1 | 0.55 | ESCALATE_NOW | The microwave in kitchen B smells of burning plastic when it's on |
| T079 | access_keys/P2 | general_enquiry/P3 | 0.0 | FULL_REVIEW | The car park barrier isn't lifting for residents |
| T080 | maintenance_general/P1 | maintenance_general/P3 | 0.85 | QUICK_APPROVE | My ceiling light fell down, the wires are hanging out |
