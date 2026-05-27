# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Stable tokenization helpers for DataTree provenance.

Wraps ``dask.base.tokenize`` to produce deterministic, content-addressed
tokens for step outputs, argument dictionaries, and step provenance chains.
Tokens are prefixed with ``"dask:"`` so future migrations to a different
hash provider remain detectable and safe to compare by full-string equality.
"""

from __future__ import annotations

import logging
from typing import Any

from dask.base import tokenize as dask_tokenize

LOG = logging.getLogger(__name__)

_TOKEN_PREFIX = "dask:"


def compute_token(*objs: Any) -> str:
    r"""Compute a stable, deterministic token over the given objects.

    Wraps ``dask.base.tokenize`` and prefixes its output so that future
    migrations to a different hash provider remain forward-compatible in
    stored ``attrs``.

    Parameters
    ----------
    \*objs : Any
        Objects to include in the token. The call is positional so that
        callers cannot accidentally pass the same objects in a different
        order and get the same token.

    Returns
    -------
    str
        A ``"dask:<hex>"`` token string.

    Examples
    --------
    >>> compute_token("hello", 42)
    'dask:...'
    >>> compute_token("hello", 42) == compute_token("hello", 42)
    True
    """
    return _TOKEN_PREFIX + dask_tokenize(*objs)


def compute_arguments_hash(arguments: dict[str, Any]) -> str:
    """Tokenize a step's arguments dictionary.

    The hash covers keys and values in a stable order so that semantically
    identical argument dicts produce identical tokens even when supplied
    via different code paths.

    Parameters
    ----------
    arguments : dict
        The step's ``arguments`` dictionary from the workflow spec.

    Returns
    -------
    str
        A ``"dask:"``-prefixed token string.
    """
    # Sort items so two dicts with the same content hash identically
    sorted_items = tuple(sorted(arguments.items(), key=lambda kv: kv[0]))
    return compute_token(sorted_items)


def compute_step_output_token(
    step_output: Any,
    plugin_name: str,
    plugin_kind: str,
    arguments: dict[str, Any],
    upstream_tokens: dict[str, str] | None = None,
) -> str:
    """Compute a step's ``output_token`` for provenance attrs.

    The token MUST change when any of *plugin identity*, *arguments*, or
    *upstream tokens* change.  It MUST NOT change for cosmetic refactors
    that produce the same data.

    Parameters
    ----------
    step_output : Any
        The return value of a step's ``call()`` method (a Dataset, DataTree,
        numpy array, dict, etc.).
    plugin_name : str
        Plugin name (e.g. ``"abi_netcdf"``).
    plugin_kind : str
        Plugin kind (e.g. ``"reader"``).
    arguments : dict
        The step's ``arguments`` dictionary.
    upstream_tokens : dict[str, str] or None
        Mapping of upstream step-id → output_token, or ``None`` for
        reader steps with no dependencies.

    Returns
    -------
    str
        A ``"dask:"``-prefixed token, or ``"untokenizable:<exc>"`` if
        tokenization raises an exception.
    """
    try:
        return compute_token(
            plugin_name,
            plugin_kind,
            compute_arguments_hash(arguments),
            tuple(sorted((upstream_tokens or {}).items())),
            step_output,
        )
    except Exception as exc:
        LOG.warning(
            "Could not tokenize output from %s/%s: %s",
            plugin_kind,
            plugin_name,
            exc,
        )
        return f"untokenizable:{type(exc).__name__}"
