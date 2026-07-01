# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Implements a base class for class-based plugins.

The base class implemented here would expose the call signature of the child plugin
class as `__call__()` while also providing hooks for pre- and post-processing.

The hooks are available as `_pre_call()` and `_post_call()`. They should be used to
implement common functionality that all plugins of this type should posess but which we
don't want developers to need to implement. They are intended to be overridden by the
child plugin-type class (e.g. BaseReaderPlugin). They should define what kwargs they
accept when defined on the plugin-type class but should accept their arguments from
`**kwargs` from `__call__()`.

The `call()` method should be overridden on the actual plugin class. It should provide
the data processing for the plugin. `__call__()`'s signature will be identical to that
of `call()` except that `call()` should not accept `**kwargs`. That should be consumed
by the hooks.

`__call__()` should not be overridden anywhere.

I removed this for now, but maybe consider again later:
I still need to do more research to understand the effects of ParamSpec, TypeVar, and
Generic, but they are supposed to help make this class and its children interact with
IDE, static analysis tools, and other type checkers correctly.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import functools
import inspect
import logging

import xarray as xr

from geoips.errors import PluginError
from geoips import interfaces
from geoips.utils.types.obp_conduits import OBP_CONDUITS

LOG = logging.getLogger(__name__)

# P = ParamSpec("P")
# R = TypeVar("R")


# To do:
# - __repr__()
# - __str__()
# - tokenize() - Call from _post_call if tokenize=True
# - Converter to/from dict of xarray - Probably pure, accept data and family name
# - Converter to/from data_tree


def valid_str_attr(cls, attr_name: str):
    """Check that the given attribute is a non-empty string."""
    attr_value = getattr(cls, attr_name, None)
    if not isinstance(attr_value, str):
        raise TypeError(f"{cls.__name__}.{attr_name} must be a string")
    if not attr_value:
        raise ValueError(f"{cls.__name__}.{attr_name} cannot be empty")


# The OBP conduit binding registry and its extractor helpers now live in
# ``geoips.utils.types.obp_conduits`` (imported above as ``OBP_CONDUITS``) so
# that there is a single home for per-kind input wiring.


# class BaseClassPlugin(Generic[P, R], ABC):
class BaseClassPlugin(ABC):
    """The base class for GeoIPS class-based plugins.

    All plugins are required to carry the following class attributes:

    - interface: The interface type the plugin belongs to (e.g. 'readers', 'products').
      This is typically provided by the interface-level plugin class and not the
      individual plugin class.
    - family: The family name of the plugin. This should be defined by the plugin class.
    - name: The specific name of the plugin. This should be defined by the plugin class.

    Subclasses of this base class must also implement the following methods:

    - call(): The main method that performs the plugin's functionality. This method
      should be implemented by the plugin class.
    - _pre_call(): A hook method that can be overridden to preprocess data before
      calling the main call() method. This method should accept the same arguments as
      call() via `*args` and `**kwargs` and should, typically, be implemented by the
      interface-level plugin class.
    - _post_call(): A hook method that can be overridden to post-process data after
      calling the main call() method. This method should accept the same arguments as
      call() via `*args` and `**kwargs` and should, typically, be implemented by the
      interface-level plugin class.

    The purpose of `_pre_call()` and `_post_call()` is to allow for common
    functionality that all plugins of a certain type should possess, without requiring
    developers to implement this functionality in every plugin class. Initially, this
    will be used to convert inputs from DataTree to other formats and back to DataTree
    after processing, but it could be used for other common tasks as well.
    """

    # If set to True, we are in OBP. False means we are in a legacy procflow.
    # Set up logic in this or interface classes to convert from DT to data type
    # referenced in family

    # If no family is provided, just assume it works with DT
    data_tree = False
    required_attributes = ["interface", "family", "name"]

    def _check_interface_attribute(cls):
        """Check the validity of the 'interface' attribute.

        Checks to be sure that the interface attribute is a non-empty string and that it
        is a known plugin interface.
        """
        valid_str_attr(cls, "interface")
        if cls.interface not in interfaces.list_available_interfaces()["class_based"]:
            raise ValueError(
                f"{cls.__name__}.interface '{cls.interface}' is not a known plugin "
                "interface"
            )

    def _check_family_attribute(cls):
        """Check the validity of the 'family' attribute."""
        valid_str_attr(cls, "family")

    def _check_name_attribute(cls):
        """Check the validity of the 'name' attribute."""
        valid_str_attr(cls, "name")

    @abstractmethod
    # def call(self, *args: P.args, **kwargs: P.kwargs) -> R:
    def call(self, *args, **kwargs):
        """Callable method to be implemented by the plugin class."""
        pass

    # hooks are intentionally loose; document their accepted kwargs
    # def _pre_call(self, data: R, *args, **kwargs) -> R:
    def _pre_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Preprocess the data before calling the main plugin method.

        For ``data_tree=False`` plugins this hook:

        1. Unwraps a ``DataTreeDitto`` (or plain ``DataTree``) input
           to recover the native object via ``_unwrap()``.
        2. Applies a family-specific input conversion if the plugin's
           class defines a ``_family_conversion_map``.

        For ``data_tree=True`` plugins the data passes through unchanged.

        Parameters
        ----------
        data : R, optional
            The input data for the plugin.
        _obp_initiated : bool, optional
            Whether or not this plugin is being called via the order
            based procflow.  Defaults to False.

        Returns
        -------
        The processed data.
        """
        if data is None or self.data_tree:
            return data

        # Step 1: Unwrap DataTree → native type
        data = self._unwrap(data)

        # Step 2: Apply family-specific input conversion (OBP only)
        if _obp_initiated:
            conversion_map = getattr(self, "_family_conversion_map", None)
            if conversion_map is not None:
                spec = conversion_map.get(self.family)
                if spec is not None and spec.input_converter is not None:
                    if spec.input_type is not None and not isinstance(
                        data, spec.input_type
                    ):
                        data = spec.input_converter(data)
                    elif spec.input_type is None:
                        data = spec.input_converter(data)

        return data

    # def _post_call(self, data: R, *args, **kwargs) -> R:
    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Post-process the data after calling the main plugin method.

        For ``data_tree=False`` plugins this hook:

        1. Applies a family-specific output (reverse) conversion if the
           plugin's class defines a ``_family_conversion_map``.
        2. Wraps a non-DataTree result back into a ``DataTreeDitto``
           via ``_wrap()``.

        For ``data_tree=True`` plugins the data passes through unchanged.

        Parameters
        ----------
        data : R, optional
            The output data from the plugin.
        _obp_initiated : bool, optional
            Whether or not this plugin is being called via the order
            based procflow.  Defaults to False.

        Returns
        -------
            The processed data.
        """
        if data is None or self.data_tree:
            return data

        # Step 1: Apply family-specific reverse conversion (OBP only)
        if _obp_initiated:
            conversion_map = getattr(self, "_family_conversion_map", None)
            if conversion_map is not None:
                spec = conversion_map.get(self.family)
                if spec is not None and spec.output_converter is not None:
                    data = spec.output_converter(data)

        # Step 2: Wrap into DataTreeDitto if not already (OBP only)
        if _obp_initiated and not isinstance(data, xr.DataTree):
            data = self._wrap(data)

        return data

    def _unwrap(self, data):
        """Unwrap a DataTree-like container to the original type.

        If the input is a ``DataTreeDitto``, call ``get_original()``
        to recover the native object (numpy array, Dataset, dict, …)
        that was originally passed to the constructor.  If the input
        is a plain ``xr.DataTree`` that contains a ``DataTreeDitto``
        dataset, extract and unwrap it.

        For multi-input DataTrees (collected by
        ``Workflow._collect_upstream_data``) the root dataset carries
        no ``_ditto_original_type``.  In that case:

        * A single child is unwrapped directly.
        * Multiple children pass through unchanged (the caller's
          ``_extract_child_kwargs`` handles extraction).

        Parameters
        ----------
        data : Any
            The container passed to the plugin callable.

        Returns
        -------
        Any
            The unwrapped native object.
        """
        from geoips.utils.types.datatree_ditto import DataTreeDitto

        if isinstance(data, DataTreeDitto):
            return data.get_original()

        if isinstance(data, xr.DataTree):
            children = dict(data.children)
            if children and not data.ds.attrs.get("_ditto_original_type"):
                if len(children) == 1:
                    child = next(iter(children.values()))
                    if isinstance(child, DataTreeDitto):
                        return child.get_original()
                    return child
                return data
            try:
                return DataTreeDitto(data.ds).get_original()
            except (TypeError, ValueError, RuntimeError) as exc:
                LOG.debug("Could not unwrap DataTree to original: %s", exc)
        return data

    def _wrap(self, result):
        """Wrap a non-DataTree result back into a DataTreeDitto.

        If *result* is already a ``DataTreeDitto`` it is returned as-is.
        Any other non-None value is wrapped into a ``DataTreeDitto``
        (with an automatic name derived from the plugin).

        Parameters
        ----------
        result : Any
            The return value of ``_post_call``.

        Returns
        -------
        DataTreeDitto or the original result.
        """
        from geoips.utils.types.datatree_ditto import DataTreeDitto

        if result is None:
            return result
        if isinstance(result, DataTreeDitto):
            return result
        # If we already have a DataTree, convert to DTD and return
        if isinstance(result, xr.DataTree):
            return DataTreeDitto.from_datatree(result)
        # In the case of a scalar, create a DataSet, then convert to DataTreeDitto.
        # The resulting DTD instance will have a single attribute, "value", containing
        # the scalar value. This must be handled by the calling plugin's `_post_call()`
        # to give the attribute an appropriate name. For example, CoverageCheckers
        # rename "value" to "coverage"
        if isinstance(result, (str, int, float, bool)):
            ds = xr.Dataset(attrs={"value": result})
            return DataTreeDitto(ds, name=getattr(self, "name", "result"))
        # For all types not previously handled, convert whatever we got to a DTD whose
        # name is the same as the calling plugin and return
        return DataTreeDitto(result, name=getattr(self, "name", "result"))

    @staticmethod
    def _to_mutable_dataset(data):
        """Convert a DataTree with children into a mutable ``xr.Dataset``.

        ``DataTree.ds`` returns an immutable ``DatasetView``.  Plugins
        that need to write into the dataset must call this helper first.

        * Single child → ``children[0].to_dataset()``
        * Multiple children → ``xr.merge(...)``
        * Not a DataTree → returned unchanged.
        """
        if not isinstance(data, xr.DataTree):
            return data
        children = list(data.children.values())
        if len(children) == 1:
            return children[0].to_dataset()
        if len(children) > 1:
            return xr.merge([c.to_dataset() for c in children])
        return data

    @staticmethod
    def _extract_child_kwargs(data, kwargs):
        if not isinstance(data, xr.DataTree):
            return kwargs

        children = dict(data.children)
        if not children:
            return kwargs

        for _child_name, child in children.items():
            pkind = (
                str(child.ds.attrs.get("plugin_kind", ""))
                if child.ds is not None
                else ""
            )
            conduit = OBP_CONDUITS.get(pkind)
            if conduit is None:
                continue
            kwarg_name = conduit["kwarg"]
            if kwarg_name in kwargs:
                continue

            val = conduit["extract"](child)
            if val is not None:
                kwargs[kwarg_name] = val

        if "xarray_obj" in kwargs and "product_name" in kwargs:
            xo = kwargs["xarray_obj"]
            if (
                hasattr(xo, "data_vars")
                and xo.data_vars
                and "product_name" not in xo.data_vars
            ):
                pn = kwargs["product_name"]
                if isinstance(pn, str) and pn not in xo.data_vars:
                    xo = xo.rename({list(xo.data_vars)[0]: pn})
                    kwargs["xarray_obj"] = xo

        return kwargs

    def _call_interpolator(self, data, kwargs):
        """Call the main interpolator plugin method.

        Parameters
        ----------
        data : R, optional
            The output data from the plugin.

        Returns
        -------
            The processed data.
        """
        input_xarray = None
        sector_found = False
        for group in data.groups:
            ds = data[group]
            # This is the data dependency
            if hasattr(ds, "attrs") and ds.attrs.get("plugin_kind"):
                if ds.attrs["plugin_kind"] != "sector":
                    input_xarray = ds.to_dataset()
                else:
                    sector_found = True

        if input_xarray is None:
            raise RuntimeError(
                "Error: Could not find an input dataset to interpolate for "
                f"interpolator plugin '{self.name}'."
            )

        if not sector_found:
            raise RuntimeError(
                "Error: Could not find an appropriate sector step to interpolate to for"
                f" interpolator plugin '{self.name}'."
            )

        interp_kwargs = _collect_interp_kwargs(input_xarray)
        if kwargs.get("area_def"):
            interp_kwargs["area_def"] = kwargs["area_def"]
        if kwargs.get("varlist"):
            interp_kwargs["varlist"] = kwargs["varlist"]
        result = self.call(**interp_kwargs)

        return result

    def _invoke(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Call the main plugin method.

        Additionally, filter out unaccepted arguments if initiated via the OBP.
        Unwrap / wrap and family-specific type conversions are handled by
        ``_pre_call()`` and ``_post_call()``.

        Parameters
        ----------
        data : R, optional
            The output data from the plugin.
        _obp_initiated : bool, optional
            Whether or not this plugin is being called via the order based procflow.
            Defaults to False.

        Returns
        -------
            The processed data.
        """
        new_kwargs = self._obp_filter_kwargs(kwargs) if _obp_initiated else kwargs

        if data is None:
            # No upstream data (e.g. reader steps, or any first step). We still
            # run ``_post_call`` so interface-level normalization happens — most
            # importantly the reader ``dict -> DataTree`` merge in
            # ``BaseReaderPlugin._post_call`` and the ``_wrap`` into a
            # ``DataTreeDitto``.  ``_pre_call`` is a no-op for ``data is None``.
            result = self.call(*args, **new_kwargs)
            return self._post_call(
                result, *args, _obp_initiated=_obp_initiated, **new_kwargs
            )

        if _obp_initiated:
            new_kwargs = self._extract_child_kwargs(data, new_kwargs)

        data = self._pre_call(data, *args, _obp_initiated=_obp_initiated, **new_kwargs)

        if self._use_positional_unpacking(data, _obp_initiated):
            if self.interface == "interpolators":
                result = self._call_interpolator(data, new_kwargs)
            else:
                new_args = _kwarg_to_positional(new_kwargs, self.call)
                result = self.call(*new_args, **new_kwargs)
        else:
            result = self.call(data, *args, **new_kwargs)

        data = self._post_call(
            result, *args, _obp_initiated=_obp_initiated, **new_kwargs
        )
        return data

    @staticmethod
    def _use_positional_unpacking(data, _obp_initiated):
        """Return True when ``call()`` should receive unpacked positional args.

        Multi-child multi_input DataTrees cannot be passed as the first
        positional ``data`` arg (signature mismatch).  This helper detects
        that case so ``_invoke`` can switch to positional unpacking.
        """
        return (
            _obp_initiated
            and isinstance(data, xr.DataTree)
            and len(dict(data.children)) > 1
            and not data.ds.attrs.get("_ditto_original_type")
        )

    def _obp_filter_kwargs(self, kwargs):
        """Return a dict of only the kwargs accepted by ``self.call``."""
        accepted = set(inspect.signature(self.call).parameters.keys())
        return {k: v for k, v in kwargs.items() if k in accepted}

    def __init__(self, module=None):
        """
        Initialize the plugin object inheriting from BaseClasePlugin.

        Parameters
        ----------
        module: ModuleType, default=None
            The module from which the class-based plugin originated. This is used to
            collect metadata from the module and attach it to the plugin object. The
            metadata can then be used during validation to indicate where failing
            plugins originated. If None, the 'testing' attributes will be set to a
            string value that can also be used in tests.
        """
        if module:
            self.module_name = module.__name__
            self.module_path = module.__file__
        else:
            self.module_name = "Unknown."
            self.module_path = "Unknown."

    def __init_subclass__(cls, *, abstract=False, **kwargs) -> None:
        """
        Initialize a subclass of the plugin.

        Parameters
        ----------
        abstract : bool, optional
            If True, the subclass is treated as abstract. When treated as abstract,
            validation is disabled in __init_subclass__. Defaults to False.

        Raises
        ------
        TypeError
            If the subclass does not define the required attributes.
        TypeError
            If the subclass does not implement the call() method.
        TypeError
            If the subclass overrides the __call__() method.

        Returns
        -------
        None
        """
        super().__init_subclass__(**kwargs)

        # Treat the root as abstract and honor explicit marker
        if cls is BaseClassPlugin or abstract:
            cls.__plugin_abstract__ = True
            return

        # Enforce required attributes and run attribute checkers if they exist
        for attr in cls.required_attributes:
            # Ensure required attributes are defined
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define '{attr}' attribute")

            # Run attribute checker for the current attribute if it exists
            attribute_checker = getattr(cls, f"_check_{attr}_attribute", None)
            if attribute_checker is not None:
                attribute_checker(cls)

        # Prevent overriding __call__ in a True class-based plugin
        if "__call__" in cls.__dict__:
            raise TypeError(f"{cls.__name__} cannot override __call__")

        try:
            call_method = cls.__dict__.get("call")
        except AttributeError:
            raise TypeError(f"{cls.__name__} must implement call()")

        @functools.wraps(call_method)
        def _call(self, data=None, *args, **kwargs):
            return cls._invoke(self, data, *args, **kwargs)

        _call.__signature__ = inspect.signature(call_method)  # mirror only call()
        _call.__annotations__ = getattr(call_method, "__annotations__", {})
        cls.__call__ = _call


def _kwarg_to_positional(kwargs, call_func):
    """Convert kwargs to positional args matching ``call_func`` signature.

    For multi-child multi_input DataTrees, ``_invoke`` cannot pass the
    DataTree as the first positional arg (signature mismatch).  This
    helper inspects ``call_func``'s parameter names and promotes
    matching kwargs to positional arguments.

    Parameters
    ----------
    kwargs : dict
        Keyword arguments (mutated in-place — matching keys are popped).
    call_func : callable
        The plugin's ``call`` method (used for signature inspection).

    Returns
    -------
    tuple
        Positional arguments for ``call_func``.
    """
    import inspect as _inspect_mod

    sig = _inspect_mod.signature(call_func)
    positional = []
    consumed = set()
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        if param.kind not in (
            _inspect_mod.Parameter.POSITIONAL_ONLY,
            _inspect_mod.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            break
        if pname in kwargs:
            val = kwargs.pop(pname)
            positional.append(val)
            consumed.add(pname)
        elif param.default is not _inspect_mod.Parameter.empty:
            positional.append(param.default)
        elif pname == "data":
            for alias in ("xarray_obj",):
                if alias in kwargs:
                    val = kwargs.pop(alias)
                    positional.append(val)
                    consumed.add(alias)
                    break
            else:
                raise TypeError(
                    f"_kwarg_to_positional: required parameter {pname!r} "
                    f"is missing from kwargs and cannot be filled automatically. "
                    f"Available kwargs: {list(kwargs)}"
                )
        else:
            raise TypeError(
                f"_kwarg_to_positional: required parameter {pname!r} "
                f"is missing from kwargs and cannot be filled automatically. "
                f"Available kwargs: {list(kwargs)}"
            )
    return tuple(positional)


def _collect_interp_kwargs(data, collect_varlist=True):
    """Collect a set of keyword arguments for an interpolator plugin call.

    Parameters
    ----------
    data : xarray.core.datatree.DatasetView (essentially an xarray.Dataset)
        The input dataset to interpolate.
    collect_varlist : bool, optional
        Whether or not to collect the variable list to interpolate automatically.
        Defaults to True, but can be overridden if a user specifies a 'varlist'
        argument in their workflow under the interpolator step.

    Returns
    -------
    kwargs : dict
        A dictionary of keyword arguments generated from data required to run an
        interpolator plugin.
    """
    interp_kwargs = {
        "area_def": interfaces.sectors.get_plugin("goes_east").area_definition,
        "input_xarray": data,
        "output_xarray": xr.Dataset(),
        "varlist": list(data.variables.keys()),
    }

    if not collect_varlist:
        # if the user defined this in the interpolator step arguments, then remove this
        # key, value pair
        interp_kwargs.pop("varlist")

    return interp_kwargs
