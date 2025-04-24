"""pytest test‑suite for ``lexeme.py``."""

from __future__ import annotations

import json
from typing import Dict, Set, Tuple

import pytest
from pydantic import BaseModel

from geoips.utils.types.partial_lexeme import Lexeme

REGULAR_PAIR: Tuple[str, str] = ("reader", "readers")
IRREGULAR_PAIRS = [
    ("analysis", "analyses"),
    ("index", "indices"),
    ("child", "children"),
]


def test_creation() -> None:
    """
    Test creation of a Lexeme instance from a valid string.

    Ensures that initializing Lexeme with a simple word does not raise an exception.
    """
    Lexeme("test")


def test_regular_equality() -> None:
    """
    Test equality behavior for regular singular and plural forms.

    Checks that singular and plural forms with a standard 's' suffix compare equal
    and maintain proper equality ordering (i.e., plural != singular).
    """
    singular, plural = REGULAR_PAIR
    assert Lexeme(singular) == Lexeme(plural) == singular
    assert not plural == singular


@pytest.mark.parametrize("singular,plural", IRREGULAR_PAIRS)
def test_irregular_equality(singular: str, plural: str) -> None:
    """
    Test equality behavior for irregular plural forms.

    Parameters
    ----------
    singular : str
        The singular form of an irregular noun.
    plural : str
        The plural form of the same noun.
    """
    assert Lexeme(singular) == plural
    assert Lexeme(plural) == singular


def test_hash_equivalence() -> None:
    """
    Test that hash-based structures treat singular and plural as equivalent keys.

    Notes
    -----
    Variables must be cast as a Lexeme to index correctly.
    """
    d: Dict[Lexeme, int] = {Lexeme("analysis"): 1}
    d[Lexeme("analyses")] = d.get(Lexeme("analyses"), 0) + 1
    assert len(d) == 1
    assert d["analysis"] == 2

    s: Set[Lexeme] = {Lexeme("READER")}
    s.add(Lexeme("readers"))
    assert len(s) == 1

    assert "test" in [Lexeme("test")]


def test_case_insensitivity() -> None:
    """
    Test that lexeme comparisons are case-insensitive.

    Verifies that different casing variants of the same word are considered equal.
    """
    assert Lexeme("ReadErS") == "readers"
    assert Lexeme("ReaDers") == "READERS"


def test_whitespace_trimmed() -> None:
    """
    Test that leading and trailing whitespace is trimmed.

    Ensures that spaces around the word do not affect equality.
    """
    assert Lexeme(" reader ") == "readers"


def test_ss_suffix_not_singularised() -> None:
    """
    Test that words ending with 'ss' are not truncated to singular.

    Words like 'glass' should not lose one 's' when singularized.
    """
    assert Lexeme("glass") == "glass"
    assert Lexeme("glass") != "glas"


def test_short_word_not_truncated() -> None:
    """
    Test that short words less than 3 characters are not truncated.

    Ensures that 'bus' remains unchanged and does not become 'bu'.
    """
    assert Lexeme("bus") == "bus"
    assert Lexeme("bus") != "bu"


def test_plural_property_idempotent() -> None:
    """
    Test that the plural property is idempotent for already plural words.

    When requesting the plural of a word that is already plural,
    it should remain the same.
    """
    word = Lexeme("boxes")
    assert word.plural == "boxes"


def test_additional_plural_rules() -> None:
    """
    Test additional pluralization rules for words ending in 'ch', 'sh', and 'x'.

    'dish' -> 'dishes', 'church' -> 'churches', 'box'.plural -> 'boxes'.
    """
    assert Lexeme("dish") == "dishes"
    assert Lexeme("church") == "churches"
    assert Lexeme("box").plural == "boxes"


def test_type_error_on_non_string() -> None:
    """
    Test that initializing Lexeme with a non-string raises a TypeError.

    Passing an integer should not be allowed.
    """
    with pytest.raises(TypeError):
        Lexeme(123)


def test_repr_roundtrip() -> None:
    """
    Test that repr and eval round-trip produce equivalent Lexeme objects.

    Ensures that repr(obj) yields a string that eval can recreate the same object.
    """
    obj = Lexeme("reader")
    string_repr = "Lexeme('reader')"
    assert repr(obj) == string_repr
    assert eval(string_repr) == obj


def test_equality_with_unrelated_type() -> None:
    """
    Test that comparing Lexeme to an unrelated type returns False.

    Ensures safe equality checks with non-string types.
    """
    assert (Lexeme("reader") == 5) is False


def test_pydantic_model_serialisation() -> None:
    """
    Test Pydantic v2 integration for Lexeme fields in models.

    - Internal equality: singular/plural mapping within the model
    - Serialization: model_dump_json yields plain strings
    """

    class Plugin(BaseModel):
        kind: Lexeme
        interface: Lexeme

    model = Plugin(kind="reader", interface="readers")

    # Internal equality
    assert model.kind == model.interface == "reader"

    # Serialisation should yield plain strings
    data = json.loads(model.model_dump_json())
    assert data == {"kind": "reader", "interface": "readers"}
