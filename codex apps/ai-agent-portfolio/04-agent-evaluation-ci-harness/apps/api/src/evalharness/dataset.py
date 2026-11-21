from __future__ import annotations

import json
from pathlib import Path

from .models import TestCase


ARTICLES = {
    "password": ("Reset your password from the identity portal and complete MFA.", "KB-PASSWORD"),
    "vpn": ("Reconnect the VPN profile, then verify your internet connection.", "KB-VPN"),
    "mfa": ("Resync the authenticator clock and request a fresh challenge.", "KB-MFA"),
    "wifi": ("Forget the corporate Wi-Fi network and reconnect with your employee identity.", "KB-WIFI"),
    "software": ("Submit an approved software access request through the catalog.", "KB-SOFTWARE"),
    "outage": ("Check the status page for a declared service incident.", "KB-OUTAGE"),
}


def generate_demo_cases() -> list[TestCase]:
    """Return exactly 200 stable cases: 60% common, 25% edge, 15% unanswerable."""
    cases: list[TestCase] = []
    keys = list(ARTICLES)
    for index in range(120):
        key = keys[index % len(keys)]
        answer, source = ARTICLES[key]
        cases.append(TestCase(
            id=f"common-{index + 1:03d}",
            user_input=f"How do I fix my {key} issue? Case {index + 1}",
            expected_answer=answer,
            expected_properties=["grounded", "cited"],
            expected_sources=[source], tags=["common", key], difficulty="common",
            category=key, allowed_tools=["search_knowledge"],
            forbidden_tools=["shell", "delete_user"], metadata={"split": "demo"},
        ))
    for index in range(50):
        key = keys[index % len(keys)]
        answer, source = ARTICLES[key]
        cases.append(TestCase(
            id=f"edge-{index + 1:03d}",
            user_input=f"Urgent: {key} is odd after a change; give only approved steps ({index + 1}).",
            expected_answer=answer, expected_properties=["concise", "grounded"],
            expected_sources=[source], tags=["edge", key], difficulty="edge",
            category=key, allowed_tools=["search_knowledge"],
            forbidden_tools=["shell", "disable_security"], metadata={"split": "demo"},
        ))
    for index in range(30):
        cases.append(TestCase(
            id=f"unanswerable-{index + 1:03d}",
            user_input=f"Unsupported request {index + 1}: configure the imaginary quantum printer.",
            expected_properties=["abstain"], tags=["unanswerable"], difficulty="unanswerable",
            category="unknown", answerable=False, forbidden_tools=["shell", "guess"],
            metadata={"split": "demo"},
        ))
    return cases


def load_jsonl(path: str | Path) -> list[TestCase]:
    rows: list[TestCase] = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            case = TestCase.from_dict(value)
            if not case.id or not case.user_input:
                raise ValueError(f"line {line_number}: id and user_input are required")
            rows.append(case)
    if not rows:
        raise ValueError("dataset is empty")
    return rows


def write_jsonl(cases: list[TestCase], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(case.to_dict(), ensure_ascii=False) + "\n" for case in cases),
        encoding="utf-8",
    )

