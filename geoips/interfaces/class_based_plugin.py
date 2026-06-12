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

from geoips import interfaces

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

        # Stash attrs from Dataset input for restoration in _post_call (OBP only)
        if _obp_initiated and hasattr(data, "attrs"):
            self._stashed_input_attrs = dict(data.attrs)

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

        # Step 1.5: Restore stashed metadata from input (OBP only)
        stashed = getattr(self, "_stashed_input_attrs", None)
        if _obp_initiated and stashed:
            if hasattr(data, "attrs"):
                for k, v in stashed.items():
                    if k not in getattr(data, "attrs", {}):
                        data.attrs[k] = v
                LOG.debug("Restored %d stashed attrs to output", len(stashed))
            self._stashed_input_attrs = None

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
        if isinstance(result, xr.DataTree):
            return DataTreeDitto.from_datatree(result)
        if isinstance(result, (str, int, float, bool)):
            ds = xr.Dataset(attrs={"value": result})
            return DataTreeDitto(ds, name=getattr(self, "name", "result"))
        return DataTreeDitto(result, name=getattr(self, "name", "result"))

    @staticmethod
    def _extract_child_kwargs(data, kwargs):
        from geoips.utils.types.yaml_plugin_callable import _KIND_TO_KWARG

        if not isinstance(data, xr.DataTree):
            return kwargs

        children = dict(data.children)
        if not children:
            return kwargs

        def _wrap_spec(spec):
            return {"spec": spec} if spec is not None else None

        def _unwrap_ditto(child):
            from geoips.utils.types.datatree_ditto import DataTreeDitto

            if isinstance(child, DataTreeDitto):
                return child.get_original()
            return child.ds

        def _unwrap_ds(child):
            from geoips.utils.types.datatree_ditto import DataTreeDitto

            if isinstance(child, DataTreeDitto):
                return child.ds
            if isinstance(child, xr.DataTree):
                return child.ds
            return child

        _EXTRACTORS = {
            "algorithm": _unwrap_ds,
            "colormapper": lambda c: c.ds.attrs.get("_mpl_colors_info"),
            "feature_annotator": lambda c: _wrap_spec(c.ds.attrs.get("spec")),
            "filename_formatter": lambda c: c.ds.attrs.get("output_fnames"),
            "gridline_annotator": lambda c: _wrap_spec(c.ds.attrs.get("spec")),
            "product": lambda c: str(c.name) if c.name else None,
            "sector": lambda c: c.ds.attrs.get("area_definition"),
        }

        for _child_name, child in children.items():
            pkind = (
                str(child.ds.attrs.get("plugin_kind", ""))
                if child.ds is not None
                else ""
            )
            kwarg_name = _KIND_TO_KWARG.get(pkind)
            if not kwarg_name or kwarg_name in kwargs:
                continue

            extract = _EXTRACTORS.get(pkind)
            if extract is not None:
                val = extract(child)
                if val is not None:
                    kwargs[kwarg_name] = val
            elif pkind in ("product", "product_default"):
                kwargs[kwarg_name] = dict(child.ds.attrs)

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
        if _obp_initiated:
            provided_args = set(kwargs)
            accepted_args = set(list(inspect.signature(self.call).parameters.keys()))
            unaccepted_args = provided_args - accepted_args
            for arg in unaccepted_args:
                provided_args.remove(arg)

            new_kwargs = {kwarg: kwargs[kwarg] for kwarg in provided_args}
        else:
            new_kwargs = kwargs

        if data is None:
            result = self.call(*args, **new_kwargs)
        else:
            if _obp_initiated:
                new_kwargs = self._extract_child_kwargs(data, new_kwargs)
            data = self._pre_call(
                data, *args, _obp_initiated=_obp_initiated, **new_kwargs
            )
            if (
                _obp_initiated
                and isinstance(data, xr.DataTree)
                and len(dict(data.children)) > 1
                and not data.ds.attrs.get("_ditto_original_type")
            ):
                new_args = _kwarg_to_positional(new_kwargs, self.call)
                result = self.call(*new_args, **new_kwargs)
                data = self._post_call(
                    result, *args, _obp_initiated=_obp_initiated, **new_kwargs
                )
                result = data
            else:
                data = self.call(data, *args, **new_kwargs)
                data = self._post_call(
                    data, *args, _obp_initiated=_obp_initiated, **new_kwargs
                )
                result = data

        return result

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
        elif pname == "data" and "xarray_obj" in kwargs:
            val = kwargs.pop("xarray_obj")
            positional.append(val)
            consumed.add("xarray_obj")
        else:
            raise TypeError(
                f"_kwarg_to_positional: required parameter {pname!r} "
                f"is missing from kwargs and cannot be filled automatically. "
                f"Available kwargs: {list(kwargs)}"
            )
    return tuple(positional)
