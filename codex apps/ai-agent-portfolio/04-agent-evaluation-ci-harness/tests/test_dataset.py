from evalharness.dataset import generate_demo_cases, load_jsonl, write_jsonl


def test_demo_dataset_has_required_distribution(tmp_path):
    cases = generate_demo_cases()
    assert len(cases) == 200
    assert sum(case.difficulty == "common" for case in cases) == 120
    assert sum(case.difficulty == "edge" for case in cases) == 50
    assert sum(not case.answerable for case in cases) == 30
    assert all(case.forbidden_tools for case in cases)
    path = tmp_path / "cases.jsonl"
    write_jsonl(cases, path)
    assert load_jsonl(path) == cases


def test_import_rejects_missing_required_fields(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"id":"case"}\n', encoding="utf-8")
    try:
        load_jsonl(path)
    except ValueError as exc:
        assert "user_input" in str(exc)
    else:
        raise AssertionError("invalid dataset accepted")

