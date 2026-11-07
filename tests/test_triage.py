import json

import pytest

from triage.agent import TriageAgent, review_mode
from triage.classifier import BaselineClassifier, LLMClassifier, Triage, validate
from triage.redact import redact


def test_redact_removes_structured_pii():
    text = "Email ana.k@gmail.com, call 087 123 4567, IBAN IE29 AIBK 9311 5212 3456 78, D08 XY12"
    clean, counts = redact(text)
    assert "ana.k@gmail.com" not in clean
    assert "087 123 4567" not in clean
    assert "IE29" not in clean
    assert "D08 XY12" not in clean
    assert counts == {"EMAIL": 1, "IBAN": 1, "PHONE": 1, "EIRCODE": 1}


def test_redact_leaves_room_numbers_alone():
    clean, counts = redact("Leak in room 214, floor 3")
    assert clean == "Leak in room 214, floor 3"
    assert counts == {}


def test_safety_always_escalates():
    t = Triage("safety_security", "P1", 0.95, "", "x", safety_flag=True)
    assert review_mode(t) == "ESCALATE_NOW"


def test_low_confidence_goes_to_full_review():
    t = Triage("cleaning_waste", "P3", 0.3, "", "x")
    assert review_mode(t) == "FULL_REVIEW"


def test_gas_smell_is_p1_safety():
    t = BaselineClassifier().classify("I can smell gas in the kitchen")
    assert t.category == "safety_security" and t.priority == "P1" and t.safety_flag


def test_unknown_text_defaults_to_full_review(tmp_path):
    agent = TriageAgent(audit_path=tmp_path / "log.jsonl")
    p = agent.propose("hello there")
    assert p.review_mode == "FULL_REVIEW"


def test_audit_log_has_no_raw_pii(tmp_path):
    log = tmp_path / "log.jsonl"
    agent = TriageAgent(audit_path=log)
    p = agent.propose("Charged twice for rent, email me at ana.k@gmail.com")
    agent.record_decision(p, reviewer="coordinator-1", action="edited", final_priority="P2")
    content = log.read_text()
    assert "ana.k@gmail.com" not in content
    events = [json.loads(line)["event"] for line in content.splitlines()]
    assert events == ["proposed", "decided"]


def test_override_is_recorded(tmp_path):
    agent = TriageAgent(audit_path=tmp_path / "log.jsonl")
    p = agent.propose("The oven doesn't work")
    d = agent.record_decision(p, "coordinator-1", "edited", final_category="safety_security")
    assert d["overridden"] is True and d["final"]["owner"] == "Duty Manager"


def test_invalid_decision_rejected(tmp_path):
    agent = TriageAgent(audit_path=tmp_path / "log.jsonl")
    p = agent.propose("The oven doesn't work")
    with pytest.raises(ValueError):
        agent.record_decision(p, "c1", "maybe")


def test_schema_validation_rejects_bad_category():
    with pytest.raises(ValueError):
        validate({"category": "plumbing", "priority": "P1", "confidence": 0.9,
                  "safety_flag": False, "rationale": ""})


def test_llm_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    t = LLMClassifier().classify("My radiator is cold")
    assert "fallback" in t.model and t.category == "heating_hvac"


def test_llm_output_safety_net(monkeypatch):
    """If the model says 'not safety' but the text mentions gas, the rule net still escalates."""
    clf = LLMClassifier()
    clf.provider = "fake"
    monkeypatch.setattr(clf, "_call", lambda text: json.dumps(
        {"category": "maintenance_general", "priority": "P3", "confidence": 0.9,
         "safety_flag": False, "rationale": "cooker issue"}))
    t = clf.classify("Cooker smells of gas")
    assert t.safety_flag and t.priority == "P1"
