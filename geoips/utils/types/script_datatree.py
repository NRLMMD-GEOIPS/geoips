# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Helpers for OBP-style plugin calls from scripts."""

from datetime import datetime, timezone
from enum import StrEnum
from functools import cache

import xarray as xr

from geoips.utils.types.datatree_ditto import DataTreeDitto


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


def _utc_now():
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def _format_timestamp(timestamp, field_name):
    """Return an ISO-formatted timestamp string from a datetime or None."""
    if timestamp is None:
        return None
    if not isinstance(timestamp, datetime):
        raise TypeError(
            f"{field_name} must be a datetime.datetime instance or None. "
            f"Got {type(timestamp).__module__}.{type(timestamp).__name__}."
        )
    return timestamp.isoformat()


def _is_script_tree(tree):
    """Return whether *tree* is an initialized script DataTree."""
    return (
        isinstance(tree, xr.DataTree)
        and tree.attrs.get("execution_mode") == SCRIPT_EXECUTION_MODE
    )


@cache
def _valid_script_plugin_kinds():
    """Return valid registered plugin kinds for script step metadata.

    Interface discovery can be expensive, so this result is cached for the
    lifetime of the Python process. The returned set contains registered
    GeoIPS interface kinds, excluding ``product`` and ``workflow`` for now,
    plus the special ``manual`` kind for user-created script data.
    """
    from geoips import interfaces
    from geoips.utils.types.partial_lexeme import Lexeme

    interface_names = [
        name
        for names in interfaces.list_available_interfaces().values()
        for name in names
    ]
    plugin_kinds = {str(Lexeme(name).singular) for name in interface_names}
    plugin_kinds.difference_update({"product", "workflow"})
    plugin_kinds.add("manual")
    return frozenset(plugin_kinds)


def _validate_script_step_metadata(step_name, plugin_kind, plugin_name):
    """Validate script step metadata before attaching a result."""
    if not isinstance(step_name, str) or not step_name:
        raise ValueError("A step_id or plugin_name is required to attach a result.")
    if not step_name.isidentifier():
        raise ValueError(
            f"Script step id {step_name!r} is invalid. Step ids must be valid "
            "Python identifiers."
        )

    valid_plugin_kinds = _valid_script_plugin_kinds()
    if plugin_kind not in valid_plugin_kinds:
        valid_kinds = ", ".join(sorted(valid_plugin_kinds))
        raise ValueError(
            f"Invalid script plugin kind {plugin_kind!r}. "
            f"Expected one of: {valid_kinds}."
        )

    if plugin_name is not None and not isinstance(plugin_name, str):
        raise ValueError("plugin_name must be a string when provided.")
    if plugin_name == "":
        raise ValueError("plugin_name must be a non-empty string when provided.")
    if plugin_kind != "manual" and not plugin_name:
        raise ValueError("plugin_name must be a non-empty string.")


def initialize_script_tree(name, retention_policy, **attrs):
    """Initialize a root DataTree for OBP-style scripted plugin calls.

    The returned tree is intended to be passed as the ``data`` argument to
    direct plugin calls. Plugins infer script-mode OBP behavior from the
    tree's ``execution_mode`` metadata and attach results back onto this
    script tree using ``step_id``.

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
            "start_time": _utc_now().isoformat(),
            "end_time": None,
            **attrs,
        }
    )
    return tree


def _normalize_script_step_result(step_data, step_name):
    """Normalize a plugin result to a DataTree-compatible script node."""
    if isinstance(step_data, DataTreeDitto):
        return step_data
    if isinstance(step_data, xr.DataTree):
        return DataTreeDitto.from_datatree(step_data)
    try:
        return DataTreeDitto(step_data)
    except TypeError as exc:
        step_data_type = type(step_data)
        raise TypeError(
            f"Cannot attach result for script step {step_name!r}: step_data "
            "must be an xarray DataTree, DataTreeDitto, xarray Dataset, "
            "xarray DataArray, or another type convertible by DataTreeDitto. "
            f"Got {step_data_type.__module__}.{step_data_type.__name__}. "
            "To attach a scalar or other simple value, wrap it in a Dataset, "
            "DataArray, or supported dict, for example {'value': 0}. "
            f"Original conversion error: {exc}"
        ) from exc


def _require_script_tree(tree):
    """Raise if *tree* is not an initialized script DataTree."""
    if not isinstance(tree, xr.DataTree):
        raise TypeError(
            "Script DataTree helpers require an xarray.DataTree created by "
            f"initialize_script_tree(). Got {type(tree).__module__}."
            f"{type(tree).__name__}."
        )
    if tree.attrs.get("execution_mode") != SCRIPT_EXECUTION_MODE:
        raise ValueError(
            "Script DataTree helpers may only operate on a DataTree created "
            "by initialize_script_tree()."
        )
    missing_attrs = [
        attr
        for attr in ("retention_policy", "start_time", "end_time")
        if attr not in tree.attrs
    ]
    if missing_attrs:
        missing_attr_names = ", ".join(missing_attrs)
        raise ValueError(
            "Script DataTree is missing required metadata. Use "
            "initialize_script_tree() to create script trees. Missing attrs: "
            f"{missing_attr_names}."
        )


def _normalize_output_products(output_products):
    """Return output products as a list of paths/products."""
    if output_products is None:
        return []
    if isinstance(output_products, str):
        return [output_products]
    return list(output_products)


def get_output_products(tree, step_id=None):
    """Return products written by scripted output formatter steps.

    Parameters
    ----------
    tree : xarray.DataTree
        Root script DataTree created by ``initialize_script_tree``.
    step_id : str, optional
        Specific output formatter step to inspect. If omitted, products from
        all steps with ``attrs["output_products"]`` are returned in tree order.

    Returns
    -------
    list
        Output products recorded by output formatter steps.

    Raises
    ------
    ValueError
        If *tree* is not an initialized script tree, *step_id* is unknown, or
        no output products are available.

    Examples
    --------
    >>> from geoips.scripting import get_output_products
    >>> output_products = get_output_products(tree)
    >>> output_products
    ["/path/to/output.png"]
    """
    _require_script_tree(tree)

    if step_id is not None:
        if step_id not in tree.children:
            raise ValueError(f"Script DataTree does not contain step {step_id!r}.")
        output_products = _normalize_output_products(
            tree[step_id].attrs.get("output_products")
        )
        if not output_products:
            raise ValueError(
                f"Script step {step_id!r} does not contain output products."
            )
        return output_products

    output_products = []
    for child in tree.children.values():
        output_products.extend(
            _normalize_output_products(child.attrs.get("output_products"))
        )

    if not output_products:
        raise ValueError(
            "No output products are available. Run an output formatter step "
            "before calling get_output_products()."
        )
    return output_products


def _attrs_only_node(node):
    """Return a DataTree node containing only attrs from *node*."""
    return xr.DataTree(dataset=xr.Dataset(attrs=dict(node.attrs)))


def _older_step_ids(tree, current_step_id):
    """Return top-level step ids older than *current_step_id*."""
    step_ids = list(tree.children)
    return step_ids[: step_ids.index(current_step_id)]


def _reduce_step_to_attrs_only(tree, step_id):
    """Reduce a top-level script step node to attrs-only metadata."""
    tree[step_id] = _attrs_only_node(tree[step_id])


def _remove_step(tree, step_id):
    """Remove a top-level script step node."""
    del tree[step_id]


_XARRAY_DATA_PLUGIN_KINDS = frozenset(
    ("algorithm", "interpolator", "manual", "reader")
)


def _is_xarray_data_step(node):
    """Return whether *node* should provide xarray input to later plugins."""
    return (
        node.attrs.get("plugin_kind") in _XARRAY_DATA_PLUGIN_KINDS
        and _has_data_vars(node)
    )


def _latest_xarray_data_step_id(tree, current_step_id):
    """Return the newest xarray-data step at or before *current_step_id*."""
    candidate_step_ids = [
        *_older_step_ids(tree, current_step_id),
        current_step_id,
    ]
    for step_id in reversed(candidate_step_ids):
        if _is_xarray_data_step(tree[step_id]):
            return step_id
    return None


def _metadata_only_preserved_step_ids(tree, current_step_id):
    """Return step ids that must remain intact for metadata_only retention."""
    preserved = {current_step_id}
    latest_data_step_id = _latest_xarray_data_step_id(tree, current_step_id)
    if latest_data_step_id is not None:
        preserved.add(latest_data_step_id)
    return preserved


def _has_data_vars(node):
    """Return whether a script step node or its children contain data vars."""
    if node.ds is not None and bool(node.ds.data_vars):
        return True
    return any(_has_data_vars(child) for child in node.children.values())


def _to_mutable_dataset(node):
    """Return a mutable Dataset containing data from *node* and children."""
    datasets = []
    if node.ds is not None and bool(node.ds.data_vars):
        datasets.append(node.to_dataset())
    for child in node.children.values():
        if _has_data_vars(child):
            datasets.append(_to_mutable_dataset(child))

    if not datasets:
        return xr.Dataset(attrs=dict(node.attrs))
    if len(datasets) == 1:
        dataset = datasets[0].copy(deep=True)
    else:
        dataset = xr.merge(datasets).copy(deep=True)
    dataset.attrs = {**dict(node.attrs), **dict(dataset.attrs)}
    return dataset


def get_current_data(tree):
    """Return the dataset from the most recent data-containing script step.

    Parameters
    ----------
    tree : xarray.DataTree
        Root script DataTree created by ``initialize_script_tree``.

    Returns
    -------
    xarray.Dataset
        Dataset from the most recent top-level reader, interpolator, algorithm,
        or manual step containing data variables, including data stored in child
        nodes such as reader outputs. The
        returned object is a mutable dataset copy intended for inspection,
        modification, and reinsertion with ``add_data_step``.

    Raises
    ------
    ValueError
        If *tree* is not an initialized script DataTree or no data-containing
        step is available.
    """
    _require_script_tree(tree)

    for step_id in reversed(list(tree.children)):
        node = tree[step_id]
        if _is_xarray_data_step(node):
            return _to_mutable_dataset(node)

    raise ValueError(
        "No data-containing script steps are available. Attach a plugin result "
        "or manual data step before calling get_current_data()."
    )


def add_data_step(tree, data, *, step_id, retention_policy=None):
    """Attach user-created or user-modified data as a manual script step.

    Parameters
    ----------
    tree : xarray.DataTree
        Root script DataTree created by ``initialize_script_tree``.
    data : xarray.DataTree, DataTreeDitto, xarray.Dataset, xarray.DataArray, or
        convertible object
        Data to attach as the new manual step.
    step_id : str
        Step id for the inserted data.
    retention_policy : RetentionPolicy or str, optional
        Retention policy override for the inserted data step.

    Returns
    -------
    xarray.DataTree
        The same root script DataTree, updated in place and returned for
        convenient chaining.
    """
    return attach_plugin_result(
        tree,
        data,
        step_id=step_id,
        plugin_kind="manual",
        retention_policy=retention_policy,
    )


def apply_script_retention(tree, current_step_id, retention_policy=None):
    """Apply a retention policy to an initialized script DataTree.

    Parameters
    ----------
    tree : xarray.DataTree
        Root script DataTree created by ``initialize_script_tree``.
    current_step_id : str
        Step id for the current result. This step remains intact for all
        retention policies.
    retention_policy : RetentionPolicy or str, optional
        Retention policy to apply. Defaults to the root script DataTree policy.

    Returns
    -------
    xarray.DataTree
        The same root script DataTree, updated in place and returned for
        convenient chaining.

    Raises
    ------
    ValueError
        If *tree* is not an initialized script DataTree, if *current_step_id*
        does not exist, or if the retention policy is invalid.
    """
    _require_script_tree(tree)

    if current_step_id not in tree.children:
        raise ValueError(
            f"Cannot apply script retention for unknown step {current_step_id!r}."
        )

    if retention_policy is None:
        retention_policy = tree.attrs.get("retention_policy")
    retention_policy = normalize_retention_policy(retention_policy)

    if retention_policy is RetentionPolicy.keep_all:
        return tree

    older_step_ids = _older_step_ids(tree, current_step_id)

    if retention_policy is RetentionPolicy.metadata_only:
        preserved_step_ids = _metadata_only_preserved_step_ids(tree, current_step_id)
        for step_id in older_step_ids:
            if step_id not in preserved_step_ids:
                _reduce_step_to_attrs_only(tree, step_id)
        return tree

    if retention_policy is RetentionPolicy.current_only:
        for step_id in older_step_ids:
            _remove_step(tree, step_id)
        return tree

    raise ValueError(f"Unhandled retention policy {retention_policy!r}.")


def attach_plugin_result(
    tree,
    step_data,
    *,
    step_id=None,
    plugin_kind,
    plugin_name=None,
    start_time=None,
    end_time=None,
    retention_policy=None,
):
    """Attach a scripted plugin result to an initialized script DataTree.

    This internal helper records one plugin result under the supplied
    ``step_id``. If ``step_id`` is omitted, the plugin name is used. Duplicate
    step names are rejected so scripts do not accidentally clobber earlier
    results.

    Parameters
    ----------
    tree : xarray.DataTree
        Root script DataTree created by ``initialize_script_tree``.
    step_data : xarray.DataTree, DataTreeDitto, xarray.Dataset, xarray.DataArray, or
        convertible object
        Result returned by a plugin call. Values must either already be
        DataTree-compatible or be convertible by ``DataTreeDitto``. Scalars and
        other simple values should be wrapped in a ``Dataset``, ``DataArray``,
        or supported container such as a ``dict`` before attaching.
    step_id : str, optional
        Name to use for the attached result node. Defaults to *plugin_name*.
    plugin_kind : str
        Registered plugin kind that produced *step_data*, or ``"manual"`` for
        user-created script data. Values are validated against the cached GeoIPS
        interface list plus ``"manual"``.
    plugin_name : str, optional
        Plugin name that produced *step_data*. Required for registered plugin
        kinds. For ``plugin_kind="manual"``, omitted plugin names are recorded
        as ``"manual"``.
    start_time : datetime.datetime, optional
        Step start datetime. Defaults to the current UTC time for
        registered plugin kinds. For ``plugin_kind="manual"``, omitted times
        are recorded as ``None``.
    end_time : datetime.datetime, optional
        Step end datetime. Defaults to the current UTC time for
        registered plugin kinds. For ``plugin_kind="manual"``, omitted times
        are recorded as ``None``.
    retention_policy : RetentionPolicy or str, optional
        Retention policy used for this step. Defaults to the policy stored on
        the root script DataTree.

    Returns
    -------
    xarray.DataTree
        The same root script DataTree, updated in place and returned for
        convenient chaining.

    Raises
    ------
    ValueError
        If *tree* is not an initialized script DataTree, if no step name can be
        determined, if the step name already exists, or if the retention policy
        is invalid.
    TypeError
        If *step_data* cannot be converted to a script DataTree node.
    """
    _require_script_tree(tree)

    step_name = step_id or plugin_name
    if plugin_kind == "manual" and plugin_name is None:
        plugin_name = "manual"
        step_name = step_name or plugin_name
    _validate_script_step_metadata(step_name, plugin_kind, plugin_name)
    if step_name in tree.children:
        raise ValueError(
            f"Script DataTree already contains step {step_name!r}. "
            "Provide a unique step_id to avoid clobbering existing results."
        )

    if retention_policy is None:
        retention_policy = tree.attrs.get("retention_policy")
    retention_policy = normalize_retention_policy(retention_policy)

    if plugin_kind == "manual":
        step_start_time = start_time
        step_end_time = end_time
    else:
        step_start_time = start_time or _utc_now()
        step_end_time = end_time or _utc_now()
    step_start_time = _format_timestamp(step_start_time, "start_time")
    step_end_time = _format_timestamp(step_end_time, "end_time")

    node = _normalize_script_step_result(step_data, step_name)
    tree[step_name] = node

    attached = tree[step_name]
    attached.attrs.update(
        {
            "step_id": step_name,
            "plugin_kind": plugin_kind,
            "plugin_name": plugin_name,
            "start_time": step_start_time,
            "end_time": step_end_time,
            "retention_policy": retention_policy.value,
        }
    )
    apply_script_retention(tree, step_name, retention_policy=retention_policy)
    return tree
