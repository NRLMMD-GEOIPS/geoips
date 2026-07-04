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
from geoips.utils.types.datatree_ditto import DataTreeDitto
from geoips.utils.types.obp_conduits import OBP_CONDUITS

LOG = logging.getLogger(__name__)

_MISSING = object()
LEGACY_DATA_ARGUMENTS = frozenset(
    {
        "arrays",
        "input_xarray",
        "xarray_dict",
        "xarray_obj",
        "xobj",
    }
)

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
        plugin_name = getattr(self, "name", "result")
        try:
            return DataTreeDitto(result, name=plugin_name)
        except TypeError as exc:
            raise TypeError(
                f"Plugin '{plugin_name}' (kind "
                f"'{getattr(self, 'interface', 'unknown')}') returned a value of "
                f"type '{type(result).__module__}.{type(result).__name__}' that "
                f"could not be wrapped in a DataTreeDitto because no converter is "
                f"registered for it. Either return a supported type (DataTree, "
                f"Dataset, DataArray, ndarray, dict, list, or a scalar) or "
                f"register a converter for this type. See "
                f"geoips.utils.types.converters for examples.\n"
                f"Original error: {exc}"
            ) from exc

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

    def _invoke(self, *args, _obp_initiated=False, **kwargs):
        """Call the plugin while adapting the canonical ``data`` keyword.

        ``data`` belongs to the ``BaseClassPlugin.__call__`` protocol. It is always
        accepted by that wrapper, even when the implementation's ``call`` method does
        not declare a data parameter (readers are the important example). Existing
        plugins may instead declare one of the legacy data argument names in
        :data:`LEGACY_DATA_ARGUMENTS`; this method binds the real ``call`` signature
        first and then places preprocessed data into the matching argument.

        All other positional and keyword arguments retain normal Python binding
        semantics. In particular, the first positional argument to a reader remains
        ``fnames`` and a second-position ``input_xarray`` or ``xarray_obj`` remains in
        its declared position.
        """
        input_data = kwargs.pop("data", _MISSING)
        signature = inspect.signature(self.call)
        data_argument = self._resolve_data_argument(signature)

        call_kwargs = dict(kwargs)
        conduit_arguments = set()
        if _obp_initiated and input_data is not _MISSING:
            original_keys = set(call_kwargs)
            call_kwargs = self._extract_child_kwargs(input_data, call_kwargs)
            conduit_arguments = set(call_kwargs) - original_keys

        if _obp_initiated:
            call_kwargs = self._obp_filter_kwargs(call_kwargs)
            conduit_arguments.intersection_update(call_kwargs)

        bound = signature.bind_partial(*args, **call_kwargs)
        data_is_bound = data_argument is not None and data_argument in bound.arguments

        if input_data is not _MISSING and data_is_bound:
            if data_argument not in conduit_arguments:
                raise TypeError(
                    f"Plugin '{self.name}' received input through both the canonical "
                    f"'data' keyword and its call argument {data_argument!r}"
                )
            # A conduit extracted the implementation-specific value from the
            # aggregate input tree. Prefer that value over the aggregate tree itself.
            data_to_prepare = bound.arguments[data_argument]
        elif input_data is not _MISSING:
            data_to_prepare = input_data
        elif data_is_bound:
            # Preserve direct legacy calls such as plugin(xarray_obj=dataset).
            data_to_prepare = bound.arguments[data_argument]
        else:
            data_to_prepare = _MISSING

        hook_kwargs = self._hook_kwargs(bound, exclude={data_argument, "data"})
        if data_to_prepare is not _MISSING:
            prepared_data = self._pre_call(
                data_to_prepare,
                _obp_initiated=_obp_initiated,
                **hook_kwargs,
            )
            if data_argument is not None:
                bound.arguments[data_argument] = prepared_data

        result = self.call(*bound.args, **bound.kwargs)
        post_call_kwargs = self._hook_kwargs(bound, exclude={data_argument, "data"})
        return self._post_call(
            result,
            _obp_initiated=_obp_initiated,
            **post_call_kwargs,
        )

    def _resolve_data_argument(self, signature):
        """Return the implementation argument that receives canonical input data.

        New plugins use ``data``. During the transition, known legacy argument names
        are detected from the actual ``call`` signature. A plugin with an unusual
        legacy name may declare ``data_argument`` on its class. Plugins such as legacy
        readers, whose ``call`` method consumes no upstream data, resolve to ``None``;
        their wrapper still accepts ``data`` for hooks and dependency extraction.
        """
        if "data" in signature.parameters:
            return "data"

        override = getattr(self, "data_argument", None)
        if override is not None:
            if override not in signature.parameters:
                raise TypeError(
                    f"Plugin '{self.name}' declares data_argument={override!r}, but "
                    "that name is not present in its call signature"
                )
            return override

        matches = LEGACY_DATA_ARGUMENTS.intersection(signature.parameters)
        if len(matches) == 1:
            return next(iter(matches))
        if len(matches) > 1:
            raise TypeError(
                f"Plugin '{self.name}' has multiple possible data arguments "
                f"{sorted(matches)}; set its data_argument attribute explicitly"
            )
        return None

    @staticmethod
    def _hook_kwargs(bound, exclude=frozenset()):
        """Return bound call arguments as keyword context for invocation hooks."""
        hook_kwargs = {}
        for name, value in bound.arguments.items():
            if name in exclude:
                continue
            parameter = bound.signature.parameters[name]
            if parameter.kind is inspect.Parameter.VAR_KEYWORD:
                hook_kwargs.update(
                    {key: item for key, item in value.items() if key not in exclude}
                )
            else:
                hook_kwargs[name] = value
        return hook_kwargs

    def _obp_filter_kwargs(self, kwargs):
        """Return a dict of only the kwargs accepted by ``self.call``.

        If ``call`` accepts ``**kwargs`` (a ``VAR_KEYWORD`` parameter) every key
        is retained, since such a signature accepts arbitrary keywords.
        """
        params = inspect.signature(self.call).parameters.values()
        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params):
            return dict(kwargs)
        accepted = {p.name for p in params}
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
        def _call(self, *args, **kwargs):
            return cls._invoke(self, *args, **kwargs)

        _call.__signature__ = inspect.signature(call_method)  # mirror only call()
        _call.__annotations__ = getattr(call_method, "__annotations__", {})
        cls.__call__ = _call
