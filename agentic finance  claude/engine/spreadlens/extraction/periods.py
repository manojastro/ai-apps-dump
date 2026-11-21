"""Period header parsing: '31 March 2025', 'March 31, 2025', '31.03.2025', 'FY 2024-25', '2025'."""

from __future__ import annotations

import calendar
import re
from datetime import date

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})
MONTHS["sept"] = 9

_MON = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
DATE_DMY = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?[\s\-]+{_MON}[,\s\-]+(\d{{4}})\b", re.I)
DATE_MDY = re.compile(rf"\b{_MON}\s+(\d{{1,2}}),?\s+(\d{{4}})\b", re.I)
DATE_NUM = re.compile(r"\b(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})\b")
FY_RANGE = re.compile(r"\b(?:FY\s?)?(\d{4})\s?[-–/]\s?(\d{2,4})\b", re.I)
FY_SINGLE = re.compile(r"\bFY\s?'?(\d{2,4})\b", re.I)
YEAR = re.compile(r"\b(20\d{2}|19\d{2})\b")
YEAR_ENDED = re.compile(r"(year|period)\s+ended\s+(?:on\s+)?(.{0,30})", re.I)

PERIOD_PATTERNS = [DATE_DMY, DATE_MDY, DATE_NUM, FY_RANGE, FY_SINGLE]


def _safe_date(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def parse_date(text: str) -> date | None:
    m = DATE_DMY.search(text)
    if m:
        return _safe_date(int(m.group(3)), MONTHS[m.group(2).lower()[:3] if m.group(2).lower()[:3] in MONTHS else m.group(2).lower()], int(m.group(1)))
    m = DATE_MDY.search(text)
    if m:
        return _safe_date(int(m.group(3)), MONTHS[m.group(1).lower()[:3]], int(m.group(2)))
    m = DATE_NUM.search(text)
    if m:
        return _safe_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))  # day-first (Indian convention)
    return None


def fiscal_year_end(text: str) -> tuple[int, int] | None:
    """(month, day) of the fiscal year end from phrases like 'for the year ended 31 March 2025'."""
    for m in YEAR_ENDED.finditer(text):
        d = parse_date(m.group(2))
        if d:
            return d.month, d.day
    return None


def parse_period_header(text: str, fye: tuple[int, int] | None) -> tuple[date | None, str]:
    """Return (period_end, how) for one column header. Never guesses a month/day without evidence."""
    d = parse_date(text)
    if d:
        return d, "explicit date"
    m = FY_RANGE.search(text)
    if m:
        y2 = int(m.group(2))
        end_year = y2 if y2 > 100 else (int(m.group(1)) // 100) * 100 + y2
        if end_year < int(m.group(1)):
            end_year += 100
        if end_year - int(m.group(1)) == 1 and fye:
            return _safe_date(end_year, fye[0], fye[1]), "fiscal year range + stated year end"
        if end_year - int(m.group(1)) == 1:
            return None, "fiscal year range without a stated year-end date"
    m = FY_SINGLE.search(text)
    if m and fye:
        y = int(m.group(1))
        y = y if y > 100 else 2000 + y
        return _safe_date(y, fye[0], fye[1]), "FY label + stated year end"
    m = YEAR.search(text)
    if m and fye:
        return _safe_date(int(m.group(1)), fye[0], fye[1]), "year + stated year end"
    return None, "no period recognised"


def is_period_header(text: str) -> bool:
    return any(p.search(text) for p in PERIOD_PATTERNS) or bool(YEAR.fullmatch(text.strip()))


def duration_for(statement_type: str, title_and_header: str) -> str:
    if statement_type == "balance_sheet":
        return "point_in_time"
    t = title_and_header.lower()
    if re.search(r"quarter|three months|3 months", t):
        return "quarterly"
    if re.search(r"nine months|six months|half[- ]year|9 months|6 months|year to date|ytd", t):
        return "ytd"
    if re.search(r"year ended|for the year|annual|fy\s?\d", t):
        return "annual"
    return "annual" if statement_type in ("income_statement", "cash_flow") and "ended" in t else "unknown"


def period_start_for(end: date, duration: str) -> date | None:
    if duration != "annual":
        return None
    try:
        start = date(end.year - 1, end.month, end.day)
    except ValueError:
        start = date(end.year - 1, end.month, 28)
    return date.fromordinal(start.toordinal() + 1)
