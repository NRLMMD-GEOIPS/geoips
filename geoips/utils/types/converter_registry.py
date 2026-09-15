# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Generalised bidirectional type-converter registry.

``TypeConverterRegistry`` stores one-way converters keyed by
``(source_type, target_type)`` tuples and dispatches with
priority-matching (exact type, then ``isinstance`` MRO-ordered).

It is independent of ``DataTreeDitto`` so that both the tree-storage
layer and the plugin-lifecycle hooks can share the same converters.
"""

from __future__ import annotations

from typing import Any


class TypeConverterRegistry:
    """Bidirectional type converter registry with priority dispatch.

    Stores one-way (source → target) converters and dispatches calls
    using exact-type matching first, falling back to
    ``isinstance``-based matching with MRO ordering (most specific
    registered type wins).

    A module-level singleton ``converter_registry`` is created at
    import time for use throughout the framework.

    Examples
    --------
    >>> registry = TypeConverterRegistry()
    >>> registry.register(np.ndarray, xr.Dataset, numpy_to_dataset)
    >>> ds = registry.convert(np.array([1, 2, 3]), xr.Dataset)
    >>> isinstance(ds, xr.Dataset)
    True
    """

    def __init__(self) -> None:
        self._converters: dict[tuple[type, type], Any] = {}

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def register(
        self,
        source: type,
        target: type,
        converter: Any,
    ) -> None:
        """Register a one-way converter from *source* to *target*.

        Parameters
        ----------
        source : type
            Source type.
        target : type
            Target type.
        converter : callable
            ``converter(obj, **kwargs)`` must return an instance of
            *target*.
        """
        self._converters[(source, target)] = converter

    def register_bidirectional(
        self,
        type_a: type,
        type_b: type,
        a_to_b: Any,
        b_to_a: Any,
    ) -> None:
        """Register a pair of converters for round-trip conversion.

        Convenience wrapper around two ``register()`` calls.

        Parameters
        ----------
        type_a : type
            First type.
        type_b : type
            Second type.
        a_to_b : callable
            Convert *type_a* → *type_b*.
        b_to_a : callable
            Convert *type_b* → *type_a*.
        """
        self.register(type_a, type_b, a_to_b)
        self.register(type_b, type_a, b_to_a)

    def convert(self, obj: Any, target: type, **kwargs: Any) -> Any:
        """Convert *obj* to *target* using a registered converter.

        Matching order:

        1. Exact ``type(obj)`` → *target* entry.
        2. ``isinstance``-based match, ordered by the object's Method
           Resolution Order (MRO) so the most specific registered base class
           wins. The MRO is the linearized order Python searches an object's
           class hierarchy (``type(obj).__mro__``); see
           https://docs.python.org/3/howto/mro.html. For example, a
           ``MaskedArray`` (a subclass of ``ndarray``) prefers a registered
           ``MaskedArray`` converter over an ``ndarray`` one.

        Parameters
        ----------
        obj : Any
            Object to convert.
        target : type
            Desired target type.
        kwargs
            Forwarded to the converter function.

        Returns
        -------
        Any
            Converted object (guaranteed to be an instance of *target*
            when a converter is found).

        Raises
        ------
        TypeError
            If no converter is registered for the requested path.
        """
        obj_type = type(obj)

        # 1. exact match
        key = (obj_type, target)
        if key in self._converters:
            return self._converters[key](obj, **kwargs)

        # 2. isinstance-based match, MRO-ordered
        matching = [
            (src, tgt)
            for (src, tgt) in self._converters
            if tgt is target and isinstance(obj, src)
        ]
        if matching:
            mro = obj_type.__mro__
            matching.sort(
                key=lambda pair: mro.index(pair[0]) if pair[0] in mro else len(mro),
            )
            src = matching[0][0]
            return self._converters[(src, target)](obj, **kwargs)

        registered_sources = sorted(
            {f"{src.__module__}.{src.__name__}" for src, _ in self._converters}
        )
        raise TypeError(
            f"Cannot convert an object of type "
            f"'{obj_type.__module__}.{obj_type.__name__}' to "
            f"'{target.__module__}.{target.__name__}': no converter is "
            f"registered for this type. This typically surfaces when a "
            f"DataTreeDitto (or the order-based procflow) is given a payload "
            f"whose type has no registered conversion. To fix it, register a "
            f"converter, e.g.:\n"
            f"    from geoips.utils.types.converter_registry import "
            f"converter_registry\n"
            f"    converter_registry.register("
            f"{obj_type.__name__}, {target.__name__}, my_converter_fn)\n"
            f"Currently registered source types: {registered_sources}. "
            f"See geoips.utils.types.converters for examples."
        )

    def can_convert(self, obj: Any, target: type) -> bool:
        """Return ``True`` if a conversion path exists for *obj* → *target*."""
        obj_type = type(obj)
        if (obj_type, target) in self._converters:
            return True
        return any(
            tgt is target and isinstance(obj, src) for src, tgt in self._converters
        )

    # ------------------------------------------------------------------
    # introspection
    # ------------------------------------------------------------------

    @property
    def registered_types(self) -> dict[type, set[type]]:
        """Return {source_type: {target_type, ...}} summary."""
        summary: dict[type, set[type]] = {}
        for src, tgt in self._converters:
            summary.setdefault(src, set()).add(tgt)
        return summary

    def __repr__(self) -> str:
        """Return a concise repr showing the number of registered converters."""
        return f"{self.__class__.__name__}(" f"converters={len(self._converters)})"


# Module-level singleton — import and use directly.
converter_registry = TypeConverterRegistry()
