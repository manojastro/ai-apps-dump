"""GSTIN structure and check character.

A GSTIN is 15 characters: state code (2 digits), PAN (10), entity number (1-9 or A-Z),
the letter 'Z', then a check character. The check character is Luhn mod 36 over the
alphabet 0-9A-Z: walk the first 14 characters left to right with weights 1, 2, 1, 2 ...,
fold each product as p // 36 + p % 36, sum, and take (36 - sum % 36) % 36.

Sources (read 2026-10-25): Luhn mod N algorithm (en.wikipedia.org/wiki/Luhn_mod_N_algorithm);
several independent GSTIN validator write-ups agree on the alphabet and weights. No official
GSTN specification was found, so tests check the algorithm's properties on synthetic GSTINs.
"""

import re
from enum import StrEnum

from invoiceflow.core.gst_states import STATE_NAMES
from invoiceflow.data.models import Frozen

GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
VALID_STATE_CODES = frozenset(STATE_NAMES)
_FORMAT = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
_PAN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


class GstinFailure(StrEnum):
    WRONG_LENGTH = "WRONG_LENGTH"
    BAD_FORMAT = "BAD_FORMAT"
    UNKNOWN_STATE_CODE = "UNKNOWN_STATE_CODE"
    BAD_CHECK_CHARACTER = "BAD_CHECK_CHARACTER"


class GstinCheck(Frozen):
    gstin: str
    valid: bool
    failure: GstinFailure | None = None
    detail: str = ""


def check_character(first14: str) -> str:
    n = len(GSTIN_CHARSET)
    total = 0
    for position, char in enumerate(first14):
        product = GSTIN_CHARSET.index(char) * (1 if position % 2 == 0 else 2)
        total += product // n + product % n
    return GSTIN_CHARSET[(n - total % n) % n]


def make_gstin(state_code: str, pan: str, entity: str = "1") -> str:
    if state_code not in VALID_STATE_CODES:
        raise ValueError(f"unknown GST state code {state_code!r}")
    if not _PAN.match(pan):
        raise ValueError(f"PAN must be 5 letters, 4 digits, 1 letter; got {pan!r}")
    first14 = f"{state_code}{pan}{entity}Z"
    return first14 + check_character(first14)


def validate_gstin(gstin: str) -> GstinCheck:
    if len(gstin) != 15:
        return GstinCheck(
            gstin=gstin,
            valid=False,
            failure=GstinFailure.WRONG_LENGTH,
            detail=f"GSTIN must be 15 characters, got {len(gstin)}",
        )
    if not _FORMAT.match(gstin):
        return GstinCheck(
            gstin=gstin,
            valid=False,
            failure=GstinFailure.BAD_FORMAT,
            detail="expected 2 digits, PAN (5 letters, 4 digits, letter), entity 1-9/A-Z, 'Z', "
            "check character",
        )
    if gstin[:2] not in VALID_STATE_CODES:
        return GstinCheck(
            gstin=gstin,
            valid=False,
            failure=GstinFailure.UNKNOWN_STATE_CODE,
            detail=f"state code {gstin[:2]!r} is not on the GST state code list",
        )
    expected = check_character(gstin[:14])
    if gstin[14] != expected:
        return GstinCheck(
            gstin=gstin,
            valid=False,
            failure=GstinFailure.BAD_CHECK_CHARACTER,
            detail=f"check character is {gstin[14]!r}, expected {expected!r}",
        )
    return GstinCheck(gstin=gstin, valid=True)
