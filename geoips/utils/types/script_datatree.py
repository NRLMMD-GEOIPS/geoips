# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Helpers for OBP-style plugin calls from scripts."""

from datetime import datetime, timezone
from enum import StrEnum

import xarray as xr


class RetentionPolicy(StrEnum):
    """Retention policies for OBP-style scripted plugin calls.

    Use these values when initializing a script DataTree or overriding
    retention behavior for a single scripted plugin call. Each enum member is
    string-like, so it can be compared with or serialized as its string value,
    but it also carries a short interactive description.

    Examples
    --------
    >>> from geoips.scripting import RetentionPolicy, initialize_script_tree
    >>> tree = initialize_script_tree(
    ...     "abi_infrared_test",
    ...     retention_policy=RetentionPolicy.metadata_only,
    ... )
    >>> tree = reader_plugin(
    ...     data=tree,
    ...     filenames=fnames,
    ...     step_id="read_data",
    ...     _obp_initiated=True,
    ... )

    String values such as ``"metadata_only"`` are also accepted for
    configuration-driven scripts.
    """

    def __new__(cls, value, description):
        """Create a string-like retention policy with a description."""
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    @property
    def __doc__(self):
        """Return the policy description for interactive help."""
        return self.description

    keep_all = (
        "keep_all",
        "Keep every plugin result intact. Useful for debugging, exploratory "
        "scripts, notebooks, and tests where intermediate data should remain "
        "available for inspection.",
    )
    metadata_only = (
        "metadata_only",
        "Keep the current plugin result intact, but reduce older results to "
        "attrs only. Useful for preserving provenance while reducing memory "
        "used by previous datasets.",
    )
    current_only = (
        "current_only",
        "Keep only the current plugin result and discard older step nodes. "
        "Useful for memory-sensitive processing where only the latest data "
        "product is needed.",
    )


SCRIPT_EXECUTION_MODE = "script"
RETENTION_POLICIES = tuple(RetentionPolicy)
_RESERVED_ROOT_ATTRS = frozenset(
    ("execution_mode", "retention_policy", "start_time", "end_time")
)


def normalize_retention_policy(retention_policy):
    """Return a canonical retention policy from a string or RetentionPolicy.

    This internal helper lets user-facing functions accept either
    ``RetentionPolicy.metadata_only`` style values or equivalent string values
    such as ``"metadata_only"``.
    """
    try:
        return RetentionPolicy(retention_policy)
    except ValueError as resp:
        valid_policies = ", ".join(policy.value for policy in RETENTION_POLICIES)
        raise ValueError(
            f"Invalid retention policy {retention_policy!r}. "
            f"Expected one of: {valid_policies}."
        ) from resp


def validate_retention_policy(retention_policy):
    """Validate a script DataTree retention policy."""
    normalize_retention_policy(retention_policy)


def initialize_script_tree(name, retention_policy, **attrs):
    """Initialize a root DataTree for OBP-style scripted plugin calls.

    The returned tree is intended to be passed as the ``data`` argument to
    plugins called with ``_obp_initiated=True``. Each plugin call will
    eventually attach its result back onto this script tree using ``step_id``.

    Parameters
    ----------
    name : str
        Name for the root script DataTree.
    retention_policy : RetentionPolicy or str
        Retention policy to apply after scripted plugin calls. May be supplied
        as a ``RetentionPolicy`` value or its string value. May be overridden
        on individual steps.
    **attrs : dict
        Additional root-level metadata to store on the script DataTree.

    Returns
    -------
    xarray.DataTree
        Root DataTree with standard script execution metadata.

    Raises
    ------
    ValueError
        If *retention_policy* is not recognized, or if *attrs* attempts to
        override reserved script metadata fields.

    Examples
    --------
    >>> from geoips.scripting import RetentionPolicy, initialize_script_tree
    >>> tree = initialize_script_tree(
    ...     "abi_infrared_test",
    ...     retention_policy=RetentionPolicy.metadata_only,
    ... )
    >>> tree = reader_plugin(
    ...     data=tree,
    ...     filenames=fnames,
    ...     step_id="read_data",
    ...     _obp_initiated=True,
    ... )
    """
    retention_policy = normalize_retention_policy(retention_policy)

    reserved_attrs = _RESERVED_ROOT_ATTRS.intersection(attrs)
    if reserved_attrs:
        reserved_names = ", ".join(sorted(reserved_attrs))
        raise ValueError(
            "Script DataTree metadata fields are reserved and may not be "
            f"overridden: {reserved_names}."
        )

    tree = xr.DataTree(name=name)
    tree.attrs.update(
        {
            "execution_mode": SCRIPT_EXECUTION_MODE,
            "retention_policy": retention_policy.value,
            "start_time": datetime.now(timezone.utc).isoformat(),
            **attrs,
        }
    )
    return tree
