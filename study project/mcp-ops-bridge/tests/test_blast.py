"""blast_radius BFS tests."""

import pytest

from mock_itsm.blast import blast_radius
from mock_itsm.db import connect


def test_blast_firewall_includes_vpn(db_path: str) -> None:
    conn = connect(db_path)
    try:
        out = blast_radius(conn, "fw-edge-01", 1)
        affected = list(out["affected"])  # type: ignore[typeddict-item]
        assert "vpn-gateway-01" in affected
        assert "vpn-gateway-02" in affected
    finally:
        conn.close()


def test_blast_orders_db_depth2(db_path: str) -> None:
    conn = connect(db_path)
    try:
        out = blast_radius(conn, "orders-db-01", 2)
        affected = set(out["affected"])  # type: ignore[typeddict-item]
        assert {"orders-app-01", "orders-app-02", "search-idx-01"} <= affected
    finally:
        conn.close()


def test_blast_depth1_smaller_than_depth2(db_path: str) -> None:
    conn = connect(db_path)
    try:
        d1 = set(blast_radius(conn, "k8s-cluster-01", 1)["affected"])  # type: ignore[typeddict-item]
        d2 = set(blast_radius(conn, "k8s-cluster-01", 3)["affected"])  # type: ignore[typeddict-item]
        assert d1 <= d2
    finally:
        conn.close()


def test_blast_unknown_ci(db_path: str) -> None:
    conn = connect(db_path)
    try:
        with pytest.raises(ValueError):
            blast_radius(conn, "nope-01", 2)
        with pytest.raises(ValueError):
            blast_radius(conn, "fw-edge-01", 0)
    finally:
        conn.close()
