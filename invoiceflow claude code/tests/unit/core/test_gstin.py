"""GSTIN structure and Luhn mod-36 check character. Synthetic GSTINs only (rule 2)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from invoiceflow.core.gstin import (
    GSTIN_CHARSET,
    VALID_STATE_CODES,
    GstinFailure,
    check_character,
    make_gstin,
    validate_gstin,
)

# Worked by hand, left to right with weights 1,2,1,2...; folded = p // 36 + p % 36:
#   2 9 Q W X Y Z 9 8 7 6 K 1 Z  -> folded 2,18,26,29,33,33,35,18,8,14,6,5,1,35 = 263
#   263 % 36 = 11 -> (36 - 11) % 36 = 25 -> 'P'
HAND_VECTOR = "29QWXYZ9876K1ZP"
# Entity character 1 -> Q adds 25, so the sum is 288 = 8 * 36 and the check is '0'.
# Covers the final "% 36" that a naive (36 - sum % 36) misses.
HAND_VECTOR_ZERO = "29QWXYZ9876KQZ0"

letters = st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
digits = st.sampled_from("0123456789")
pans = st.tuples(
    st.lists(letters, min_size=5, max_size=5),
    st.lists(digits, min_size=4, max_size=4),
    letters,
).map(lambda t: "".join(t[0]) + "".join(t[1]) + t[2])
states = st.sampled_from(sorted(VALID_STATE_CODES))
entities = st.sampled_from("123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")


@pytest.mark.parametrize("gstin", [HAND_VECTOR, HAND_VECTOR_ZERO])
def test_hand_computed_vectors(gstin: str) -> None:
    assert check_character(gstin[:14]) == gstin[14]
    assert validate_gstin(gstin).valid


@given(state=states, pan=pans, entity=entities)
def test_generated_gstins_always_validate(state: str, pan: str, entity: str) -> None:
    gstin = make_gstin(state, pan, entity)
    result = validate_gstin(gstin)
    assert result.valid, result.detail
    assert result.failure is None


@given(
    state=states,
    pan=pans,
    position=st.integers(min_value=0, max_value=14),
    replacement=st.sampled_from(GSTIN_CHARSET),
)
def test_every_single_character_substitution_is_caught(
    state: str, pan: str, position: int, replacement: str
) -> None:
    gstin = make_gstin(state, pan)
    if gstin[position] == replacement:
        return
    mutated = gstin[:position] + replacement + gstin[position + 1 :]
    assert not validate_gstin(mutated).valid


def test_wrong_check_character_is_reported_with_expected_value() -> None:
    result = validate_gstin(HAND_VECTOR[:14] + "Q")
    assert result.failure is GstinFailure.BAD_CHECK_CHARACTER
    assert "expected 'P'" in result.detail


@pytest.mark.parametrize(
    ("gstin", "failure"),
    [
        ("29QWXYZ9876K1Z", GstinFailure.WRONG_LENGTH),
        ("29QWXYZ9876K1ZPP", GstinFailure.WRONG_LENGTH),
        ("29qwxyz9876k1zp", GstinFailure.BAD_FORMAT),
        ("29QWXYZ9876K1XP", GstinFailure.BAD_FORMAT),  # 14th character must be Z
        ("29QWXYZ9876K0ZP", GstinFailure.BAD_FORMAT),  # entity number cannot be 0
        ("28QWXYZ9876K1ZP", GstinFailure.UNKNOWN_STATE_CODE),  # 28 retired
        ("99QWXYZ9876K1ZP", GstinFailure.UNKNOWN_STATE_CODE),
    ],
)
def test_structural_failures_are_named(gstin: str, failure: GstinFailure) -> None:
    result = validate_gstin(gstin)
    assert not result.valid
    assert result.failure is failure
    assert result.detail


def test_make_gstin_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError, match="state code"):
        make_gstin("28", "QWXYZ9876K")
    with pytest.raises(ValueError, match="PAN"):
        make_gstin("29", "QWXYZ9876")
