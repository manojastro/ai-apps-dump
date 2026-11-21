"""Evaluation over the synthetic ground-truth fixtures.

    uv run python -m eval.run_eval              # digital + xlsx fixtures (fast)
    uv run python -m eval.run_eval --ocr        # also the scanned fixture (slow, local OCR)

Resets the TEST database, processes each fixture through the real API + workflow (demo mode), answers
metadata questions from ground truth (counted as analyst interventions) and reports each metric
separately. Exit code 1 when a threshold in eval/thresholds.yaml is not met.

How tests detect invented or incorrectly mapped values:
  * every numeric observation's raw text must occur in the extracted source text of its page/sheet
    (otherwise it is counted as an invented value);
  * cells that ground truth marks unreadable/ambiguous must NOT carry a number;
  * each row's canonical code is compared with ground truth, including rows that must stay unmapped.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from decimal import Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SCALE = {"units": 1, "thousands": 10**3, "lakhs": 10**5, "millions": 10**6, "crores": 10**7}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def setup_env() -> None:
    import psycopg

    from tests.conftest import _test_db_url

    url = _test_db_url().rsplit("/", 1)[0] + "/spreadlens_eval"  # separate database: never touches dev or test data
    with psycopg.connect(url.replace("postgresql+psycopg://", "postgresql://").rsplit("/", 1)[0] + "/postgres", autocommit=True) as c:
        if not c.execute("select 1 from pg_database where datname='spreadlens_eval'").fetchone():
            c.execute("create database spreadlens_eval")
    os.environ.update({"SPREADLENS_ENV": "test", "SPREADLENS_DATABASE_URL": url, "SPREADLENS_AGENT_MODE": "demo",
                       "SPREADLENS_RUN_WORKER_IN_API": "false", "SPREADLENS_SEED_PASSWORD": "eval-pass-123",
                       "SPREADLENS_STORAGE_ROOT": str(ROOT / "data" / "eval-files")})


def reset_db() -> dict:
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from spreadlens.db import get_engine, session_scope
    from spreadlens.seed import seed

    with get_engine().begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", os.environ["SPREADLENS_DATABASE_URL"])
    command.upgrade(cfg, "head")
    with session_scope() as db:
        return seed(db)


def main(include_ocr: bool = False, only: list[str] | None = None) -> dict:
    setup_env()
    ws_ids = reset_db()
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    from spreadlens.config import get_settings
    from spreadlens.db import session_scope
    from spreadlens.main import app
    from spreadlens.models import Artifact, CalculationResult, MappingProposal, Observation, Spread, WorkflowRun
    from spreadlens.workflow.worker import Worker

    manifest = json.loads((ROOT / "fixtures" / "ground_truth" / "manifest.json").read_text())
    thresholds = yaml.safe_load((ROOT / "eval" / "thresholds.yaml").read_text())
    agg = {k: [0, 0] for k in ("numeric", "assoc", "unitsign", "mapping", "citation")}
    tp = fp = fn = 0
    invented = numeric_total = 0
    interventions = obs_total = 0
    per_fixture = []
    with TestClient(app) as c:
        h = {"authorization": "Bearer " + c.post("/api/auth/login", json={"email": "analyst@demo.local", "password": "eval-pass-123"}).json()["token"]}
        for fx in manifest["fixtures"]:
            name = fx["file"]
            if only and not any(o in name for o in only):
                continue
            if fx["kind"] == "pdf_scanned" and not include_ocr:
                continue
            t0 = time.monotonic()
            cid = c.post(f"/api/workspaces/{ws_ids['Demo Credit Team']}/companies", headers=h, json={"name": f"eval {name}"}).json()["id"]
            files = [name] + (["01_aravalli_fy25_standalone.pdf"] if "restated" in name else [])
            ups = []
            for f in files:
                media = "application/pdf" if f.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                with open(ROOT / "fixtures" / "documents" / f, "rb") as fh:
                    ups.append(c.post(f"/api/companies/{cid}/documents", headers=h, files={"file": (f, fh, media)}).json())
            Worker(get_settings()).drain()
            for u in ups:  # answer questions from ground truth (counted as interventions)
                d = c.get(f"/api/documents/{u['document_version_id']}", headers=h).json()
                for q in d["questions"]:
                    ans = {"scope": fx.get("scope") if fx.get("scope") in ("standalone", "consolidated") else "standalone",
                           "scale": fx.get("scale") or "crores", "currency": fx.get("currency") or "INR"}.get(q["field"])
                    if ans:
                        c.post(f"/api/questions/{q['id']}/answer", headers=h, json={"answer": ans})
                        interventions += 1
            Worker(get_settings()).drain()
            elapsed = time.monotonic() - t0
            dv_ids = {u["document_version_id"] for u in ups}
            main_dv = ups[0]["document_version_id"]
            with session_scope() as db:
                obs = list(db.scalars(select(Observation).where(Observation.document_version_id.in_(dv_ids))))
                main_obs = [o for o in obs if o.document_version_id == main_dv]
                raw = {}
                run = db.scalar(select(WorkflowRun).where(WorkflowRun.document_version_id == main_dv))
                for a in db.scalars(select(Artifact).where(Artifact.run_id == run.id, Artifact.artifact_type == "raw_extraction")):
                    raw = a.payload
                texts = {p.get("page") or p.get("sheet"): p["text"] for p in raw.get("page_texts", [])}
                alltext = "\n".join(texts.values())
                obs_total += len(main_obs)
                # citations
                wb = None
                if name.endswith(".xlsx"):
                    from openpyxl import load_workbook

                    wb = load_workbook(ROOT / "fixtures" / "documents" / name, data_only=True)
                for o in main_obs:
                    agg["citation"][1] += 1
                    agg["citation"][0] += bool((o.page and o.bbox) or (o.sheet and o.cell_ref))
                    if o.value_state in ("value", "zero"):
                        numeric_total += 1
                        if wb is not None:
                            # spreadsheet: the number must equal the actual worksheet cell
                            v = wb[o.sheet][o.cell_ref].value if o.sheet in wb.sheetnames else None
                            if v is None or Decimal(repr(v) if isinstance(v, float) else str(v)) != o.parsed_value:
                                invented += 1
                        elif o.raw_text not in alltext:
                            invented += 1
                for st in fx.get("expected_states", []):
                    hit = [o for o in main_obs if o.canonical_code == st["code"] and o.period_end.isoformat() == st["period_end"]]
                    if any(o.value_state in ("value", "zero") for o in hit):
                        invented += 1
                    numeric_total += 1
                # numeric / association / unit-sign (by label + period, independent of mapping)
                for g in fx.get("expected", []):
                    if g["scope"] not in ("standalone", "consolidated"):
                        continue
                    agg["assoc"][1] += 1
                    cands = [o for o in main_obs if _norm(o.original_label) == _norm(g["label"]) and o.period_end.isoformat() == g["period_end"]
                             and o.scope == g["scope"] and o.statement_type == g["statement_type"]]
                    exp = Decimal(g["value"])
                    if cands:
                        agg["numeric"][1] += 1
                        agg["unitsign"][1] += 1
                        ok_num = any(o.parsed_value is not None and o.parsed_value == exp for o in cands)
                        agg["numeric"][0] += ok_num
                        agg["assoc"][0] += ok_num
                        factor = 1 if g["code"].startswith("is.eps") else SCALE[g["scale"]]
                        agg["unitsign"][0] += any(o.normalized_value is not None and o.normalized_value == exp * factor for o in cands)
                # mapping (rows listed in ground truth, including expected-unmapped)
                props = {}
                for o in main_obs:
                    p = db.scalar(select(MappingProposal).where(MappingProposal.row_id == o.row_id, MappingProposal.is_current.is_(True)))
                    props[(o.statement_type, _norm(o.original_label), o.row_id)] = (p.decided_code or p.proposed_code) if p else None
                for row in fx.get("rows", []):
                    matches = [v for (st, lbl, _), v in props.items() if st == row["statement_type"] and lbl == _norm(row["label"])]
                    if not matches:
                        continue
                    agg["mapping"][1] += 1
                    agg["mapping"][0] += row["expected_code"] in matches
                # validation precision / recall
                spreads = {o.spread_id for o in main_obs}
                fails = []
                for sid in spreads:
                    sp = db.get(Spread, sid)
                    for cr in db.scalars(select(CalculationResult).where(CalculationResult.spread_id == sid, CalculationResult.kind == "validation",
                                                                         CalculationResult.spread_version_no == sp.current_version_no,
                                                                         CalculationResult.status == "fail")):
                        fails.append((cr.rule_id, cr.period_end.isoformat() if cr.period_end else None, cr.statement_type))
                expected = [(e["rule"], e["period_end"], e["statement_type"]) for e in fx.get("expected_rule_failures", [])]
                tp_f = sum(1 for e in expected if e in fails)
                tp += tp_f
                fn += len(expected) - tp_f
                fp += sum(1 for f in fails if f not in expected)
            per_fixture.append({"fixture": name, "seconds": round(elapsed, 2), "observations": len(main_obs), "validation_failures": len(fails)})

    def ratio(k: str) -> float:
        n, d = agg[k]
        return round(n / d, 4) if d else 1.0

    metrics = {
        "numeric_extraction_accuracy": ratio("numeric"),
        "row_period_association_accuracy": ratio("assoc"),
        "unit_sign_accuracy": ratio("unitsign"),
        "mapping_accuracy": ratio("mapping"),
        "source_citation_coverage": ratio("citation"),
        "validation_precision": round(tp / (tp + fp), 4) if tp + fp else 1.0,
        "validation_recall": round(tp / (tp + fn), 4) if tp + fn else 1.0,
        "unsupported_value_invention_rate": round(invented / numeric_total, 4) if numeric_total else 0.0,
        "analyst_intervention_rate": round(interventions / obs_total, 4) if obs_total else 0.0,
        "cost_usd": 0.0,
        "mode": "demo (deterministic adapters; no model calls)",
    }
    counts = {k: {"correct": v[0], "total": v[1]} for k, v in agg.items()}
    failures = []
    for k, th in thresholds.items():
        if k == "max_seconds_per_digital_document":
            slow = [f for f in per_fixture if f["seconds"] > th and "scanned" not in f["fixture"]]
            if slow:
                failures.append(f"latency: {slow}")
        elif k == "unsupported_value_invention_rate":
            if metrics[k] > th:
                failures.append(f"{k}={metrics[k]} > {th}")
        elif metrics[k] < th:
            failures.append(f"{k}={metrics[k]} < {th}")
    report = {"disclaimer": manifest["disclaimer"], "metrics": metrics, "counts": counts, "validation": {"tp": tp, "fp": fp, "fn": fn},
              "fixtures": per_fixture, "threshold_failures": failures}
    out = ROOT / "eval" / "last_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    rep = main(include_ocr="--ocr" in sys.argv)
    print(json.dumps({"metrics": rep["metrics"], "counts": rep["counts"], "validation": rep["validation"],
                      "threshold_failures": rep["threshold_failures"]}, indent=2))
    sys.exit(1 if rep["threshold_failures"] else 0)
