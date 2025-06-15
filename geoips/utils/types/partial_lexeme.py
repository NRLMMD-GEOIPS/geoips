# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Lightweight helper for treating singular and plural spellings as equivalent.

A drop‑in str subclass that normalizes English nouns so that their
singular and plural forms compare as equal, hash to the same key, and work
inside Pydantic v2 models. Ignores capitalization.

Examples
--------
>>> from partial_lexeme import Lexeme
>>> Lexeme("reader") == "readers" == Lexeme("readers")
True
>>> {Lexeme("analyses"): 1} == {"analysis": 1}
True

>>> from pydantic import BaseModel
>>> class _Plugin(BaseModel):
>>>     kind: Lexeme
>>>     interface: Lexeme
>>> model = _Plugin(kind="reader", interface="readers")
>>> assert model.kind == model.interface == "reader"
"""

from __future__ import annotations
from typing import Any, Dict

__all__ = ["Lexeme"]

# Irregular nouns – plural ↔ singular
#   - Each plural maps to its singular
#   - Singulars map to themselves so that a single lookup works
_IRREGULAR: Dict[str, str] = {
    "analyses": "analysis",
    "analysis": "analysis",
    "indices": "index",
    "index": "index",
    "children": "child",
    "data": "datum",
    "criteria": "criterion",
}

# Reverse map – singular → plural
_S_TO_P: Dict[str, str] = {
    singular: plural for plural, singular in _IRREGULAR.items() if plural != singular
}


def _normalize(word: str) -> str:
    """Return the canonical singular, lower‑case form of word.

    Check the irregular table and then if not found
    apply heuristic suffix rules for regular nouns.
    """
    w = word.strip().lower()
    if not w:
        return ""

    if w in _IRREGULAR:
        return _IRREGULAR[w]

    # heuristics
    if w.endswith("ies") and len(w) > 3 and w[-4] not in "aeiou":
        return w[:-3] + "y"

    if w.endswith("es") and w[-3:] in {"ses", "xes", "zes"}:
        return w[:-2]

    if w.endswith("es") and w[-4:-2] in {"sh", "ch"}:
        return w[:-2]

    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]

    return w


def _to_plural(word: str) -> str:
    """Return a plausible plural spelling for *word*.

    This is best‑effort but the
    lexeme type does not depend on it because equality & hashing
    always normalizes back to singular.
    """
    w = word.strip().lower()

    if w in _S_TO_P:
        return _S_TO_P[w]

    # Simple heuristic rules
    if w.endswith("y") and w[-2] not in "aeiou":
        return w[:-1] + "ies"

    if w.endswith(("s", "x", "z")) or w.endswith("sh") or w.endswith("ch"):
        return w + "es"

    return w + "s"


class Lexeme(str):
    """A string that treats singular and plural spellings as equal.

    It behaves exactly like a built‑in ``str`` but overrides equality and
    hashing to use the canonical singular form.  This makes singular and
    plural spellings interchangeable as dict keys, set members, CLI options,
    etc.
    """

    def __new__(cls, value: Any) -> "Lexeme":
        """Create new Lexeme."""
        if isinstance(value, str):
            return super().__new__(cls, value)
        raise TypeError(
            f"{cls.__name__} must be built from str, got {type(value).__name__}"
        )

    @property
    def singular(self) -> "Lexeme":
        """Return the singular spelling."""
        return self.__class__(_normalize(self))

    @property
    def plural(self) -> "Lexeme":
        """Return a plural spelling."""
        return self.__class__(_to_plural(self.singular))

    def _key(self) -> str:
        """Normalize key for comparisons and hashing."""
        return _normalize(self)

    def __eq__(self, other: object) -> bool:
        """Plural or singular equality check."""
        if isinstance(other, str):
            return self._key() == _normalize(other)
        if isinstance(other, Lexeme):
            return self._key() == other._key()
        return False

    def __hash__(self) -> int:
        """Hash lexeme."""
        return hash(self._key())

    def __repr__(self) -> str:
        """Print out un-serialized self."""
        return f"{self.__class__.__name__}({super().__str__()!r})"

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        """Return a core_schema that allows ``Lexeme`` for use as a field in pydantic.

        Accepts ``str`` or ``Lexeme``; coerces to ``Lexeme``.
        Always serializes output as plain string.
        """
        # lazy import so only imported if using pydantic
        from pydantic_core import core_schema

        def _to_lexeme(value: object, _info=None):
            if isinstance(value, cls):
                return value
            if isinstance(value, str):
                return cls(value)
            raise TypeError("String or Lexeme required")

        return core_schema.no_info_after_validator_function(
            _to_lexeme,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v)
            ),
        )
