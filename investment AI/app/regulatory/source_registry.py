from __future__ import annotations

from app.models.facts import SourceRecord

# Official landing pages only — do not invent deep circular URLs.
REGISTRY: list[dict] = [
    {
        "source_id": "src-itd-home",
        "title": "Income Tax Department",
        "url": "https://www.incometax.gov.in/iec/foportal/",
        "authority": "Income Tax Department",
        "tier": 1,
        "facts": ["tax_regimes", "section_80c", "vda_tax"],
    },
    {
        "source_id": "src-itd-india",
        "title": "Income Tax India",
        "url": "https://incometaxindia.gov.in/",
        "authority": "Income Tax Department",
        "tier": 1,
        "facts": ["tax_regimes", "section_80ccd_1b", "section_80ccd_2"],
    },
    {
        "source_id": "src-rbi",
        "title": "Reserve Bank of India",
        "url": "https://www.rbi.org.in/",
        "authority": "RBI",
        "tier": 1,
        "facts": ["lrs", "market_data_restrictions"],
    },
    {
        "source_id": "src-pfrda",
        "title": "Pension Fund Regulatory and Development Authority",
        "url": "https://www.pfrda.org.in/",
        "authority": "PFRDA",
        "tier": 1,
        "facts": ["nps"],
    },
    {
        "source_id": "src-nps-trust",
        "title": "NPS Trust",
        "url": "https://www.npstrust.org.in/",
        "authority": "NPS Trust",
        "tier": 1,
        "facts": ["nps"],
    },
    {
        "source_id": "src-sebi",
        "title": "Securities and Exchange Board of India",
        "url": "https://www.sebi.gov.in/",
        "authority": "SEBI",
        "tier": 1,
        "facts": ["market_data_restrictions"],
    },
    {
        "source_id": "src-amfi",
        "title": "Association of Mutual Funds in India",
        "url": "https://www.amfiindia.com/",
        "authority": "AMFI",
        "tier": 1,
        "facts": ["mutual_fund_universe"],
    },
    {
        "source_id": "src-nse",
        "title": "National Stock Exchange of India",
        "url": "https://www.nseindia.com/",
        "authority": "NSE",
        "tier": 1,
        "facts": ["index_observation"],
    },
    {
        "source_id": "src-bse",
        "title": "BSE Limited",
        "url": "https://www.bseindia.com/",
        "authority": "BSE",
        "tier": 1,
        "facts": ["index_observation"],
    },
    {
        "source_id": "src-indiapost",
        "title": "India Post",
        "url": "https://www.indiapost.gov.in/",
        "authority": "India Post",
        "tier": 1,
        "facts": ["small_savings"],
    },
]


def registry_records(*, mock: bool, fetched_at, as_of: str, verification: str) -> list[SourceRecord]:
    return [
        SourceRecord(
            source_id=item["source_id"],
            title=item["title"],
            url=item["url"],
            authority=item["authority"],
            tier=item["tier"],
            fetched_at=fetched_at,
            as_of=as_of,
            verification=verification,  # type: ignore[arg-type]
            confidence="medium" if mock else "high",
            affected_facts=item["facts"],
            mock=mock,
        )
        for item in REGISTRY
    ]
