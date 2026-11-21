"""Run the copilot eval: one command, per-question results, honest pass rate.

Live run (calls the Anthropic API, so it costs money):
    cd backend && uv run python ../eval/run_eval.py

Plumbing check (no API calls, no cost):
    cd backend && uv run python ../eval/run_eval.py --dry-run

--dry-run replaces Claude with a script that calls the expected tool and repeats the
expected facts. It only proves the questions, answer keys, tools and scorer are wired up.
It says nothing about copilot quality, so its result must never be quoted as a pass rate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from questions import Question, build_questions  # noqa: E402
from scorer import Score, score_answer  # noqa: E402

from app.copilot.agent import Copilot, LLMUnavailable  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.models import User  # noqa: E402
from app.db.session import session_factory  # noqa: E402
from app.services.scope import Scope  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"


class ScriptedPlumbingClient:
    """Stands in for Claude in --dry-run. Not a model, and not a measure of quality."""

    def __init__(self, question: Question, facts: list[str], arguments: dict) -> None:
        self.question = question
        self.facts = facts
        self.arguments = arguments
        self.step = 0

    @staticmethod
    def _reply(blocks: list, stop: str) -> SimpleNamespace:
        usage = SimpleNamespace(input_tokens=0, output_tokens=0)
        return SimpleNamespace(content=blocks, stop_reason=stop, usage=usage)

    def create(self, **kwargs):
        tools = self.question.expected_tools
        if self.step < len(tools):
            name = tools[self.step]
            self.step += 1
            block = SimpleNamespace(type="tool_use", name=name, id=f"dry_{self.step}",
                                    input=self.arguments.get(name, {}))
            return self._reply([block], "tool_use")
        kind = self.question.kind
        if kind == "refusal":
            answer = "I can only help with revenue questions."
        elif kind == "no_data":
            answer = "I don't have that data."
        elif kind == "scope":
            answer = "I cannot access that record."
        else:
            # Cite the first record the tool returned, as a well-behaved answer would.
            text = json.dumps(kwargs["messages"], default=str)
            seen = re.findall(r'cite\\*": \\*"([a-z_]+#\w+)', text)
            cite = f" [{seen[0]}]" if seen else ""
            answer = (" ".join(f.split("|")[0] for f in self.facts) or "See the source.") + cite
        block = SimpleNamespace(type="text", text=answer)
        return self._reply([block], "end_turn")


def dry_arguments(question: Question) -> dict:
    arguments: dict[str, dict] = {}
    deal = re.search(r"deal (\d+)", question.text)
    if deal:
        arguments["explain_deal"] = {"deal_id": int(deal.group(1))}
    arguments["search_tickets_and_notes"] = {"query": question.text}
    of = re.search(r"(?:of|does|for) ([A-Z][\w ]+?)(?: have|\?|,)", question.text)
    if of:
        arguments["get_account_360"] = {"account_name": of.group(1)}
    return arguments


def run_question(session, question: Question, dry_run: bool) -> tuple[Score, dict]:
    user = session.get(User, question.user_id)
    scope = Scope(user_id=user.id, role=user.role, team_id=user.team_id)
    team = user.team.name if user.team else None
    facts = question.facts(session) if question.facts else []
    client = ScriptedPlumbingClient(question, facts, dry_arguments(question)) if dry_run else None
    result = Copilot(session, scope, team, client=client).ask(question.text)
    tools = [t["name"] for t in result.tools_called]
    score = score_answer(
        question.id, question.kind, result.answer, question.expected_tools, tools, facts,
        result.citations, result.invalid_citations, result.ungrounded_numbers, question.forbidden,
    )
    detail = {
        "id": question.id, "kind": question.kind, "question": question.text,
        "answer": result.answer, "tools": tools, "citations": result.citations,
        "passed": score.passed, "checks": score.checks, "notes": score.notes,
        "latency_ms": result.latency_ms, "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }
    return score, detail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="No API calls. Plumbing only.")
    parser.add_argument("--only", help="Comma-separated question ids to run.")
    args = parser.parse_args()

    settings = get_settings()
    if not args.dry_run and not settings.anthropic_api_key:
        print("NOT RUN: ANTHROPIC_API_KEY is not set. Use --dry-run to test the plumbing only.")
        return 2

    with session_factory()() as session:
        questions = build_questions(session)
        if args.only:
            wanted = set(args.only.split(","))
            questions = [q for q in questions if q.id in wanted]
        details: list[dict] = []
        for question in questions:
            try:
                score, detail = run_question(session, question, args.dry_run)
            except LLMUnavailable as error:
                print(f"NOT RUN: {error}")
                return 2
            details.append(detail)
            mark = "PASS" if score.passed else "FAIL"
            print(f"{mark} {question.id} [{question.kind:9s}] {question.text[:70]}")
            for note in score.notes:
                print(f"       - {note}")
        session.rollback()

    passed = sum(d["passed"] for d in details)
    label = "PLUMBING CHECK (not a quality score)" if args.dry_run else "LIVE EVAL"
    print(f"\n{label}: {passed}/{len(details)} passed")
    if not args.dry_run:
        tokens_in = sum(d["input_tokens"] for d in details)
        tokens_out = sum(d["output_tokens"] for d in details)
        print(f"Model {settings.llm_model}. Tokens in {tokens_in:,}, out {tokens_out:,}.")

    RESULTS_DIR.mkdir(exist_ok=True)
    name = "dry_run.json" if args.dry_run else "latest.json"
    (RESULTS_DIR / name).write_text(json.dumps({
        "run_at": datetime.now(UTC).isoformat(), "dry_run": args.dry_run,
        "model": None if args.dry_run else settings.llm_model,
        "passed": passed, "total": len(details), "questions": details,
    }, indent=2))
    return 0 if passed == len(details) else 1


if __name__ == "__main__":
    raise SystemExit(main())
