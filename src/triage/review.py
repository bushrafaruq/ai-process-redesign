"""Coordinator review queue (command line).

    python -m triage.review "My radiator is cold and it's freezing"
    python -m triage.review --file data/sample_inbox.csv

For each request the agent shows its proposal; the coordinator approves, edits or rejects.
Every proposal and decision is written to outputs/audit_log.jsonl.
"""

from __future__ import annotations

import argparse
import csv

from .agent import TriageAgent
from .classifier import BaselineClassifier, LLMClassifier
from .taxonomy import CATEGORIES, PRIORITIES

BADGE = {"ESCALATE_NOW": "!! ESCALATE NOW", "QUICK_APPROVE": "quick approve", "FULL_REVIEW": "full review"}


def review_one(agent: TriageAgent, text: str, reviewer: str, rid: str | None = None) -> None:
    p = agent.propose(text, request_id=rid)
    print("\n" + "=" * 72)
    print(f"[{p.request_id}] {BADGE[p.review_mode]}")
    print(f"Request : {p.redacted_text}")
    if p.pii_removed:
        print(f"PII     : removed {p.pii_removed}")
    print(f"Proposal: {p.category} -> {p.owner} | {p.priority} | confidence {p.confidence}")
    print(f"Why     : {p.rationale}")
    print(f"Reply   : {p.draft_reply}")
    if p.review_mode == "ESCALATE_NOW":
        print(f">> {p.owner} on-call alerted (simulated). Review still required for the record.")
    choice = input("[a]pprove / [e]dit / [r]eject ? ").strip().lower()[:1] or "a"
    if choice == "e":
        cats = list(CATEGORIES)
        for i, c in enumerate(cats):
            print(f"  {i}: {c}")
        ci = input(f"category number [{cats.index(p.category)}]: ").strip()
        pr = input(f"priority {list(PRIORITIES)} [{p.priority}]: ").strip().upper()
        note = input("note (optional): ").strip()
        d = agent.record_decision(p, reviewer, "edited",
                                  final_category=cats[int(ci)] if ci else None,
                                  final_priority=pr or None, note=note)
    elif choice == "r":
        d = agent.record_decision(p, reviewer, "rejected", note=input("reason: ").strip())
    else:
        d = agent.record_decision(p, reviewer, "approved")
    print(f"Routed to {d['final']['owner']} as {d['final']['category']}/{d['final']['priority']}"
          + (" (override logged)" if d["overridden"] else ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--file", help="CSV with columns id,text")
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--reviewer", default="coordinator-1")
    args = ap.parse_args()
    agent = TriageAgent(LLMClassifier() if args.llm else BaselineClassifier())
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                review_one(agent, row["text"], args.reviewer, row.get("id"))
    elif args.text:
        review_one(agent, args.text, args.reviewer)
    else:
        ap.error("give a request text or --file")


if __name__ == "__main__":
    main()
