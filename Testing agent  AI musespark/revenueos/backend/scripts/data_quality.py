"""Data-quality checks: duplicates, nulls, orphans, stale open deals, impossible dates.

Checks run on the raw connector output, before the loader, because the database's
foreign keys would otherwise hide orphans. The summary is saved so the Admin page can
show the last result.

Run: uv run python -m scripts.data_quality
"""
from __future__ import annotations

import re
from datetime import date, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from app.connectors.base import Connector
from app.connectors.synthetic import SyntheticCsvConnector
from app.core.config import get_settings
from app.db.models import DataQualityRun
from app.db.session import get_engine

STALE_DAYS = 60
_LEGAL_SUFFIX = re.compile(r"[,\s]+(inc\.?|llc|ltd\.?|corp\.?)\s*$", re.IGNORECASE)

REQUIRED_FIELDS = {
    "accounts": ["industry", "owner_id"],
    "contacts": ["title"],
    "deals": ["source", "discount_pct", "close_date"],
}


def normalise_name(name: str) -> str:
    return _LEGAL_SUFFIX.sub("", name).strip().lower()


def find_duplicates(accounts: pd.DataFrame) -> list[list[int]]:
    """Group accounts that share a domain or a normalised company name."""
    frame = accounts.assign(key=accounts["name"].map(normalise_name))
    groups: list[list[int]] = []
    for column in ("domain", "key"):
        for _, group in frame.dropna(subset=[column]).groupby(column):
            ids = sorted(group["id"].astype(int).tolist())
            if len(ids) > 1 and ids not in groups:
                groups.append(ids)
    return groups


def find_nulls(frames: dict[str, pd.DataFrame]) -> dict[str, int]:
    return {
        f"{table}.{column}": int(frames[table][column].isna().sum())
        for table, columns in REQUIRED_FIELDS.items()
        for column in columns
    }


def find_orphans(frames: dict[str, pd.DataFrame]) -> dict[str, list[int]]:
    checks = [
        ("tickets", "account_id", "accounts"),
        ("activities", "contact_id", "contacts"),
        ("activities", "deal_id", "deals"),
        ("deals", "account_id", "accounts"),
        ("contacts", "account_id", "accounts"),
        ("invoices", "account_id", "accounts"),
    ]
    found: dict[str, list[int]] = {}
    for child, column, parent in checks:
        frame = frames[child]
        bad = frame[frame[column].notna() & ~frame[column].isin(frames[parent]["id"])]
        found[f"{child}.{column}"] = sorted(bad["id"].astype(int).tolist())
    return found


def find_stale_deals(frames: dict[str, pd.DataFrame], as_of: date) -> list[int]:
    """Open deals past their close date with no activity in the last STALE_DAYS."""
    deals = frames["deals"]
    opened = deals[deals["outcome"].isna()].copy()
    opened["close_date"] = pd.to_datetime(opened["close_date"])
    activity = frames["activities"].copy()
    activity["occurred_at"] = pd.to_datetime(activity["occurred_at"])
    last_touch = activity.groupby("deal_id")["occurred_at"].max()
    opened["last_touch"] = opened["id"].map(last_touch)
    cutoff = pd.Timestamp(as_of - timedelta(days=STALE_DAYS))
    stale = opened[(opened["close_date"] < pd.Timestamp(as_of))
                   & (opened["last_touch"].isna() | (opened["last_touch"] < cutoff))]
    return sorted(stale["id"].astype(int).tolist())


def find_impossible_dates(frames: dict[str, pd.DataFrame], as_of: date) -> dict[str, list[int]]:
    deals, tickets = frames["deals"], frames["tickets"]
    created = pd.to_datetime(deals["created_at"])
    closed = pd.to_datetime(deals["closed_at"])
    opened = pd.to_datetime(tickets["opened_at"])
    resolved = pd.to_datetime(tickets["resolved_at"])
    return {
        "deals.closed_before_created": sorted(deals[closed < created]["id"].astype(int).tolist()),
        "deals.created_in_future": sorted(
            deals[created > pd.Timestamp(as_of)]["id"].astype(int).tolist()
        ),
        "tickets.resolved_before_opened": sorted(
            tickets[resolved < opened]["id"].astype(int).tolist()
        ),
    }


def run_checks(connector: Connector, as_of: date) -> dict:
    frames = connector.fetch_all()
    duplicates = find_duplicates(frames["accounts"])
    nulls = find_nulls(frames)
    orphans = find_orphans(frames)
    stale = find_stale_deals(frames, as_of)
    impossible = find_impossible_dates(frames, as_of)
    return {
        "as_of": as_of.isoformat(),
        "row_counts": {name: len(frame) for name, frame in frames.items()},
        "duplicates": duplicates,
        "nulls": nulls,
        "orphans": orphans,
        "stale_open_deals": stale,
        "impossible_dates": impossible,
        "summary": {
            "duplicate_groups": len(duplicates),
            "null_values": sum(nulls.values()),
            "orphan_rows": sum(len(v) for v in orphans.values()),
            "stale_open_deals": len(stale),
            "impossible_dates": sum(len(v) for v in impossible.values()),
        },
    }


def print_report(results: dict) -> None:
    print(f"DATA QUALITY REPORT (as of {results['as_of']})")
    print("-" * 56)
    for key, value in results["summary"].items():
        print(f"{key:28s} {value:>6,}")
    print("\nNulls by field:")
    for key, value in results["nulls"].items():
        print(f"  {key:26s} {value:>6,}")
    print("\nOrphans by relation:")
    for key, value in results["orphans"].items():
        print(f"  {key:26s} {len(value):>6,}")
    print("\nImpossible dates:")
    for key, value in results["impossible_dates"].items():
        print(f"  {key:32s} {len(value):>6,}")
    print(f"\nDuplicate account groups: {results['duplicates']}")
    print(f"Stale open deals: {results['stale_open_deals']}")


def save(results: dict) -> None:
    with Session(get_engine()) as session:
        session.add(DataQualityRun(results_json=results))
        session.commit()


def main() -> None:
    settings = get_settings()
    results = run_checks(SyntheticCsvConnector(settings.data_dir), settings.data_as_of)
    print_report(results)
    save(results)


if __name__ == "__main__":
    main()
