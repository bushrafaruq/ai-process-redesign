"""The triage agent: redact -> classify -> route -> decide the human step -> draft reply -> log.

Design rule (docs/03_future_state.md): the agent PROPOSES, a person DISPOSES.
In this first release every routing decision is approved by a coordinator.
What changes with confidence is HOW the item is presented:

* ESCALATE_NOW  - safety flag or P1: on-call/duty manager is alerted immediately,
                  in parallel with coordinator review. Never waits in a queue.
* QUICK_APPROVE - high confidence: one-click approval of the proposed routing.
* FULL_REVIEW   - low confidence: coordinator classifies with the proposal as a hint.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .classifier import BaselineClassifier, Triage
from .redact import redact
from .taxonomy import CATEGORIES, PRIORITIES

CONFIDENCE_THRESHOLD = 0.6

REPLY_TEMPLATES = {
    "P1": ("Thank you for letting us know. This has been marked urgent and the {owner} "
           "team has been alerted now. If anyone is in danger, call 112 immediately."),
    "P2": ("Thank you for your message. We have passed this to the {owner} team as a "
           "high-priority {label} request. You will hear from them within {hours} hours."),
    "P3": ("Thank you for your message. We have logged this as a {label} request with "
           "the {owner} team. You will hear from them within {hours} hours."),
}


@dataclass
class Proposal:
    request_id: str
    received_at: str
    redacted_text: str
    pii_removed: dict
    category: str
    owner: str
    priority: str
    confidence: float
    safety_flag: bool
    review_mode: str
    draft_reply: str
    rationale: str
    model: str


def review_mode(t: Triage, threshold: float = CONFIDENCE_THRESHOLD) -> str:
    if t.safety_flag or t.priority == "P1":
        return "ESCALATE_NOW"
    if t.confidence >= threshold:
        return "QUICK_APPROVE"
    return "FULL_REVIEW"


def draft_reply(category: str, priority: str) -> str:
    c = CATEGORIES[category]
    return REPLY_TEMPLATES[priority].format(
        owner=c.owner, label=c.label.lower(), hours=PRIORITIES[priority]["first_response_hours"])


class TriageAgent:
    def __init__(self, classifier=None, audit_path: str | Path = "outputs/audit_log.jsonl",
                 threshold: float = CONFIDENCE_THRESHOLD):
        self.classifier = classifier or BaselineClassifier()
        self.audit_path = Path(audit_path)
        self.threshold = threshold

    def propose(self, text: str, request_id: str | None = None) -> Proposal:
        clean, pii = redact(text)
        t = self.classifier.classify(clean)
        prop = Proposal(
            request_id=request_id or uuid.uuid4().hex[:8],
            received_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            redacted_text=clean,
            pii_removed=pii,
            category=t.category,
            owner=CATEGORIES[t.category].owner,
            priority=t.priority,
            confidence=t.confidence,
            safety_flag=t.safety_flag,
            review_mode=review_mode(t, self.threshold),
            draft_reply=draft_reply(t.category, t.priority),
            rationale=t.rationale,
            model=t.model,
        )
        self._log("proposed", asdict(prop))
        return prop

    def record_decision(self, prop: Proposal, reviewer: str, action: str,
                        final_category: str | None = None, final_priority: str | None = None,
                        note: str = "") -> dict:
        """action: 'approved' | 'edited' | 'rejected'. Every decision is logged."""
        if action not in {"approved", "edited", "rejected"}:
            raise ValueError("action must be approved, edited or rejected")
        fc = final_category or prop.category
        fp = final_priority or prop.priority
        if fc not in CATEGORIES or fp not in PRIORITIES:
            raise ValueError("unknown category or priority")
        decision = {
            "request_id": prop.request_id,
            "reviewer": reviewer,
            "action": action,
            "proposed": {"category": prop.category, "priority": prop.priority},
            "final": {"category": fc, "priority": fp, "owner": CATEGORIES[fc].owner},
            "overridden": (fc, fp) != (prop.category, prop.priority),
            "note": note,
        }
        self._log("decided", decision)
        return decision

    def _log(self, event: str, payload: dict) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, **payload}
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
