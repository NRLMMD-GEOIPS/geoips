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

    It converts plural nouns to their singular forms using:
    1. An irregular lookup table, `_IRREGULAR` for known exceptions.
    2. Heuristic suffix rules for regular pluralization:

      - Words ending in "ies" - replace "ies" with "y" if preceded by a consonant
      - Words in double "zzes" - removes "zes"
      - Words ending in "sses", "xes", or "zes" - remove "es"
      - Words ending in "ses" - remove "s"
      - Words ending in "es" and containing "sh" or "ch" in their singular form
      - Words ending in singular "s" and more than three characters long - remove "s"

    Parameters
    ----------
    word : str
        The singular form of noun.

    Returns
    -------
    str
        A plausible plural form of the given word.

    Notes
    -----
    - It does not handle all English irregulars such as mice -> mouse unless present
       in `_IRREGULAR`.
    - Words that do not match any rule are returned unchanged in lowercase.
    """
    w = word.strip().lower()
    if not w:
        return ""

    if w in _IRREGULAR:
        return _IRREGULAR[w]

    # heuristics

    # parties -> party (replace "ies" with "y" if the preceding letter is a consonant)
    if w.endswith("ies") and len(w) > 3 and w[-4] not in "aeiou":
        return w[:-3] + "y"

    # quizzes -> quiz (remove "zes")
    if w.endswith("zzes"):
        return w[:-3]

    # processes -> process (remove "es")
    # boxes -> box, buzzes -> buzz (remove "es")
    if w.endswith(("sses", "xes", "zes")):
        return w[:-2]

    # processes -> process (remove "s")
    if w.endswith("ses"):
        return w[:-1]

    # dishes -> dish, churches -> church (remove "es")
    if w.endswith("es") and w[-4:-2] in {"sh", "ch"}:
        return w[:-2]

    # readers -> reader (remove "s")
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]

    return w


def _to_plural(word: str) -> str:
    r"""Return a plausible plural spelling for *word*.

    In this function’s documentation, consider * a regular Linux wildcard character.
    This function attempts tp pluralize a singular English noun using:

    1. An irregular lookup table, `_S_TO_P` for known exceptions.
    2. Heuristic spelling rules for regular pluralization:

      - \\*consonant + y --> \\*+ies such as party -> parties
      - \\*(x, ch, sh, ss, zz) --> \\*+es such as box -> boxes, buzz -> buzzes
      - \\*z -> \\*+zes --> such as quiz -> quizzes
      - near-default with min length of two characters -> default+s

    Parameters
    ----------
    word : str
        The singular form of noun.

    Returns
    -------
    str
        A plausible plural form of the given word.

    Raises
    ------
    ValueError
        If the `word` is empty or no pluralization rule can be applied.

    Notes
    -----
    -  This is best‑effort but the lexeme type does not depend on it because equality
       and hashing always normalizes back to singular.
    -  It does not handle all English irregulars such as mouse -> mice unless present
       in `_S_TO_P`.
    - Consider ``*`` a regular Linux wildcard character for reference.

    """
    w = word.strip().lower()

    # check for irregular words first
    if w in _S_TO_P:
        return _S_TO_P[w]

    # heuristics

    # party -> parties (replace "y" with "ies" if preceding by a consonant)
    if w.endswith("y") and w[-2] not in "aeiou":
        return w[:-1] + "ies"

    # box -> boxes (ends with "x" -> append "es")
    # church -> churches (ends with "ch" -> append "es")
    # dish -> dishes (ends with "sh" -> append "es")
    # process -> processes  (ends with "ss" -> append "es")
    # buzz -> buzzes (ends with double "z" -> append "es")
    if w.endswith(("x", "ch", "sh", "ss", "zz")):
        return w + "es"

    # quiz -> quizzes (ends with single "z" -> append zes)
    if w.endswith("z"):
        return w + "zes"

    # reader -> readers (near default scenario, append "s")
    if len(w) >= 2:
        return w + "s"

    raise ValueError(
        f"No pluralization rule for word: {w}. Check if it's a valid noun!!"
    )


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
        return _normalize(self)

    @property
    def plural(self) -> "Lexeme":
        """Return a plural spelling."""
        return _to_plural(self.singular)

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
