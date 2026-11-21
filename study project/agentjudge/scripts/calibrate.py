"""Print Cohen's kappa between human labels and a run's judge scores."""

import sys

from agentjudge.calibration import calibrate

HUMAN = "labels/human_20.jsonl"


def main(run: str = "", human: str = HUMAN) -> None:
    if not run:
        raise SystemExit("usage: calibrate.py <run.json> [--human labels/human_20.jsonl]")
    result = calibrate(human, run)
    print(f"n={result['n']} kappa={float(result['kappa']):.3f}")
    print(f"human={result['human']}")
    print(f"judge={result['judge']}")


if __name__ == "__main__":
    cli = sys.argv[1:]
    human = HUMAN
    if "--human" in cli:
        i = cli.index("--human")
        human = cli[i + 1]
        del cli[i : i + 2]
    print("mock judge (offline, no API keys).", file=sys.stderr)
    main(cli[0] if cli else "", human)
