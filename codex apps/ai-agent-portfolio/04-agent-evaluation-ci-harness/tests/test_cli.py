import json

from evalharness.cli import main


def test_cli_run_report_and_gate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'cli.db'}")
    assert main(["seed"]) == 0
    assert main(["run", "--mode", "good", "--limit", "5", "--output", "good.json"]) == 0
    assert main(["report", "--run", "good.json", "--output", "report.md"]) == 0
    config = tmp_path / "gates.yml"
    config.write_text("absolute_thresholds:\n  task_success: 0.9\n", encoding="utf-8")
    assert main(["gate", "--candidate", "good.json", "--config", str(config)]) == 0
    value = json.loads((tmp_path / "good.json").read_text())
    assert value["aggregate"]["sample_count"] == 5
    assert "Aggregate metrics" in (tmp_path / "report.md").read_text()

