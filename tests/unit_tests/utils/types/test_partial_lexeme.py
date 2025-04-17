"""pytest test‑suite for ``lexeme.py`` (Python 3.10).

Run with:
    pytest -q
"""

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
    Lexeme("test")


def test_regular_equality() -> None:
    singular, plural = REGULAR_PAIR
    assert Lexeme(singular) == Lexeme(plural) == singular
    assert not plural == singular


@pytest.mark.parametrize("singular,plural", IRREGULAR_PAIRS)
def test_irregular_equality(singular: str, plural: str) -> None:
    assert Lexeme(singular) == plural
    assert Lexeme(plural) == singular


def test_hash_equivalence() -> None:
    """Dictionary and set operations should treat singular/plural as the same key.

    Note
    ----
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
    assert Lexeme("ReadErS") == "readers"
    assert Lexeme("ReaDers") == "READERS"


def test_whitespace_trimmed() -> None:
    assert Lexeme(" reader ") == "readers"


def test_ss_suffix_not_singularised() -> None:
    """Words ending with 'ss' should not be truncated to singular."""
    assert Lexeme("glass") == "glass"
    assert Lexeme("glass") != "glas"


def test_short_word_not_truncated() -> None:
    assert Lexeme("bus") == "bus"
    assert Lexeme("bus") != "bu"


def test_plural_property_idempotent() -> None:
    word = Lexeme("boxes")
    assert word.plural == "boxes"


def test_additional_plural_rules() -> None:
    assert Lexeme("dish") == "dishes"
    assert Lexeme("church") == "churches"
    assert Lexeme("box").plural == "boxes"


def test_type_error_on_non_string() -> None:
    with pytest.raises(TypeError):
        Lexeme(123)


def test_repr_roundtrip() -> None:
    obj = Lexeme("reader")
    assert repr(obj) == "Lexeme('reader')"
    assert eval(repr(obj)) == obj


def test_equality_with_unrelated_type() -> None:
    assert (Lexeme("reader") == 5) is False


# Pydantic v2 integration
def test_pydantic_model_serialisation() -> None:
    class Plugin(BaseModel):
        kind: Lexeme
        interface: Lexeme

    model = Plugin(kind="reader", interface="readers")

    # Internal equality
    assert model.kind == model.interface == "reader"

    # Serialisation should yield plain strings
    data = json.loads(model.model_dump_json())
    assert data == {"kind": "reader", "interface": "readers"}
