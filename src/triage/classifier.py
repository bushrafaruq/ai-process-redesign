"""Two interchangeable classifiers that return the same structured output.

* BaselineClassifier: transparent keyword scoring. Runs offline with no API key,
  so the whole pipeline and evaluation can be reproduced by anyone.
* LLMClassifier: asks an LLM for a JSON object matching TRIAGE_SCHEMA, validates it,
  and falls back to the baseline if the call fails or the output is invalid.

Both produce a Triage result. The agent (agent.py) decides what happens next.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from .taxonomy import CATEGORIES, PRIORITIES


@dataclass
class Triage:
    category: str
    priority: str
    confidence: float          # 0-1, how sure the classifier is about the category
    rationale: str
    model: str
    safety_flag: bool = False  # possible risk to people: always escalated
    signals: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Baseline: weighted keyword rules
# --------------------------------------------------------------------------

KEYWORDS: dict[str, list[tuple[str, float]]] = {
    "maintenance_plumbing": [
        (r"\bleak", 3), (r"\bdrip", 2), (r"\bblock(ed|age)?\b", 2), (r"\bclog", 2),
        (r"\btoilet", 3), (r"\bflush", 2), (r"\bsink\b", 2), (r"\btap\b", 2), (r"\bshower", 2),
        (r"\bdrain", 2), (r"\bwater pressure", 3), (r"\bflood", 3), (r"\bpipe", 2),
        (r"\bplumb", 3), (r"\bceiling.*(wet|water)|(wet|water).*ceiling", 3),
    ],
    "maintenance_general": [
        (r"\bsocket", 3), (r"\bplug\b", 2), (r"\bfuse", 3), (r"\btripp?(ed|ing)?\b", 2),
        (r"\blight(s|bulb)?\b", 2), (r"\bbulb", 2), (r"\bpower\b", 2), (r"\belectric", 3),
        (r"\boven\b", 3), (r"\bhob\b", 3), (r"\bfridge", 3), (r"\bmicrowave", 3),
        (r"\bwashing machine|\bwasher\b|\bdryer\b", 3), (r"\bappliance", 3), (r"\bspark", 2),
        (r"\bextractor fan", 1), (r"\bwindow", 2), (r"\bwardrobe|\bdesk\b|\bchair\b|\bbed frame|\bfurniture", 2),
        (r"\bhinge|\bhandle\b|\bcupboard|\bdrawer|\bblinds?\b|\bcurtain", 2),
        (r"\blift\b|\belevator", 3), (r"\bbroken\b|\bbroke\b|\bfell (down|off)|\bcame off", 1), (r"\bwires?\b", 2),
    ],
    "heating_hvac": [
        (r"\bheat(ing|er)?\b", 3), (r"\bradiator", 3), (r"\bhot water\b", 3),
        (r"\bfreezing|\bcold\b", 2), (r"\bboiler", 3), (r"\bventilat", 2),
        (r"\bair ?con|\bhvac\b", 3), (r"\btemperature", 2), (r"\bmould|\bmold\b|\bcondensation", 2),
    ],
    "access_keys": [
        (r"\block(ed)? out\b|\blockout", 4), (r"\bkey ?card|\bkey\b|\bkeys\b", 3),
        (r"\bfob\b", 3), (r"\bdoor (won'?t|will not|doesn'?t) open", 3), (r"\baccess\b", 2),
        (r"\bswipe", 2), (r"\bcan'?t get in|cannot get in", 3), (r"\block\b", 1),
        (r"\bentry\b", 1),
    ],
    "billing_payments": [
        (r"\brent\b", 3), (r"\binvoice", 3), (r"\bpay(ment|ing)?\b", 3), (r"\bcharged?\b", 2),
        (r"\brefund", 3), (r"\bdeposit", 3), (r"\bdirect debit", 3), (r"\bbalance\b", 2),
        (r"\breceipt", 2), (r"\bfee\b|\bfees\b", 2), (r"€|\beur\b|\beuro", 2), (r"\bbank", 1),
        (r"\bstatement", 2), (r"\bovercharg", 3),
    ],
    "noise_conduct": [
        (r"\bnois(e|y)", 4), (r"\bloud\b", 3), (r"\bmusic\b", 2), (r"\bparty|\bparties", 3),
        (r"\bneighbou?r", 2), (r"\bshout", 2), (r"\bscream", 1), (r"\bsmok(e|ing) in", 2),
        (r"\bdisturb", 2), (r"\bflatmate|\broommate", 2), (r"\bcomplain", 1), (r"\bkeep(ing)? me (up|awake)", 3),
    ],
    "cleaning_waste": [
        (r"\bbin(s)?\b", 3), (r"\brubbish|\btrash|\bgarbage|\bwaste\b", 3), (r"\bclean", 3),
        (r"\bdirty|\bfilthy|\bmess(y)?\b", 2), (r"\bsmell(s|y)?\b", 1), (r"\bmice\b|\bmouse\b|\brats?\b", 3),
        (r"\bcockroach|\bpest", 3), (r"\bspill", 1), (r"\brecycl", 2), (r"\bhousekeep", 3),
    ],
    "internet_wifi": [
        (r"\bwi-?fi\b", 4), (r"\binternet", 4), (r"\bnetwork", 2), (r"\bconnect(ion|ed|ing)?\b", 2),
        (r"\brouter", 3), (r"\bethernet", 3), (r"\bonline\b", 1), (r"\bslow\b", 1),
        (r"\bbroadband", 3), (r"\bsignal", 1),
    ],
    "move_in_out": [
        (r"\bmove[- ]?(in|out)|\bmoving (in|out)", 4), (r"\bcheck[- ]?(in|out)\b", 3),
        (r"\barriv(e|al|ing)", 2), (r"\bcontract", 2), (r"\blease", 2), (r"\binspection", 3),
        (r"\btransfer\b", 2), (r"\bswitch rooms?|\bchange rooms?|\broom change", 3),
        (r"\bleav(e|ing) early|\bterminat", 3), (r"\binventory", 2),
    ],
    "general_enquiry": [
        (r"\bparcel|\bpackage|\bdelivery|\bpost\b", 3), (r"\bguest|\bvisitor|\bstay(ing)? over", 3),
        (r"\bfeedback|\bthank(s| you)\b|\bcompliment", 2), (r"\bopening hours|\bwhat time", 2),
        (r"\bevent(s)?\b|\bgym\b|\bstudy room booking", 2), (r"\bregister", 1),
    ],
    "safety_security": [
        (r"\bfire\b", 4), (r"\bsmoke alarm|\bfire alarm|\balarm", 3), (r"\bgas\b", 4),
        (r"\bintruder|\bstranger|\btailgat|\bbroke(n)? in|\bbreak[- ]?in", 4),
        (r"\binjur|\bhurt\b|\bbleeding|\bambulance|\bcollapsed", 4), (r"\bthreat", 4),
        (r"\bunsafe|\bdanger", 3), (r"\bcarbon monoxide|\bco alarm", 4), (r"\bstolen|\btheft", 3),
        (r"\bsmell of burning|\bburning smell", 4), (r"\bassault|\bharass", 4),
    ],
}

# Signals that make something urgent regardless of category.
P1_SIGNALS = [
    r"\bflood", r"\bwater (is )?(pouring|coming through)", r"\bgas\b", r"\bfire\b",
    r"\bsmoke\b", r"\bspark", r"\bburning", r"\binjur", r"\bbleeding", r"\bintruder",
    r"\bbroke(n)? in", r"\bthreat", r"\bassault", r"\block(ed)? out", r"\bcan'?t get in",
    r"\bcarbon monoxide", r"\bno power\b", r"\bcollapsed", r"\bemergency",
]
P2_SIGNALS = [
    r"\bno hot water", r"\bno heat", r"\bfreezing", r"\bnot working", r"\bbroken\b",
    r"\bwon'?t (work|flush|drain|turn on)", r"\bovercharg", r"\bcharged twice|\bdouble charg",
    r"\bno (wi-?fi|internet)", r"\btoday\b", r"\btonight\b", r"\burgent", r"\bleak",
    r"\bblocked\b", r"\ball night", r"\bevery night", r"\bexam",
]

SAFETY_SIGNALS = [
    r"\bgas\b", r"\bfire\b", r"\bsmoke\b", r"\bspark", r"\bburning", r"\binjur", r"\bbleeding",
    r"\bintruder", r"\bbroke(n)? in", r"\bthreat", r"\bassault", r"\bcarbon monoxide",
    r"\bcollapsed", r"\bharass", r"\bunsafe",
]


def _match_any(patterns: list[str], text: str) -> list[str]:
    return [p for p in patterns if re.search(p, text)]


def assign_priority(text: str, category: str) -> tuple[str, list[str]]:
    t = text.lower()
    p1 = _match_any(P1_SIGNALS, t)
    if p1 or category == "safety_security":
        return "P1", p1
    p2 = _match_any(P2_SIGNALS, t)
    if p2:
        return "P2", p2
    return "P3", []


class BaselineClassifier:
    name = "baseline-keywords-v1"

    def classify(self, text: str) -> Triage:
        t = text.lower()
        scores = {}
        for cat, rules in KEYWORDS.items():
            scores[cat] = sum(w for pat, w in rules if re.search(pat, t))
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        (best, s1), (_, s2) = ranked[0], ranked[1]
        if s1 == 0:
            category, confidence = "general_enquiry", 0.0   # default, always goes to full review
            rationale = "No category keywords matched."
        else:
            category = best
            # margin-based confidence: how far ahead the winner is
            confidence = round(min(1.0, (s1 - s2) / s1 * 0.6 + min(s1, 8) / 8 * 0.4), 2)
            rationale = f"Keyword score {s1} vs next best {s2}."
        safety_hits = _match_any(SAFETY_SIGNALS, t)
        if safety_hits and category != "safety_security" and scores["safety_security"] >= 4:
            category = "safety_security"
        priority, signals = assign_priority(text, category)
        return Triage(category, priority, confidence, rationale, self.name,
                      safety_flag=bool(safety_hits), signals=signals + safety_hits)


# --------------------------------------------------------------------------
# LLM classifier with structured output
# --------------------------------------------------------------------------

TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "priority": {"type": "string", "enum": list(PRIORITIES)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "safety_flag": {"type": "boolean"},
        "rationale": {"type": "string"},
    },
    "required": ["category", "priority", "confidence", "safety_flag", "rationale"],
}

SYSTEM_PROMPT = """You triage resident service requests for a residential building.
Return ONLY a JSON object with keys: category, priority, confidence, safety_flag, rationale.

Categories:
{categories}

Priorities:
{priorities}

Rules:
- safety_flag is true if there is any possible risk to a person (fire, gas, smoke,
  injury, intruder, threat, harassment). When in doubt, set it to true.
- confidence is your probability (0-1) that the category is correct.
- rationale is one short sentence. Do not repeat personal details.
"""


def _system_prompt() -> str:
    cats = "\n".join(f"- {c.key}: {c.description}" for c in CATEGORIES.values())
    pris = "\n".join(f"- {k}: {v['rule']}" for k, v in PRIORITIES.items())
    return SYSTEM_PROMPT.format(categories=cats, priorities=pris)


def validate(obj: dict) -> dict:
    """Minimal schema check without extra dependencies. Raises ValueError."""
    for key in TRIAGE_SCHEMA["required"]:
        if key not in obj:
            raise ValueError(f"missing {key}")
    if obj["category"] not in CATEGORIES:
        raise ValueError(f"bad category {obj['category']}")
    if obj["priority"] not in PRIORITIES:
        raise ValueError(f"bad priority {obj['priority']}")
    c = float(obj["confidence"])
    if not 0 <= c <= 1:
        raise ValueError("confidence out of range")
    obj["confidence"] = c
    obj["safety_flag"] = bool(obj["safety_flag"])
    return obj


class LLMClassifier:
    """Uses the Anthropic API if ANTHROPIC_API_KEY is set, else OpenAI if OPENAI_API_KEY is set.

    Any failure (no key, network, invalid JSON, schema violation) falls back to the
    baseline and is recorded in the rationale, so the pipeline never silently drops a request.
    """

    def __init__(self, model: str | None = None):
        self.fallback = BaselineClassifier()
        if os.getenv("ANTHROPIC_API_KEY"):
            self.provider, self.model = "anthropic", model or os.getenv("TRIAGE_MODEL", "claude-haiku-5-5")
        elif os.getenv("OPENAI_API_KEY"):
            self.provider, self.model = "openai", model or os.getenv("TRIAGE_MODEL", "gpt-4o-mini")
        else:
            self.provider, self.model = None, None
        self.name = f"llm-{self.provider}-{self.model}" if self.provider else "llm-unavailable"

    def _call(self, text: str) -> str:
        if self.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model=self.model, max_tokens=300, temperature=0,
                system=_system_prompt(),
                messages=[{"role": "user", "content": f"Request:\n{text}"}],
            )
            return msg.content[0].text
        if self.provider == "openai":
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model=self.model, temperature=0,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": _system_prompt()},
                          {"role": "user", "content": f"Request:\n{text}"}],
            )
            return resp.choices[0].message.content
        raise RuntimeError("no LLM provider configured")

    def classify(self, text: str) -> Triage:
        try:
            raw = self._call(text)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            obj = validate(json.loads(match.group(0) if match else raw))
            # Rule-based safety net: keyword safety signals can only ADD an escalation.
            safety = obj["safety_flag"] or bool(_match_any(SAFETY_SIGNALS, text.lower()))
            priority = "P1" if safety else obj["priority"]
            return Triage(obj["category"], priority, obj["confidence"], obj["rationale"],
                          self.name, safety_flag=safety)
        except Exception as exc:  # noqa: BLE001 - any failure must fall back, not crash
            result = self.fallback.classify(text)
            result.rationale = f"LLM fallback ({type(exc).__name__}). " + result.rationale
            result.model = f"{self.name}->fallback"
            return result
