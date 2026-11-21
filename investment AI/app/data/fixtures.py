from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.facts import SourceRecord, SourcedValue
from app.models.plan import Candidate, MarketSnapshot


def mock_candidates() -> list[Candidate]:
    as_of = "mock-fixture"
    common = dict(as_of=as_of, verification="verified", mock=True, source_ids=["src-amfi", "src-sebi"])
    return [
        Candidate(
            name="Overnight / liquid mutual fund (class)",
            category="cash_safety",
            vehicle_type="liquid_fund",
            role_in_portfolio="Emergency reserve and near-term cash",
            risks=["inflation erosion", "credit events in underlying (low but not zero)"],
            liquidity="T+1 typical for liquid funds; confirm scheme documents",
            tax_notes="Tax treatment follows the current snapshot; not a reason to choose the class alone.",
            **common,
        ),
        Candidate(
            name="Bank / India Post small-savings instruments (class)",
            category="cash_safety",
            vehicle_type="small_savings",
            role_in_portfolio="Capital stability sleeve",
            risks=["reinvestment risk", "rate changes"],
            liquidity="Varies; some lock-ins (PPF, NSC, KVP)",
            tax_notes="PPF EEE historically; confirm current snapshot.",
            **common,
        ),
        Candidate(
            name="Gilt / high-quality debt fund (class)",
            category="fixed_income",
            vehicle_type="gilt",
            role_in_portfolio="Duration and sovereign-quality debt",
            risks=["interest-rate volatility"],
            liquidity="Mutual-fund liquidity; not a bank deposit",
            tax_notes="Debt-fund tax rules are snapshot-backed.",
            **common,
        ),
        Candidate(
            name="Corporate bond / short-duration fund (class)",
            category="fixed_income",
            vehicle_type="corporate_bond",
            role_in_portfolio="Income sleeve; no low-quality speculative NCD",
            risks=["credit spread", "rate risk"],
            liquidity="Mutual-fund liquidity",
            tax_notes="See snapshot.",
            **common,
        ),
        Candidate(
            name="Broad-market Indian index fund / ETF (class)",
            category="equity",
            vehicle_type="index_fund",
            role_in_portfolio="Default equity engine for simulations",
            risks=["market drawdowns of 20%+ are normal historically"],
            liquidity="High for open-end index funds/ETFs",
            tax_notes="Equity tax rules are snapshot-backed. ELSS only if old-regime circumstances fit.",
            **common,
        ),
        Candidate(
            name="Large-cap / flexi-cap regulated mutual fund (class)",
            category="equity",
            vehicle_type="flexi_cap",
            role_in_portfolio="Active or style complement; still a class, not a tip",
            risks=["manager risk", "market risk"],
            liquidity="High",
            tax_notes="See snapshot.",
            **common,
        ),
        Candidate(
            name="Gold ETF / gold FoF (class)",
            category="gold",
            vehicle_type="gold_etf",
            role_in_portfolio="Diversifier. Jewellery is consumption.",
            risks=["price volatility", "no yield"],
            liquidity="High for ETFs",
            tax_notes="See snapshot. SGB issuance must be checked; do not assume new SGB exists.",
            **common,
        ),
        Candidate(
            name="India-domiciled international fund (class)",
            category="international",
            vehicle_type="international_fund",
            role_in_portfolio="Optional diversifier only if the household opts in",
            risks=["currency", "foreign-market", "LRS/TCS if direct overseas"],
            liquidity="Fund-dependent",
            tax_notes="LRS, TCS and tax from RegulatorySnapshot.",
            source_ids=["src-rbi", "src-amfi"],
            as_of=as_of,
            verification="verified",
            mock=True,
        ),
        Candidate(
            name="Listed REIT (class, educational)",
            category="real_assets",
            vehicle_type="reit",
            role_in_portfolio="Listed real-asset sleeve; never a specific project or developer",
            risks=["rate sensitivity", "occupancy"],
            liquidity="Exchange-traded; still not cash",
            tax_notes="See snapshot.",
            **common,
        ),
    ]


def mock_market_snapshot() -> MarketSnapshot:
    now = datetime.now(timezone.utc)
    return MarketSnapshot(
        snapshot_id=f"mkt-{uuid4().hex[:12]}",
        generated_at=now,
        macro_state="neutral",
        notes=[
            "Mock macro state is educational and is not market timing.",
            "No live index level is claimed.",
            "DEGRADED_DATA: fixture, not a live scrape.",
        ],
        observations={
            "broad_index": SourcedValue(
                value=None,
                unit="",
                source_url="https://www.nseindia.com/",
                source_tier=1,
                fetched_at=now,
                as_of="mock-fixture",
                confidence="low",
                verification="unverified",
                mock=True,
                notes="No fabricated index level.",
            )
        },
        sources=[
            SourceRecord(
                source_id="src-nse",
                title="NSE",
                url="https://www.nseindia.com/",
                authority="NSE",
                fetched_at=now,
                as_of="mock-fixture",
                verification="unverified",
                mock=True,
                affected_facts=["broad_index"],
            )
        ],
        degraded=True,
        data_mode="mock",
        stale=False,
    )
