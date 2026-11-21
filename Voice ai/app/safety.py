"""Operations-only guard rails: text we generate must not contain clinical judgement or advice."""
from __future__ import annotations

import re

# Words that signal diagnosis, urgency/triage, reassurance or medication advice. Deliberately blunt.
CLINICAL_RE = re.compile(
    r"\b(diagnos\w*|urgent\w*|emergenc\w*|critical\w*|serious\w*|severe\w*|life[- ]threatening|sepsis|infect\w*|"
    r"prescri\w*|dosage|dose|medicat\w*|antibiotic\w*|stop taking|start taking|"
    r"is fine|are fine|no concern\w*|nothing to worry|safe|case closed|close the case|all clear|"
    r"go to (the )?(er|a&e|hospital)|call 911|call 999)\b",
    re.IGNORECASE,
)
PATIENT_ID_RE = re.compile(r"\bpat-\d{4}\b")


def clinical_terms(text: str) -> list[str]:
    return sorted({m.group(0).lower() for m in CLINICAL_RE.finditer(text)})


def foreign_patient_ids(text: str, own_id: str | None) -> list[str]:
    return sorted({m for m in PATIENT_ID_RE.findall(text) if m != own_id})


def wrap_untrusted(label: str, text: str) -> str:
    """Wrap patient-written text so the model can see it is data. Closing tags inside are neutralised."""
    safe = text.replace("</untrusted_patient_text>", "[/untrusted_patient_text removed]")
    return f'<untrusted_patient_text field="{label}">\n{safe}\n</untrusted_patient_text>'
