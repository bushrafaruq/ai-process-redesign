"""PII redaction applied BEFORE any text is sent to a model or written to the audit log.

Pattern-based and deliberately conservative. It catches structured identifiers
(emails, phone numbers, card numbers, IBANs, Eircodes). It does NOT reliably catch
personal names in free text; that limitation is recorded in docs/05_evaluation.md.
"""

import re

_PATTERNS = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,3})?\b")),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("PHONE", re.compile(r"(?:\+353|\b0)\s?\(?\d{1,2}\)?[\s-]?\d{3}[\s-]?\d{3,4}\b")),
    ("EIRCODE", re.compile(r"\b[AC-FHKNPRTV-Y]\d{2}\s?[AC-FHKNPRTV-Y0-9]{4}\b", re.IGNORECASE)),
]


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Return (redacted_text, counts_by_type)."""
    counts: dict[str, int] = {}
    for label, pattern in _PATTERNS:
        text, n = pattern.subn(f"[{label}]", text)
        if n:
            counts[label] = counts.get(label, 0) + n
    return text, counts
