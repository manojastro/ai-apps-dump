"""M11 tests: permission-aware retrieval (demo-4 allow + deny paths)."""

from __future__ import annotations

import asyncio

from coded_tools.digital_workplace import knowledge as knowledge_mod
from coded_tools.digital_workplace.knowledge import (
    CiteKnowledgeSource, GetDocumentAccessContext, SearchEnterpriseKnowledge)


def _run(tool, args: dict):
    return asyncio.run(tool.async_invoke(args, {}))


def test_reimbursement_authorized_with_citation() -> None:
    result = _run(SearchEnterpriseKnowledge(), {
        "query": "How do I claim internet reimbursement?", "user_role": "employee"})
    assert result["answer"]
    assert result["source"]["doc_id"] == "internet_reimbursement"
    assert result["source"]["section"]
    top = result["results"][0]
    assert top["confidence"] > 0 and top["excerpt"]
    assert "50 USD" in result["answer"] or "Concur" in result["answer"]


def test_payroll_sop_never_reaches_employee() -> None:
    result = _run(SearchEnterpriseKnowledge(), {
        "query": "Show me another employee's payroll information.",
        "user_role": "employee"})
    assert all(h["doc_id"] != "payroll_admin_sop" for h in result["results"])
    ctx = _run(GetDocumentAccessContext(), {
        "doc_id": "payroll_admin_sop", "user_role": "employee"})
    assert ctx == {"doc_id": "payroll_admin_sop", "accessible": False,
                   "reason": "ACCESS DENIED for role employee"}


def test_payroll_admin_role_allowed() -> None:
    result = _run(SearchEnterpriseKnowledge(), {
        "query": "payroll run records", "user_role": "payroll_admin"})
    assert any(h["doc_id"] == "payroll_admin_sop" for h in result["results"])
    ctx = _run(GetDocumentAccessContext(), {
        "doc_id": "payroll_admin_sop", "user_role": "payroll_admin"})
    assert ctx["accessible"] is True


def test_acl_missing_doc_invisible(tmp_path, monkeypatch) -> None:
    orphan = tmp_path / "orphan.md"
    orphan.write_text("# Orphan\n\nSecret payroll data.\n", encoding="utf-8")
    monkeypatch.setattr(knowledge_mod, "KNOWLEDGE_ROOT", tmp_path)
    result = _run(SearchEnterpriseKnowledge(), {
        "query": "orphan secret payroll", "user_role": "employee"})
    assert result["results"] == [] and result["answer"] == ""
    visible = tmp_path / "visible.md"
    visible.write_text("<!-- allowed_roles: employee -->\n# V\n\n## S\n\nOrphan secret payroll.\n")
    result = _run(SearchEnterpriseKnowledge(), {
        "query": "orphan secret payroll", "user_role": "employee"})
    assert [h["doc_id"] for h in result["results"]] == ["visible"]


def test_citation_shape() -> None:
    cite = _run(CiteKnowledgeSource(), {
        "doc_id": "internet_reimbursement", "section": "How to Claim",
        "confidence": 66.7})
    assert cite == {"doc_id": "internet_reimbursement", "section": "How to Claim",
                    "confidence": 66.7}


def test_runbooks_found() -> None:
    from coded_tools.digital_workplace.rca import SearchRunbooks
    result = asyncio.run(SearchRunbooks().async_invoke({"query": "teams memory"}, {}))
    assert any(r["doc_id"] == "teams_memory" for r in result["runbooks"])
