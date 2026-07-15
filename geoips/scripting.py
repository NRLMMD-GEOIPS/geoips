# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""User-facing helpers for scripting with GeoIPS plugins."""

from geoips.utils.types.script_datatree import (
    RETENTION_POLICIES,
    RetentionPolicy,
    initialize_script_tree as _initialize_script_tree,
)


def initialize_script_tree(name, retention_policy, **attrs):
    """Initialize a DataTree for OBP-style scripted plugin calls.

    Use this helper at the start of scripts that call GeoIPS plugins directly
    while passing an accumulated script tree from one plugin to the next. The
    returned tree should be supplied as the ``data`` argument to plugin calls
    made with ``_obp_initiated=True``.

    Parameters
    ----------
    name : str
        Name for the root script DataTree.
    retention_policy : RetentionPolicy or str
        Retention policy to apply after scripted plugin calls. Prefer
        ``RetentionPolicy`` values in Python code; equivalent strings are also
        accepted for configuration-driven scripts.
    **attrs : dict
        Additional root-level metadata to store on the script DataTree.

    Returns
    -------
    xarray.DataTree
        Root DataTree with standard script execution metadata.

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
    return _initialize_script_tree(name, retention_policy, **attrs)

__all__ = ["RETENTION_POLICIES", "RetentionPolicy", "initialize_script_tree"]
