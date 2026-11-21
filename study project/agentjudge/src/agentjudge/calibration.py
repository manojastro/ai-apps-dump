"""Calibration: agreement between human labels and the judge (Cohen's kappa)."""

from pathlib import Path

from agentjudge.judge import cohens_kappa


def load_labels(path: str | Path) -> tuple[list[str], list[int]]:
    """Load labels/human_20.jsonl -> (ids, human correctness scores)."""
    import json

    ids: list[str] = []
    scores: list[int] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        ids.append(str(row["id"]))
        scores.append(int(row["human_correctness"]))
    return ids, scores


def judge_scores_for_ids(run_path: str | Path, ids: list[str]) -> list[int]:
    """Pull judge correctness scores for ids out of a run JSON report."""
    import json

    data = json.loads(Path(run_path).read_text(encoding="utf-8"))
    by_id = {r["id"]: int(r["judge_correctness"]) for r in data.get("records", [])}
    return [by_id[i] for i in ids]


def calibrate(human_path: str | Path, run_path: str | Path) -> dict[str, object]:
    """Return {"n", "kappa", "human", "judge"} for the labelled subset."""
    ids, human = load_labels(human_path)
    judge = judge_scores_for_ids(run_path, ids)
    return {"n": len(ids), "kappa": cohens_kappa(human, judge), "human": human, "judge": judge}
